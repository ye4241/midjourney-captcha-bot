import unittest
from loguru import logger


class Tests(unittest.IsolatedAsyncioTestCase):
    async def test_solve_turnstile(self):
        from utils import solve_turnstile
        await solve_turnstile(logger, 'https://2captcha.com/demo/cloudflare-turnstile', browser_headless=False)
