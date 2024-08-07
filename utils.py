import discord
import loguru

default_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'


async def solve_captcha(logger: 'loguru.Logger',
                        data,
                        user_agent: str = None):
    logger.info(f'captcha data: {data}')
    custom_id = data['d']['custom_id'].lstrip('MJ::iframe::')
    user_agent = user_agent or default_user_agent

    async def ack_captcha_url():
        from aiohttp import ClientSession
        async with ClientSession() as session:
            url = f'https://936929561302675456.discordsays.com/captcha/api/c/{custom_id}/ack?hash=1'
            session.headers.update({
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=1, i',
                'referer': 'https://936929561302675456.discordsays.com/captcha/index.html',
                'user-agent': user_agent
            })
            logger.info(f'ack captcha: {url}')
            async with session.get(url) as response:
                result = await response.json()
                logger.info(f'ack captcha result: {result}')
                if 'detail' in result:
                    raise Exception(result['detail'])

            return f'https://editor.midjourney.com/captcha/challenge/index.html?hash={result["hash"]}&token={result["token"]}'

    import asyncio
    await asyncio.sleep(1)
    captcha_url = await ack_captcha_url()
    logger.info(f'solve captcha: {captcha_url}')
    await solve_turnstile(logger, captcha_url, user_agent)
    return True


async def solve_turnstile(logger: 'loguru.Logger',
                          url: str,
                          user_agent: str = None,
                          user_data_path: str = None,
                          screencast_save_path: str = None,
                          timeout: int = 10):
    import asyncio
    from DrissionPage import ChromiumPage, ChromiumOptions
    user_agent = user_agent or default_user_agent
    options = (
        ChromiumOptions()
        .auto_port()
        .headless()
        .incognito(True)
        .set_user_agent(user_agent)
        .set_argument('--guest')
        .set_argument('--no-sandbox')
        .set_argument('--disable-gpu')
    )
    if user_data_path:
        options.set_user_data_path(user_data_path)
    page = ChromiumPage(options)
    if screencast_save_path:
        page.screencast.set_save_path(screencast_save_path)
        page.screencast.set_mode.frugal_imgs_mode()
        page.screencast.start()
    page.get(url)
    logger.debug('waiting for cloudflare turnstile')
    await asyncio.sleep(2)
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
    logger.debug('waiting for "Verify you are human"')
    verify_element = body_element.ele("text:Verify you are human", timeout=timeout)
    logger.debug(f'click at offset of text')
    verify_element.click.at(10, 10)
    logger.debug('waiting for success')
    body_element.ele('xpath://div[@id="success"]', timeout=timeout).wait.displayed(timeout=timeout)
    await asyncio.sleep(1)
    if screencast_save_path:
        page.screencast.stop()
    page.close()


class MidjourneyCaptchaBot(discord.Client):
    def __init__(self, logger: 'loguru.Logger', token: str, guild_id: int, channel_id: int):
        super().__init__(enable_debug_events=True)
        self.__logger = logger
        self.__token = token
        self.__guild_id = guild_id
        self.__channel_id = channel_id

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
        self.__logger.info(f'message: {message.author}: {message.content}')

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
        await self.__command_event.wait()
        self.__logger.info('close bot...')
        await self.close()

    async def __solve_captcha(self, data):
        if await solve_captcha(self.__logger, data):
            self.__command_data = True
            self.__command_event.set()
