class BaseCaptchaSolver:
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'

    def __init__(self, **kwargs):
        """
        Base Captcha Solver
        :param logger:
        :param proxy:
        :param browser_path:
        :param browser_headless:
        :param browser_incognito:
        :param browser_timeout:
        :param browser_user_data_path:
        :param browser_screencast_save_path:
        :param yescaptcha_key:
        :param twocaptcha_key:
        """
        self._kwargs = kwargs
        self._verbose = self._kwargs['verbose']
        self._logger = self._kwargs['logger']
        self._proxy = self._kwargs.get('proxy')
        self._browser_path = self._kwargs.get('browser_path')
        self._browser_headless = self._kwargs.get('browser_headless', True)
        self._browser_incognito = self._kwargs.get('browser_incognito', True)
        self._browser_timeout = self._kwargs.get('browser_timeout', 30)
        self._yescaptcha_key = self._kwargs.get('yescaptcha_key')
        self._twocaptcha_key = self._kwargs.get('twocaptcha_key')
        self._solver = self._kwargs.get('solver')

    async def solve_captcha(self, data):
        self._logger.debug(f'solve captcha: {data}')
        custom_id = data['d']['custom_id'].lstrip('MJ::iframe::')

        async def ack_captcha_url():
            import httpx
            url = f'https://936929561302675456.discordsays.com/captcha/api/c/{custom_id}/ack?hash=1'
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=1, i',
                'referer': 'https://936929561302675456.discordsays.com/captcha/index.html',
                'user-agent': self.USER_AGENT
            }
            async with httpx.AsyncClient(headers=headers, verify=False, proxies=self._proxy) as client:
                self._logger.debug(f'ack captcha: {url}')
                response = await client.get(url)
                if response.status_code != 200:
                    self._logger.error(f'ack captcha failed with status code: {response.status_code}')
                    return None
                result = response.json()
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


class DrissionPageCaptchaSolver(BaseCaptchaSolver):
    def __init__(self, **kwargs):
        """
        Solve Cloudflare turnstile with DrissionPage
        :param logger:
        :param proxy:
        :param browser_headless:
        :param browser_incognito:
        :param browser_path:
        :param browser_user_data_path:
        :param browser_screencast_save_path:
        :param browser_timeout:
        """
        super().__init__(**kwargs)

    async def solve_turnstile(self, url: str) -> bool:
        import asyncio
        import random

        from DrissionPage import ChromiumPage, ChromiumOptions
        options = (
            ChromiumOptions()
            .auto_port()
            .headless(self._browser_headless)
            .incognito(self._browser_incognito)
            .set_user_agent(self.USER_AGENT)
            .set_argument('--no-sandbox')
            .set_argument('--disable-gpu')
        )
        if self._browser_path:
            options.set_browser_path(self._browser_path)
        if self._proxy:
            options.set_proxy(self._proxy)
        self._logger.debug(f'launch browser, {options.__dict__}')
        page = ChromiumPage(options)
        if self._verbose:
            page.screencast.set_save_path('screencast')
            page.screencast.set_mode.frugal_imgs_mode()
            page.screencast.start()

        async def __solve_turnstile() -> bool:
            self._logger.debug(f'get url: {url}')
            await asyncio.sleep(1)
            page.get(url, retry=3)
            self._logger.debug('waiting for cloudflare turnstile')
            await asyncio.sleep(3)
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
            if not iframe:
                self._logger.error('cloudflare iframe not found')
                return False
            body_element = iframe.ele('tag:body', timeout=self._browser_timeout).shadow_root
            await asyncio.sleep(1)
            checkbox_element = body_element.ele('xpath://input[@type="checkbox"]', timeout=self._browser_timeout)
            if not checkbox_element:
                self._logger.warning('cloudflare checkbox not found')
                return False
            self._logger.debug(f'click at random offset position of checkbox')
            width, height = checkbox_element.rect.size
            border = 2
            offset_x = random.randint(border, int(width - border))
            offset_y = random.randint(border, int(height - border))
            page.actions.move_to(checkbox_element, offset_x, offset_y)
            checkbox_element.click.at(offset_x, offset_y)
            self._logger.info('waiting for success element')
            result = (body_element.ele('xpath://div[@id="success"]', timeout=self._browser_timeout)
                      .wait.displayed(timeout=self._browser_timeout))
            if not result:
                self._logger.error('success element not found')
            return result

        solved = False
        try:
            solved = await __solve_turnstile()
        except Exception as e:
            self._logger.error(f'error: {e}')
        await asyncio.sleep(1)
        if self._verbose:
            page.screencast.stop()
        page.quit()
        return solved


class PlaywrightCaptchaSolver(BaseCaptchaSolver):
    def __init__(self, **kwargs):
        """
        Solve Cloudflare turnstile with Playwright
        :param logger:
        :param proxy:
        :param browser_headless:
        :param browser_timeout:
        """
        super().__init__(**kwargs)
        if not self._solver:
            raise ValueError('Please provide a captcha solver')

    async def solve_turnstile(self, url) -> bool:
        import asyncio
        from playwright.async_api import async_playwright, Response

        @self._logger.catch
        async def __solve_turnstile() -> bool:
            async with async_playwright() as p:
                self._logger.debug(f'launch browser, headless: {self._browser_headless}')
                proxy = {'server': self._proxy} if self._proxy else None
                browser = await p.chromium.launch(headless=self._browser_headless, proxy=proxy)
                page = await browser.new_page(user_agent=self.USER_AGENT)

                import re
                site_key: str | None = None
                site_key_event = asyncio.Event()
                # https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/g/turnstile/if/ov2/av0/rcv/1l82o/0x4AAAAAAAat3Zn0na9wnvrt/auto/fbE/auto_expire/normal/auto/
                site_key_regex = re.compile(r'https://challenges.cloudflare.com/.*?/(0x[a-zA-Z0-9]{22})/')

                custom_id: str | None = None
                custom_id_event = asyncio.Event()
                # https://editor.midjourney.com/captcha/api/c/oI4cLSolUU6h2--V3n3TvznU_HHABugkDQ0WECvDcKI5QBpq16-pwBSnwCro7hlmEn4Tkuf3NjbQf1w6/ack?hash=nl2cj4Lkt6m9z3Z_aKKIQA
                custom_id_regex = re.compile(r'https://editor.midjourney.com/captcha/api/c/(.*?)/ack\?hash=')

                async def handle_response(response: Response):
                    response_url = response.url
                    self._logger.debug(f'response url: {response_url}')
                    custom_id_match = custom_id_regex.match(response_url)
                    if custom_id_match:
                        nonlocal custom_id
                        custom_id = custom_id_match.group(1)
                        self._logger.info(f'custom id: {custom_id}')
                        custom_id_event.set()
                        return
                    site_key_match = site_key_regex.match(response_url)
                    if site_key_match:
                        nonlocal site_key
                        site_key = site_key_match.group(1)
                        self._logger.info(f'site key: {site_key}')
                        site_key_event.set()
                        return

                self._logger.debug('add response event listener')
                page.on('response', handle_response)
                self._logger.debug('inject navigator properties')
                await page.add_init_script(f'''
                    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                    Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3] }});
                    Object.defineProperty(navigator, 'languages', {{ get: () => ['en-US', 'en'] }});
                    Object.defineProperty(navigator, 'platform', {{ get: () => 'Win32' }});
                    Object.defineProperty(navigator, 'userAgent', {{ get: () => '{self.USER_AGENT}' }});
                ''')
                self._logger.info(f'goto url: {url}')
                await page.goto(url, wait_until='domcontentloaded')
                self._logger.info('waiting for site key and custom id...')
                await asyncio.wait_for(
                    asyncio.gather(site_key_event.wait(), custom_id_event.wait()),
                    timeout=self._browser_timeout
                )
                self._logger.info('solve captcha...')
                task_id = await self._solver.create_turnstile_task(url, site_key)
                self._logger.info(f'task id: {task_id}')
                captcha_token = await self._solver.get_turnstile_result(task_id)
                self._logger.info(f'submit captcha token: {captcha_token}')
                result = await page.request.post(
                    f'https://editor.midjourney.com/captcha/api/c/{custom_id}/submit',
                    form={'captcha_token': captcha_token}
                )
                self._logger.info(f'response: {result.status}, {await result.text()}')
                await asyncio.sleep(1)
                return True

        return await __solve_turnstile()
