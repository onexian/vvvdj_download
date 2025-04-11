# ---------------------
# desc 单 url m3u8 下载
# user onexian
# date 20240927
# ---------------------

import os
import requests
import asyncio
import json
import argparse
import shutil
import subprocess
import hashlib
from requests.exceptions import ConnectionError, Timeout
import time

# 创建参数解析器
parser = argparse.ArgumentParser(description='输入url: https://tspc.vvvdj.com/c2/2016/07/133499-26880a/133499.m3u8')
# 添加参数
parser.add_argument('--url', type=str, required=True, help='url')
parser.add_argument('--filename', type=str, required=False, default='') # 文件名
parser.add_argument('--suffix', type=str, required=False, default='mp3') # 文件后缀

# 解析命令行参数
args = parser.parse_args()
# m3u8 地址
# 找到最后一个斜杠的位置
last_slash_index = args.url.rfind('/')

# 切分基础路径和文件名
base_url = args.url[:last_slash_index + 1]  # 包含最后的斜杠
m3u8_url = base_url + args.url[last_slash_index + 1:]
m3u8_id = args.url[last_slash_index + 1:].split('.')[0]
m3u8_filename = args.filename
m3u8_suffix = args.suffix

# base_url = 'https://tspc.vvvdj.com/c2/2016/07/133499-26880a/'  # 替换为实际的 base URL
# m3u8_url = base_url + '133499.m3u8'

# print( m3u8_url )
# exit()

# =================================== mkdir path start ===========================
# 获取当前运行文件的绝对路径
file_path = os.path.abspath(__file__)
# 获取当前运行文件所在的目录
directory = os.path.dirname(file_path)

# 下载的文件保存目录
save_dir = directory + '/' + m3u8_suffix

# 定义保存 .ts 文件的目录
md5_hash = hashlib.md5(m3u8_url.encode()).hexdigest()
ts_files_dir = directory + '/tmp_ts/' + md5_hash
# ts_files_dir = directory + '/tmp_ts'


# 检查目录是否存在，如果不存在则创建
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 先清除旧的无用
if os.path.exists(ts_files_dir):
    try:
        # 删除文件夹及其所有内容
        shutil.rmtree(ts_files_dir)
    except Exception as e:
        print(f'删除文件夹 {ts_files_dir} 时发生错误: {e}')
        exit()



# 检查目录是否存在，如果不存在则创建
if not os.path.exists(ts_files_dir):
    os.makedirs(ts_files_dir)

# =================================== mkdir path end ===========================


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

if not m3u8_filename:  # 如果为空字符串或 None

    char_array = read_file_to_array(directory+'/filename.json')
    id_associative_array = convert_to_id_associative_array(char_array[1])
    # print( id_associative_array['130949'] )


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


else:
    mp3name = m3u8_filename

mp3_filename = save_dir+'/'+mp3name+'.'+m3u8_suffix
# 判断文件是否存在，存在跳过
if os.path.exists(mp3_filename):
    print('filename exists: ' + mp3_filename)
    shutil.rmtree(ts_files_dir)
    exit()

# print(mp3name)
# exit()
download_m3u8_index = save_dir + '/m3u8.txt'
download_m3u8 = ts_files_dir + '/playlist.m3u8'
ts_list_txt = ts_files_dir + '/ts_list.txt'
output_ts = ts_files_dir + '/autputs.ts'

# 下载 m3u8 文件
response = requests.get(m3u8_url)
with open(f'{download_m3u8}', 'wb') as f:
    f.write(response.content)

def fetch_ts_file(full_ts_url, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            ts_response = requests.get(full_ts_url, timeout=timeout)
            ts_response.raise_for_status()  # 检查 HTTP 状态码
            return ts_response
        except (ConnectionError, Timeout) as e:
            print(f"Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # 等待2秒再重试
            else:
                print(f"Failed to fetch {full_ts_url} after {retries} attempts.")
                return None


# 解析并下载 .ts 文件
ts_files = []  # 存储文件列表
with open(f'{download_m3u8}', 'r') as f:
    ts_urls = [line.strip() for line in f if line and not line.startswith('#')]
    
    for i, ts_url in enumerate(ts_urls):
        # 拼接完整的 ts 文件 URL
        full_ts_url = base_url + ts_url
        # ts_response = requests.get(full_ts_url)
        ts_response = fetch_ts_file(full_ts_url)

        ts_file_path = f'{ts_files_dir}/file{i}.ts'
        
        # 保存 .ts 文件
        with open(ts_file_path, 'wb') as ts_file:
            ts_file.write(ts_response.content)
        
        ts_files.append(f"file '{ts_file_path}'")  # 为 ffmpeg 生成列表

# 写入 filelist.txt 文件
with open(f'{ts_list_txt}', 'w') as f:
    f.write("\n".join(ts_files))


# # 合并 .ts 文件为 mp3
# # 合并 .ts 文件为一个 .ts 文件
# # os.system(f'ffmpeg -f concat -safe 0 -i "{ts_list_txt}" -c copy "{output_ts}"')
# subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', ts_list_txt, '-c', 'copy', output_ts])
# # 从合并的 .ts 文件提取音频并保存为 .mp3
# # os.system(f'ffmpeg -i "{output_ts}" -vn -c:a libmp3lame -q:a 2 "{mp3_filename}"')
# subprocess.run(['ffmpeg', '-i', output_ts, '-vn', '-c:a', 'libmp3lame', '-q:a', '2', mp3_filename])

async def run_ffmpeg_concat(ts_list_txt, output_ts):
    try:
        print(f"合并 .ts 文件到 {output_ts}")
        # 合并 .ts 文件为一个 .ts 文件
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', ts_list_txt, '-c', 'copy', output_ts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"合并失败: {stderr.decode().strip()}")
            return False
        print(f"合并成功: {stdout.decode().strip()}")
        return True
    except FileNotFoundError:
        print("错误: 找不到 ffmpeg，请确保已安装并在 PATH 中可用。")
        return False

async def run_ffmpeg_extract(output_ts, mp3_filename, ts_files_dir, download_m3u8_index, mp3name, m3u8_suffix):
    try:
        print(f"从 {output_ts} 提取音频到 {mp3_filename}")
        # 从合并的 .ts 文件提取音频并保存为 .mp3
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-i', output_ts, '-vn', '-c:a', 'libmp3lame', '-q:a', '2', mp3_filename,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"提取失败: {stderr.decode().strip()}")
            return False
        print(f"提取成功: {stdout.decode().strip()}")


        # 删除 无用缓存
        shutil.rmtree(ts_files_dir)

        # 成功目录记录下载的 m3u8
        with open(f'{download_m3u8_index}', 'a') as f:
            f.write(m3u8_url+ ' ' + mp3name+ '.' + m3u8_suffix + '\n')


        return True
    except FileNotFoundError:
        print("错误: 找不到 ffmpeg，请确保已安装并在 PATH 中可用。")
        return False

async def main(ts_list_txt, output_ts, mp3_filename, ts_files_dir, download_m3u8_index, mp3name, m3u8_suffix):
    # 运行合并和提取音频的任务
    success_concat = await run_ffmpeg_concat(ts_list_txt, output_ts)
    if success_concat:
        await run_ffmpeg_extract(output_ts, mp3_filename, ts_files_dir, download_m3u8_index, mp3name, m3u8_suffix)


asyncio.run(main(ts_list_txt, output_ts, mp3_filename, ts_files_dir, download_m3u8_index, mp3name, m3u8_suffix))


exit()




