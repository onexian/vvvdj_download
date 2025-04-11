# 清风DJ www.vvvdj.com 专辑下载

必要插件
ffmpeg
chromium
chromium-chromedriver

```

1.
docker image: python:3.12.5-alpine3.19 
apk update && apk add --no-cache \
    ffmpeg \
    chromium \
    chromium-chromedriver

2.
pip3 install -r requirements.txt

3. 
python3 main.py --url https://www.vvvdj.com/radio/212.html
仅支持：https://www.vvvdj.com/radio/(专辑ID).html

```