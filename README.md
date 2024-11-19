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

## Run

```shell
python server.py
```

## YesCaptcha(optional)

1. Register [YesCaptcha](https://yescaptcha.com/i/lSoGCH) (<- affiliate link);
2.
Download [Extension Zip](https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/25722881/YesCaptcha#%EF%BC%88%E4%BA%8C%EF%BC%89%E3%80%81%E4%B8%8B%E8%BD%BDChrome%E5%AE%89%E8%A3%85%E5%8C%85%E8%87%AA%E5%8A%A9%E5%AE%89%E8%A3%85);
3. UniZip the extension into `yescaptcha-assistant` folder;
4. Config the `config.js` file with `clientKey`.
