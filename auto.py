from loguru import logger


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Midjourney Captcha Bot for midjourney-proxy-plus')
    parser.add_argument('--api_host', type=str, required=True, help='API host')
    parser.add_argument('--api_secret', type=str, required=True, help='API secret')
    args = parser.parse_args()

    from aiohttp import ClientSession
    session = ClientSession()
    session.headers.update({
        'mj-api-secret': args.api_secret
    })
    api_host = args.api_host.rstrip('/')
    logger.info(f'get disabled accounts from {api_host}')
    response = await session.post(f'{api_host}/mj/account/query', json={
        "pageNumber": 0,
        "pageSize": 10000,
        "enable": False,
    })
    accounts = (await response.json())['content']
    logger.info(f'count: {len(accounts)}')

    for account in accounts:
        account_id = account['id']
        disable_reason = account['properties']['disabledReason']
        if '/captcha/' not in disable_reason:
            logger.info(f'skip account: {account_id}, reason: {disable_reason}')
            continue

        logger.info(f'handle account: {account_id}')
        guild_id = account['guildId']
        channel_id = account['channelId']
        user_token = account['userToken']

        from utils import MidjourneyCaptchaBot
        bot = MidjourneyCaptchaBot(logger, user_token, int(guild_id), int(channel_id))
        result = await bot.imagine('a cat --relax')
        if not result:
            logger.error(f'failed to imagine for {account_id}')
            continue

        logger.info(f'enable account: {account_id}')
        result = await session.put(f'{api_host}/mj/account/{account_id}/update-reconnect', json={
            "enable": True,
            "channelId": channel_id,
            "guildId": guild_id,
            "userToken": user_token
        })
        logger.info(f'result: {await result.json()}')

    await session.close()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
