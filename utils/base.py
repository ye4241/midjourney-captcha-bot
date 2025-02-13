import httpx
from tenacity import retry, stop_after_attempt, wait_fixed


class BaseCaptchaSolver:
    def __init__(self, api_key: str, base_url: str | None = None, proxy: str | None = None):
        self._api_key = api_key
        self._base_url = base_url
        self._proxy = proxy

    def _get_session(self) -> httpx.AsyncClient:
        session = httpx.AsyncClient(base_url=self._base_url, proxy=self._proxy)
        return session

    async def create_task(self, data) -> dict:
        raise NotImplementedError

    async def get_result(self, task_id: str) -> dict:
        raise NotImplementedError

    async def create_turnstile_task(self, website_url: str, website_key: str):
        raise NotImplementedError

    async def get_turnstile_result(self, task_id: str) -> str | None:
        raise NotImplementedError


class YesCaptchaSolver(BaseCaptchaSolver):
    def __init__(self, api_key: str, base_url: str | None = None, proxy: str | None = None):
        super().__init__(api_key, base_url or 'https://api.yescaptcha.com', proxy)

    async def __post(self, url, data) -> dict:
        async with self._get_session() as session:
            response = await session.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            error_id = result.get('errorId')
            if error_id:
                raise Exception(f'error: {result}')
            return result

    async def create_task(self, data) -> dict:
        result = await self.__post('/createTask', {
            'clientKey': self._api_key,
            'task': data
        })
        return result

    async def get_result(self, task_id: str) -> dict:
        data = await self.__post('/getTaskResult', {
            'clientKey': self._api_key,
            'taskId': task_id
        })
        return data

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def create_turnstile_task(self, website_url: str, website_key: str):
        response = await self.create_task({
            'type': 'TurnstileTaskProxyless',
            'websiteURL': website_url,
            'websiteKey': website_key
        })
        task_id = response.get('taskId')
        if not task_id:
            raise Exception(f'error: {response}')
        return task_id

    @retry(stop=stop_after_attempt(30), wait=wait_fixed(1))
    async def get_turnstile_result(self, task_id: str) -> str | None:
        response = await self.get_result(task_id)
        token = response.get('solution', {}).get('token')
        if not token:
            raise Exception(f'error: {response}')
        return token


class TwoCaptchaSolver(BaseCaptchaSolver):
    def __init__(self, api_key: str, proxy: str | None = None):
        super().__init__(api_key, base_url='https://2captcha.com', proxy=proxy)

    async def create_task(self, data) -> dict:
        async with self._get_session() as session:
            response = await session.get('/in.php', params={
                'key': self._api_key,
                'json': 1,
                **data
            })
            response.raise_for_status()
            result = response.json()
            status = result.get('status')
            if not status or status != 1:
                raise Exception(f'error: {result}')
            return result

    async def get_result(self, task_id: str) -> dict:
        async with self._get_session() as session:
            response = await session.get('/res.php', params={
                'key': self._api_key,
                'action': 'get',
                'id': task_id,
                'json': 1
            })
            response.raise_for_status()
            result = response.json()
            status = result.get('status')
            if not status or status != 1:
                raise Exception(f'error: {result}')
            return result

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def create_turnstile_task(self, website_url: str, website_key: str):
        response = await self.create_task({
            'method': 'turnstile',
            'sitekey': website_key,
            'pageurl': website_url
        })
        task_id = response.get('request')
        if not task_id:
            raise Exception(f'error: {response}')
        return task_id

    @retry(stop=stop_after_attempt(30), wait=wait_fixed(1))
    async def get_turnstile_result(self, task_id: str) -> str | None:
        response = await self.get_result(task_id)
        token = response.get('request')
        if not token:
            raise Exception(f'error: {response}')
        return token
