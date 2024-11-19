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
# 安装所需的包
pip install -r requirements.txt
```

## Run

```shell
python auto.py
```

## YesCaptcha(可选步骤)

1. 注册 [YesCaptcha](https://yescaptcha.com/i/lSoGCH) (<- 推广链接);
2. 下载 [Extension Zip](https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/25722881/YesCaptcha#%EF%BC%88%E4%BA%8C%EF%BC%89%E3%80%81%E4%B8%8B%E8%BD%BDChrome%E5%AE%89%E8%A3%85%E5%8C%85%E8%87%AA%E5%8A%A9%E5%AE%89%E8%A3%85);
3. 解压插件到 `yescaptcha-assistant` 目录;
4. 配置 `config.js` 文件中的 `clientKey`.
