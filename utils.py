import discord
import loguru


class BaseCaptchaSolver:
    _user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'

    def __init__(self, logger: 'loguru.Logger', **kwargs):
        self._logger = logger
        self._kwargs = kwargs

    async def solve_captcha(self, data):
        self._logger.info(f'captcha data: {data}')
        custom_id = data['d']['custom_id'].lstrip('MJ::iframe::')

        async def ack_captcha_url():
            from aiohttp import ClientSession, TCPConnector
            connector = TCPConnector(ssl=False)
            proxy = self._kwargs.get('proxy')
            async with ClientSession(connector=connector) as session:
                url = f'https://936929561302675456.discordsays.com/captcha/api/c/{custom_id}/ack?hash=1'
                session.headers.update({
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'priority': 'u=1, i',
                    'referer': 'https://936929561302675456.discordsays.com/captcha/index.html',
                    'user-agent': self._user_agent
                })
                self._logger.debug(f'ack captcha: {url}')
                async with session.get(url, proxy=proxy) as response:
                    result = await response.json()
                    if 'detail' in result:
                        self._logger.error(f'ack captcha error: {result["detail"]}')
                        return None

                    self._logger.debug(f'ack captcha result: {result}')
                    return f'https://editor.midjourney.com/captcha/challenge/index.html?hash={result["hash"]}&token={result["token"]}'

        import asyncio
        await asyncio.sleep(1)
        captcha_url = await ack_captcha_url()
        if captcha_url is None:
            return False
        self._logger.debug(f'solve captcha: {captcha_url}')
        return await self.solve_turnstile(captcha_url)

    async def solve_turnstile(self, url) -> bool:
        pass


class BrowserCaptchaSolver(BaseCaptchaSolver):
    def __init__(self, logger: 'loguru.Logger', **kwargs):
        super().__init__(logger, **kwargs)
        self.__browser_proxy = self._kwargs.get('proxy')
        self.__browser_path = self._kwargs.get('browser_path')
        self.__headless = self._kwargs.get('browser_headless', True)
        self.__incognito = self._kwargs.get('browser_incognito', True)
        self.__timeout = self._kwargs.get('browser_timeout', 10)
        self.__user_data_path = self._kwargs.get('browser_user_data_path')
        self.__screencast_save_path = self._kwargs.get('browser_screencast_save_path')
        self.__yescaptcha_path = self._kwargs.get('browser_yescaptcha_path', 'yescaptcha-assistant')

    async def solve_turnstile(self, url: str) -> bool:
        import asyncio
        import os

        from DrissionPage import ChromiumPage, ChromiumOptions
        options = (
            ChromiumOptions()
            .auto_port()
            .incognito(self.__incognito)
            .headless(self.__headless)
            .set_user_agent(self._user_agent)
            .set_argument('--no-sandbox')
            .set_argument('--disable-gpu')
        )
        if self.__browser_path:
            options.set_browser_path(self.__browser_path)
        if self.__browser_proxy:
            options.set_proxy(self.__browser_proxy)
        if self.__user_data_path:
            options.set_user_data_path(self.__user_data_path)
        use_yescaptcha_assistant = self.__yescaptcha_path and os.path.exists(self.__yescaptcha_path)
        if use_yescaptcha_assistant:
            self._logger.warning('using yescaptcha, please make sure api key is set')
            options.add_extension(self.__yescaptcha_path)
        self._logger.debug(f'browser options: {options.__dict__}')
        page = ChromiumPage(options)
        if use_yescaptcha_assistant and self.__incognito:
            self._logger.debug('enable yescaptcha in incognito mode')
            page.get('chrome://extensions/?id=gacfihmgcfkkcnkfoomcplhpekkcjlib')
            (page.ele('tag:extensions-manager').shadow_root
             .ele('tag:extensions-detail-view').shadow_root
             .ele('xpath://extensions-toggle-row[@id="allow-incognito"]').shadow_root
             .ele('tag:cr-toggle')
             .click())
        if self.__screencast_save_path:
            page.screencast.set_save_path(self.__screencast_save_path)
            page.screencast.set_mode.frugal_imgs_mode()
            page.screencast.start()
        solved = False
        try:
            page.get(url)
            self._logger.debug('waiting for cloudflare turnstile')
            await asyncio.sleep(2)
            divs = page.eles('tag:div')
            iframe = None
            for div in divs:
                if div.shadow_root:
                    iframe = div.shadow_root.ele(
                        'xpath://iframe[starts-with(@src, "https://challenges.cloudflare.com/")]',
                        timeout=0
                    )
                    if iframe:
                        break
                    break
            body_element = iframe.ele('tag:body', timeout=self.__timeout).shadow_root
            await asyncio.sleep(1)
            if use_yescaptcha_assistant:
                self._logger.debug('waiting for yescaptcha to solve')
            checkbox_element = body_element.ele(
                'xpath://input[@type="checkbox"]',
                timeout=3 if use_yescaptcha_assistant else self.__timeout
            )
            if checkbox_element:
                import random
                self._logger.debug(f'click at offset position of checkbox')
                width, height = checkbox_element.rect.size
                border = 2
                offset_x, offset_y = random.randint(border, int(width - border)), random.randint(border,
                                                                                                 int(height - border))
                page.actions.move_to(checkbox_element, offset_x, offset_y)
                checkbox_element.click.at(offset_x, offset_y)
            else:
                self._logger.warning('checkbox not found')
            self._logger.info('waiting for success')
            solved = body_element.ele(
                'xpath://div[@id="success"]',
                timeout=self.__timeout
            ).wait.displayed(timeout=self.__timeout)
            if not solved:
                self._logger.error('success not found')
            else:
                self._logger.info('success')
            await asyncio.sleep(1)
        except Exception as e:
            self._logger.error(f'error: {e}')
        if self.__screencast_save_path:
            page.screencast.stop()
        page.quit()
        return solved


class MidjourneyBot(discord.Client):
    MIDJOURNEY_BOT_ID = 936929561302675456

    def __init__(self,
                 logger: 'loguru.Logger',
                 token: str,
                 guild_id: int,
                 channel_id: int,
                 solver: BaseCaptchaSolver,
                 **kwargs):
        super().__init__(enable_debug_events=True, **kwargs)
        self.__logger = logger
        self.__token = token
        self.__guild_id = guild_id
        self.__channel_id = channel_id
        self.__solver = solver

        import asyncio
        self.__command_name = None
        self.__command_args = {}
        self.__command_event = asyncio.Event()
        self.__command_data = None
        self.__command_timeout = None

    async def imagine(self, prompt, timeout=120):
        self.__logger.info('imagine prompt...')
        self.__command_name = 'imagine'
        self.__command_args = {'prompt': prompt}
        self.__command_timeout = timeout
        await self.login(self.__token)
        await self.connect()
        return self.__command_data

    async def on_ready(self):
        self.__logger.info(f'logged: {self.user.name}')
        import asyncio
        _ = asyncio.create_task(await self.__send_commands(self.__command_name, **self.__command_args))

    async def on_message(self, message: discord.Message):
        if message.author is None or message.author.id != self.MIDJOURNEY_BOT_ID:
            return
        if message.channel is None or message.channel.id != self.__channel_id:
            return
        if message.guild is None or message.guild.id != self.__guild_id:
            return
        if message.embeds is not None and len(message.embeds) > 0:
            embed = message.embeds[0]
            if embed.title is None or embed.description is None:
                return
            embed_title = embed.title
            embed_description = embed.description
            self.__logger.info(f'embed: {embed_title}, {embed_description}')
            if 'Blocked' in embed_title:
                self.__command_data = False
                self.__command_event.set()

    async def on_socket_raw_receive(self, msg):
        import json
        data = json.loads(msg)
        if data['t'] == 'INTERACTION_IFRAME_MODAL_CREATE':
            self.__logger.info(f'interaction iframe modal create: {data}')
            if '/captcha/' in data['d']['iframe_path']:
                import asyncio
                _ = asyncio.create_task(self.__solve_captcha(data))

    async def __send_commands(self, command_name, **kwargs):
        self.__logger.info(f'send {command_name} commands, {kwargs}')
        channel = self.get_channel(self.__channel_id)
        commands = await channel.application_commands()
        command = next(command for command in commands if command.name == command_name)
        await command(**kwargs)
        import asyncio
        try:
            await asyncio.wait_for(self.__command_event.wait(), timeout=self.__command_timeout)
        except asyncio.TimeoutError:
            self.__logger.error('command timeout')
            self.__command_data = False
        self.__logger.info('close bot...')
        await self.close()

    async def __solve_captcha(self, data):
        self.__command_data = await self.__solver.solve_captcha(data)
        self.__command_event.set()
