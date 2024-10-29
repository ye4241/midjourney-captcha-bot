async def run(**kwargs):
    from fastapi import FastAPI, Request, HTTPException
    from loguru import logger

    app = FastAPI()

    @app.get('/')
    async def root():
        return 'Midjourney Captcha Bot'

    @app.api_route('/captcha/solve', methods=['POST', 'GET'])
    async def solve_captcha(request: Request):
        if request.method == 'GET':
            url = request.query_params.get('url')
        else:
            url = (await request.json()).get('url')
        if not url:
            raise HTTPException(status_code=400, detail='url is required')

        from urllib.parse import urlparse
        if not urlparse(url).scheme:
            raise HTTPException(status_code=400, detail='invalid url')

        from utils import BrowserCaptchaSolver
        solver = BrowserCaptchaSolver(logger, **kwargs)
        result = solver.solve_turnstile(url)
        if not result:
            raise HTTPException(status_code=500, detail='failed to solve')

        return {'code': 200, 'message': 'success'}

    import uvicorn
    config = uvicorn.Config(app, host=kwargs['host'], port=kwargs['port'])
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Midjourney Captcha Bot')
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--proxy', type=str, default=None, help='Proxy')
    parser.add_argument('--browser_path', type=str, default=None, help='Browser path')
    parser.add_argument('--browser_headless', type=str, choices=['true', 'false'], default='true',
                        help='Browser headless')
    parser.add_argument('--browser_timeout', type=int, default=10, help='Browser timeout')
    parser.add_argument('--browser_user_data_path', type=str, default=None, help='Browser User data path')
    parser.add_argument('--browser_screencast_save_path', type=str, default=None, help='Browser Screencast save path')
    parser.add_argument('--browser_yescaptcha_path', type=str, default='yescaptcha-assistant',
                        help='Browser YesCaptcha path')

    args = parser.parse_args()
    args.browser_headless = True if args.browser_headless == 'true' else False
    await run(**vars(args))


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
