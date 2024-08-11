import unittest
from loguru import logger


class Tests(unittest.IsolatedAsyncioTestCase):
    async def test_solve_turnstile(self):
        from utils import BrowserCaptchaSolver
        solver = BrowserCaptchaSolver(logger)
        await solver.solve_turnstile('https://2captcha.com/demo/cloudflare-turnstile')
