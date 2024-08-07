async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Midjourney Captcha Bot for midjourney-proxy-plus')
    parser.add_argument('--connection_string', type=str, required=True,
                        help='Connection string, e.g. mysql+mysqlconnector://user:password@localhost/dbname')
    parser.add_argument('--prompt', type=str, default='a cat --relax', help='Imagine prompt')
    args = parser.parse_args()

    from sqlalchemy import create_engine, text
    connection_string = args.connection_string
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        accounts = connection.execute(text('''select guild_id, channel_id, user_token
    from mj_account
    where enable = 0
      and json_extract(properties, '$.disabledReason') like '%captcha%';''')).fetchall()

    from utils import MidjourneyCaptchaBot
    for account in accounts:
        guild_id, channel_id, user_token = account
        bot = MidjourneyCaptchaBot(user_token, guild_id, channel_id)
        await bot.imagine(args.prompt)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
