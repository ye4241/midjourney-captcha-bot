async def run(**kwargs):
    from fastapi import FastAPI, Request, HTTPException

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

        solver = kwargs['solver']
        result = await solver.solve_turnstile(url)
        if not result:
            raise HTTPException(status_code=500, detail='failed to solve')

        return {'code': 200, 'message': 'success'}

    import uvicorn
    config = uvicorn.Config(app, host=kwargs['host'], port=kwargs['port'])
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    from utils import build_parser, parse_args
    parser = build_parser()
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    args = parse_args(parser)
    await run(**args)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
