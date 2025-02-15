# Midjourney Captcha Bot

自动解决 [midjourney-proxy](https://github.com/litter-coder/midjourney-proxy-plus) 的验证码的机器人;

## 配置

```shell
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
# Linux or macOS
source venv/bin/activate
# Windows 提示命令行
venv\Scripts\activate.bat
# Windows PowerShell
venv\Scripts\activate.ps1
# 安装所需的包，建议开全局代理后再安装，不然会很慢甚至失败
pip install -r requirements.txt
# 安装 Playwright
playwright install
# 如果你想使用 Discord 机器人，安装 discord-self 包
pip install git+https://github.com/dolfies/discord.py-self.git
```

## 搭配 Playwright 和 YesCaptcha / 2Captcha 运行

1. 注册 [YesCaptcha](https://yescaptcha.com/i/lSoGCH) 或 [2Captcha](https://2captcha.com?from=11867999)；
2. 复制 `Client Key` 或者 `API Key`，如 `3c21....3221`；
3. 运行以下命令启动服务器:
    ```shell
    # YesCaptcha
    python server.py --solver-type=playwright --yescaptcha-key=3c21....3221
    # 2Captcha
    python server.py --solver-type=playwright --2captcha-key=3c21....3221
    ```
4. 更多参数, 运行 `python server.py --help`；