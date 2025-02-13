# Midjourney Captcha Bot

[中文](./README.zh-CN.md)

A bot to solve midjourney captcha for [midjourney-proxy](https://github.com/litter-coder/midjourney-proxy-plus);

## Configuration

```shell
# Create a virtual environment
python -m venv venv
# Activate the virtual environment
# Linux or macOS
source venv/bin/activate
# Windows Command Prompt
venv\Scripts\activate.bat
# Windows PowerShell
venv\Scripts\activate.ps1
# Install the required packages
pip install -r requirements.txt
```

## Run with Playwright and YesCaptcha or 2Captcha

1. Register [YesCaptcha](https://yescaptcha.com/i/lSoGCH) or [2Captcha](https://2captcha.com?from=11867999);
2. Copy the `Client Key` or `API Key`, like `3c21....3221`;
3. Run the following command to start the server:
    ```shell
    # YesCaptcha
    python server.py --solver-type=playwright --yescaptcha-api-key=3c21....3221
    # 2Captcha
    python server.py --solver-type=playwright --2captcha-api-key=3c21....3221
    ```
4. For more args, run `python server.py --help`;

