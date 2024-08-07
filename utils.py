import discord
import loguru

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'


async def solve_captcha(logger: 'loguru.Logger', data, **kwargs):
    logger.info(f'captcha data: {data}')
    custom_id = data['d']['custom_id'].lstrip('MJ::iframe::')

    async def ack_captcha_url():
        from aiohttp import ClientSession, TCPConnector
        connector = TCPConnector(ssl=False)
        proxy = kwargs.get('proxy')
        async with ClientSession(connector=connector) as session:
            url = f'https://936929561302675456.discordsays.com/captcha/api/c/{custom_id}/ack?hash=1'
            session.headers.update({
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=1, i',
                'referer': 'https://936929561302675456.discordsays.com/captcha/index.html',
                'user-agent': user_agent
            })
            logger.debug(f'ack captcha: {url}')
            async with session.get(url, proxy=proxy) as response:
                result = await response.json()
                if 'detail' in result:
                    logger.error(f'ack captcha error: {result["detail"]}')
                    return None

                logger.debug(f'ack captcha result: {result}')
                return f'https://editor.midjourney.com/captcha/challenge/index.html?hash={result["hash"]}&token={result["token"]}'

    import asyncio
    await asyncio.sleep(1)
    captcha_url = await ack_captcha_url()
    if captcha_url is None:
        return False
    logger.debug(f'solve captcha: {captcha_url}')
    return await solve_turnstile(logger, captcha_url, **kwargs)


async def solve_turnstile(logger: 'loguru.Logger', url: str, **kwargs):
    browser_proxy = kwargs.get('proxy')
    browser_path = kwargs.get('browser_path')
    headless = kwargs.get('browser_headless')
    headless = headless.lower() == 'true' if headless else True
    timeout = kwargs.get('browser_timeout')
    timeout = int(timeout) if timeout else 10
    user_data_path = kwargs.get('browser_user_data_path')
    screencast_save_path = kwargs.get('browser_screencast_save_path')

    import asyncio
    from DrissionPage import ChromiumPage, ChromiumOptions
    options = (
        ChromiumOptions()
        .auto_port()
        .headless(headless)
        .incognito()
        .set_user_agent(user_agent)
        .set_argument('--guest')
        .set_argument('--no-sandbox')
        .set_argument('--disable-gpu')
    )
    if browser_path:
        options.set_browser_path(browser_path)
    if browser_proxy:
        options.set_proxy(browser_proxy)
    if user_data_path:
        options.set_user_data_path(user_data_path)
    logger.info(f'browser options: {options.__dict__}')
    page = ChromiumPage(options)
    if screencast_save_path:
        page.screencast.set_save_path(screencast_save_path)
        page.screencast.set_mode.frugal_imgs_mode()
        page.screencast.start()
    solved = False
    try:
        page.get(url)
        logger.debug('waiting for cloudflare turnstile')
        await asyncio.sleep(1)
        divs = page.eles('tag:div')
        iframe = None
        for div in divs:
            if div.shadow_root:
                iframe = div.shadow_root.ele(
                    "xpath://iframe[starts-with(@src, 'https://challenges.cloudflare.com/')]",
                    timeout=0
                )
                if iframe:
                    break
                break
        body_element = iframe.ele('tag:body', timeout=timeout).shadow_root
        await asyncio.sleep(1)
        logger.debug('waiting for checkbox')
        checkbox_element = body_element.ele("xpath://input[@type='checkbox']", timeout=timeout)
        logger.debug(f'click at offset position of checkbox')
        checkbox_element.click.at(10, 10)
        logger.debug('waiting for success')
        body_element.ele('xpath://div[@id="success"]', timeout=timeout).wait.displayed(timeout=timeout, raise_err=True)
        await asyncio.sleep(1)
        solved = True
    except Exception as e:
        logger.error(f'error: {e}')
    if screencast_save_path:
        page.screencast.stop()
    page.quit()
    return solved


class MidjourneyCaptchaBot(discord.Client):
    MIDJOURNEY_BOT_ID = 936929561302675456

    def __init__(self, logger: 'loguru.Logger', token: str, guild_id: int, channel_id: int, **kwargs):
        super().__init__(enable_debug_events=True, **kwargs)
        self.__logger = logger
        self.__token = token
        self.__guild_id = guild_id
        self.__channel_id = channel_id
        self.__kwargs = kwargs

        import asyncio
        self.__command_name = None
        self.__command_args = {}
        self.__command_event = asyncio.Event()
        self.__command_data = None

    async def imagine(self, prompt):
        self.__logger.info('imagine prompt...')
        self.__command_name = 'imagine'
        self.__command_args = {'prompt': prompt}
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
        self.__logger.info(f'socket received: {msg}')
        import json
        data = json.loads(msg)
        if (data['t'] == 'INTERACTION_IFRAME_MODAL_CREATE' and '/captcha/' in data['d']['iframe_path']):
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
            await asyncio.wait_for(self.__command_event.wait(), timeout=120)
        except asyncio.TimeoutError:
            self.__logger.error('command timeout')
            self.__command_data = False
        self.__logger.info('close bot...')
        await self.close()

    async def __solve_captcha(self, data):
        self.__command_data = await solve_captcha(self.__logger, data, **self.__kwargs)
        self.__command_event.set()
