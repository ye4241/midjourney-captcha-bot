from loguru import logger


async def main():
    from fastapi import FastAPI, Request

    app = FastAPI()

    @app.post('solve/catpcha')
    async def solve_captcha(request: Request):
        from utils import solve_captcha
        data = await request.json()
        await solve_captcha(logger, data)

    @app.post('solve/turnstile')
    async def solve_turnstile(request: Request):
        from utils import solve_turnstile
        data = await request.json()
        await solve_turnstile(logger, data.get('url'), data.get('user_agent'))

    import uvicorn
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
