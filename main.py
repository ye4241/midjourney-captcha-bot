async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Midjourney Captcha Bot')
    parser.add_argument('--token', type=str, required=True, help='Discord token')
    parser.add_argument('--guild_id', type=int, required=True, help='Discord guild id')
    parser.add_argument('--channel_id', type=int, required=True, help='Discord channel id')
    parser.add_argument('--prompt', type=str, default='a cat --relax', help='Imagine prompt')
    args = parser.parse_args()

    from utils import MidjourneyCaptchaBot
    bot = MidjourneyCaptchaBot(args.token, args.guild_id, args.channel_id)
    await bot.imagine(args.prompt)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
