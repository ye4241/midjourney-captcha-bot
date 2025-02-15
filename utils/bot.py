import discord

class MidjourneyBot(discord.Client):
    MIDJOURNEY_BOT_ID = 936929561302675456
    import loguru
    from .solver import BaseCaptchaSolver

    def __init__(self, logger: 'loguru.Logger', token: str, guild_id: int, channel_id: int, solver: BaseCaptchaSolver):
        super().__init__(enable_debug_events=True)
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
        await self.__command_event.wait()
        return self.__command_data

    async def on_ready(self):
        import asyncio
        self.__logger.info(f'logged: {self.user.name}')
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
            if 'You are blocked.' in embed_title or 'Subscription paused' in embed_title or 'Subscription required' in embed_title or 'Pending mod message' in embed_title:
                self.__command_data = False
                self.__command_event.set()

    async def on_socket_raw_receive(self, msg):
        import asyncio
        import json
        data = json.loads(msg)
        if data['t'] == 'INTERACTION_IFRAME_MODAL_CREATE':
            self.__logger.info(f'interaction iframe modal create: {data}')
            if '/captcha/' in data['d']['iframe_path']:
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
            self.__command_event.set()
        self.__logger.info('close bot...')
        await self.close()

    async def __solve_captcha(self, data):
        self.__command_data = await self.__solver.solve_captcha(data)
        self.__command_event.set()
