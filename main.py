# ---------------------
# desc m3u8 url 扒取
# user onexian
# date 20240928
# ---------------------

import os
import json
import requests
import argparse
import subprocess
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import urllib.parse
import time

# 记录程序开始时间
start_time = time.time()

# 创建参数解析器
# 支持url 例子 
# 1. https://www.vvvdj.com/radio/212.html
parser = argparse.ArgumentParser(description='输入url: https://www.vvvdj.com/radio/212.html')
# 添加参数
parser.add_argument('--url', type=str, required=True, help='url')
parser.add_argument('--type', type=str, required=False, default='1')
parser.add_argument('--suffix', type=str, required=False, default='mp3') # 文件后缀

# 解析命令行参数
args = parser.parse_args()

# 爬取目标网站的URL
# scheme='https', netloc='www.vvvdj.com', path='/radio/212.html'
parsed_url = urllib.parse.urlparse(args.url)
base_download_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
download_url = args.url
download_type = args.type
m3u8_suffix = args.suffix


# =================================== mkdir path start ===========================
# 获取当前运行文件的绝对路径
file_path = os.path.abspath(__file__)
# 获取当前运行文件所在的目录
directory = os.path.dirname(file_path)

filename_path = directory + '/filename.json'
m3u8_path = directory + '/m3u8.txt'
temp_path = directory + '/temp.txt'
download_main = directory + '/download.py'

# =================================== mkdir path end ===========================


if download_type == '1':
    download_url = base_download_url

    # 清空缓存目录
    if os.path.exists(filename_path):
        os.remove(filename_path)
    if os.path.exists(m3u8_path):
        os.remove(m3u8_path)
    if os.path.exists(temp_path):
        os.remove(temp_path)


print('download_url: '+ download_url + ' download_type:' + download_type)

# print(args)
# exit()

# 使用无头模式（不会显示浏览器窗口）
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 手动设置 Chrome 或 Chromium 的路径
options.binary_location = "/usr/bin/chromium-browser"

# 设置 ChromeDriver 路径
service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=options)

# 打开目标网站
driver.get(download_url)

# 等待几秒，确保页面动态内容加载完成
time.sleep(5)

# 获取所有链接
# all_urls = [a.get_attribute('href') for a in driver.find_elements(By.TAG_NAME, 'a') if a.get_attribute('href')]
# print("All page URLs:", all_urls)

# 获取通过 JS 加载的资源（如 AJAX 请求的 URL）
# xhr_urls = [req['name'] for req in driver.execute_script("return window.performance.getEntriesByType('resource');")]

# print("All XHR and resource URLs:", xhr_urls)

# 获取通过 JS 加载的资源，并过滤出 .m3u8 后缀和指定的 URL
# xhr_urls = [
#     req['name'] for req in driver.execute_script("return window.performance.getEntriesByType('resource');")
#     if '.m3u8' in req['name'] or 'https://www.vvvdj.com/play/ajax/temp' in req['name']
# ]

xhr_urls = [
    {
        'url': req['name'],
        'type': 'm3u8' if '.m3u8' in req['name'] else 'temp'
    }
    for req in driver.execute_script("return window.performance.getEntriesByType('resource');")
    if '.m3u8' in req['name'] or 'https://www.vvvdj.com/play/ajax/temp' in req['name']
]

# print("Filtered XHR and resource URLs:", xhr_urls)


driver.quit()


# 记录程序结束时间
end_time = time.time()

# 计算运行时长
elapsed_time = end_time - start_time
print(f"Total runtime: {elapsed_time:.2f} seconds")


# 读取文件并转换为字符数组
def read_file_to_array(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()  # 读取文件内容
        parsed_string = json.loads(content)
        data = json.loads(parsed_string)
        # print( data )
        # exit()

    return list(data.values())  # 转换为字符数组

# 将字符数组转换为带有唯一ID的关联数组（字典）
def convert_to_id_associative_array(char_array):
    id_dict = {item['id']: item for item in char_array}
    return id_dict

# 保存 m3u8 URL 到 m3u8.txt
with open(m3u8_path, 'a') as m3u8_file:
    for entry in xhr_urls:
        if entry['type'] == 'm3u8':

            char_array = []
            if os.path.exists(filename_path):
                char_array = read_file_to_array(filename_path)

            mp3name = 'empty'
            if len(char_array) > 1:
                id_associative_array = convert_to_id_associative_array(char_array[1])

                # m3u8 地址
                # 找到最后一个斜杠的位置
                last_slash_index = entry['url'].rfind('/')

                # 切分基础路径和文件名
                base_url = entry['url'][:last_slash_index + 1]  # 包含最后的斜杠
                m3u8_id = entry['url'][last_slash_index + 1:].split('.')[0]

                # 检查 m3u8_id 是否在关联数组中
                if m3u8_id in id_associative_array:
                    # 从关联数组中获取 mp3name
                    mp3name = id_associative_array[m3u8_id]['musicname']
                    # 判断 mp3name 是否为空
                    if not mp3name:
                        mp3name = m3u8_id  # 如果为空，则赋值为 m3u8_id
                else:
                    # 如果 m3u8_id 不存在，给 mp3name 赋一个默认值
                    mp3name = m3u8_id  # 或者你可以选择其他的默认值

            # 异步下载 启动异步进程
            if mp3name != "empty":
                print('async download start')
                subprocess.run(['python3', download_main, '--url', entry['url'], '--filename', mp3name, '--suffix', m3u8_suffix], check=True)
                # subprocess.Popen(['python3', 'download.py', '--url', entry['url'], '--filename', mp3name, '--suffix', m3u8_suffix], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print('async download end')
                
                m3u8_file.write(entry['url']+ ' ' + mp3name + '\n')


if download_type == '1':
    # 保存 temp URL 到 temp.txt
    with open(temp_path, 'a') as temp_file:
        for entry in xhr_urls:
            if entry['type'] == 'temp':
                temp_file.write(entry['url'] + '\n')

    # 保存 filename
    with open(filename_path, 'a') as filename_file:
        for entry in xhr_urls:
            if entry['type'] == 'temp':
                try:
                    # 发送 GET 请求获取 URL 的返回结果
                    response = requests.get(entry['url'])
                    # 检查请求是否成功
                    if response.status_code == 200:
                        # 将返回内容写入文件
                        filename_file.write(response.text + '\n')
                    else:
                        print(f"Error fetching {entry['url']}: {response.status_code}")

                except Exception as e:
                    print(f"Exception occurred while fetching {entry['url']}: {e}")

    for entry in xhr_urls:
        if entry['type'] == 'temp':
            # 解析 URL 获取参数
            parsed_url = urllib.parse.urlparse(entry['url'])
            query_params = urllib.parse.parse_qs(parsed_url.query)
            # 获取 ids 参数并拆分
            ids = query_params.get('ids', [''])[0].split(',')
            # 生成新的 URL
            new_urls = [f"{base_download_url}?musicid={id_}" for id_ in ids]

            # 循环处理新 URL
            for new_url in new_urls:
                print(f"run-url: {new_url}")
                # 调用 main.py 并传递 url 参数
                try:
                    result = subprocess.run(['python3', file_path, '--url', new_url, '--type', '2'], check=True)
                    print(f"run-url end: {new_url}")
                except subprocess.CalledProcessError as e:
                    print(f"Error running command for url {new_url}: {e}")


print('all end')