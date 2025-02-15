async def hook(api_host: str, api_secret: str, **kwargs):
    logger = kwargs['logger']
    solver = kwargs['solver']
    import httpx
    async with httpx.AsyncClient(verify=False) as client:
        client.headers.update({
            'mj-api-secret': api_secret
        })
        api_host = api_host.rstrip('/')
        logger.info(f'get disabled accounts from {api_host}')
        response = await client.post(f'{api_host}/mj/account/query', json={
            "pageNumber": 0,
            "pageSize": 10000,
            "enable": False,
        })
        response.raise_for_status()
        accounts = response.json()['content']
        logger.info(f'count: {len(accounts)}')

        imagine_delay = kwargs.pop('imagine_delay', 10)
        imagine_prompt = kwargs.pop('imagine_prompt', 'a cat --relax')
        imagine_timeout = kwargs.pop('imagine_timeout', 120)

        for account in accounts:
            account_id = account['id']
            disable_reason = account.get('properties', {}).get('disabledReason', '')
            if '/captcha/' not in disable_reason:
                logger.info(f'skip account: {account_id}, reason: {disable_reason}')
                continue

            logger.info(f'handle account: {account_id}')
            guild_id = int(account['guildId'])
            channel_id = int(account['channelId'])
            user_token = account['userToken']

            from utils.bot import MidjourneyBot
            bot = MidjourneyBot(logger, user_token, guild_id, channel_id, solver)
            solved = await bot.imagine(imagine_prompt, imagine_timeout)
            if not solved:
                logger.error(f'failed to imagine for {account_id}')
                continue

            logger.info(f'enable account: {account_id}')
            account['enable'] = True
            response = await client.put(f'{api_host}/mj/account/{account_id}/update-reconnect', json=account)
            response.raise_for_status()
            logger.info(f'result: {response.json()}')

            await asyncio.sleep(imagine_delay)


async def run(**kwargs):
    from datetime import datetime
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = AsyncIOScheduler()
    cron = kwargs.pop('cron')
    cron_trigger = CronTrigger.from_crontab(cron)
    scheduler.add_job(
        hook,
        kwargs=kwargs,
        trigger=cron_trigger,
        id='hook',
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.now()
    )
    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass


async def main():
    from utils import build_parser, parse_args
    parser = build_parser()
    parser.add_argument('--api-host', type=str, required=True, help='Midjourney Proxy API host')
    parser.add_argument('--api-secret', type=str, required=True, help='Midjourney Proxy API secret')
    parser.add_argument('--cron', type=str, default='*/10 * * * *', help='Cron expression')
    parser.add_argument('--imagine-delay', type=int, default=10, help='Delay between imagines')
    parser.add_argument('--imagine-prompt', type=str, default='a cat --relax', help='Prompt for imagine')
    parser.add_argument('--imagine-timeout', type=int, default=120, help='Timeout for imagine')
    args = parse_args(parser)
    await run(**args)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
