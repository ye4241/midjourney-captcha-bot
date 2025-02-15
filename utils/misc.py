import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Midjourney Captcha Bot')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--solver-type', type=str, choices=['playwright', 'drissonpage'], default='playwright', help='Captcha solver type')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy server, e.g. http://localhost:8888')
    parser.add_argument('--browser-path', type=str, default=None, help='Browser executable path')
    parser.add_argument('--browser-headless', type=str, choices=['true', 'false'], default='true', help='Browser headless mode')
    parser.add_argument('--browser-incognito', type=str, choices=['true', 'false'], default='true', help='Browser headless mode')
    parser.add_argument('--browser-timeout', type=int, default=30, help='Browser timeout in seconds')
    parser.add_argument('--yescaptcha-key', type=str, help='Yescaptcha API key, register from https://yescaptcha.com/i/lSoGCH')
    parser.add_argument('--twocaptcha-key', type=str, help='2Captcha API key, register from https://2captcha.com/?from=11867999')
    return parser


def parse_args(parser: argparse.ArgumentParser) -> dict:
    args = vars(parser.parse_args())
    args = {k.replace('-', '_'): v for k, v in args.items()}
    args['browser_headless'] = args['browser_headless'] == 'true'
    args['browser_incognito'] = args['browser_incognito'] == 'true'
    verbose = args['verbose']
    from loguru import logger
    logger.remove()
    import sys
    if verbose:
        logger.add(sys.stderr, level='DEBUG')
    else:
        logger.add(sys.stderr, level='INFO')
    args['logger'] = logger
    solver_type = args.pop('solver_type')
    if solver_type == 'playwright':
        from utils import PlaywrightCaptchaSolver
        args['solver'] = PlaywrightCaptchaSolver(**args)
    elif solver_type == 'drissonpage':
        from utils import DrissionPageCaptchaSolver
        args['solver'] = DrissionPageCaptchaSolver(**args)
    return args
