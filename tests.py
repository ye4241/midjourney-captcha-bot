import os
import unittest
from loguru import logger
from utils import MidjourneyBot, PlaywrightCaptchaSolver, DrissionPageCaptchaSolver


class Tests(unittest.IsolatedAsyncioTestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.__prompt = 'a cat --relax'
        self.__captcha_solver_args = {
            'logger': logger,
            'proxy': os.environ.get('PROXY'),
            'browser_headless': False,
            'browser_incognito': True,
            'yescaptcha_key': os.environ.get('YESCAPTCHA_KEY'),
            'twocaptcha_key': os.environ.get('TWOCAPTCHA_KEY'),
        }
        self.__midjourney_bot_args = {
            'logger': logger,
            'token': os.environ.get('DISCORD_TOKEN'),
            'guild_id': int(os.environ.get('DISCORD_GUILD_ID', 0)),
            'channel_id': int(os.environ.get('DISCORD_CHANNEL_ID', 0)),
        }

    async def test_imagine_by_playwright(self):
        solver = PlaywrightCaptchaSolver(**self.__captcha_solver_args)
        bot = MidjourneyBot(**self.__midjourney_bot_args, solver=solver)
        await bot.imagine(self.__prompt)

    async def test_imagine_by_drissonpage(self):
        solver = DrissionPageCaptchaSolver(**self.__captcha_solver_args)
        bot = MidjourneyBot(**self.__midjourney_bot_args, solver=solver)
        await bot.imagine(self.__prompt)
