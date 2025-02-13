from io import BytesIO
import base64
import aiohttp
import asyncio
import os
import requests
from PIL import Image
from telegram import constants, Update
from telegram.ext import ContextTypes
from typing import Set, TypeVar, Coroutine, Any
from datetime import datetime


T = TypeVar("T")


def print_current_time(label=""):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if label:
        print(f"{label}: {current_time}")
    else:
        print(f"Current time: {current_time}")


async def base64_img_url(imgurl, max_retries=3):
    """通过imgurl异步获取图片数据,并转换为base64编码的字符串,失败时最多重试3次"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    retries = 0
    while retries < max_retries:
        try:
            # 使用aiohttp进行异步HTTP请求
            async with aiohttp.ClientSession() as session:
                async with session.get(imgurl, headers=headers, timeout=15) as response:
                    # 确保HTTP请求成功
                    if response.status == 200:
                        # 读取响应内容(图片数据),并转换为base64编码的字符串
                        photo_data = await response.read()
                        base64_string = bits_to_base64(BytesIO(photo_data))
                        return base64_string
                    else:
                        # 请求失败,增加重试次数
                        retries += 1
        except Exception as err:
            # 发生异常,增加重试次数
            retries += 1
            # 达到最大重试次数后仍然失败,抛出异常
            if retries >= max_retries:
                raise err


def base64_to_bits(base64_string):
    """
    Convert a base64 string to a binary data stream.
    """
    image_data = base64.b64decode(base64_string)
    image_stream = BytesIO(image_data)
    image_stream.seek(0)  # 将文件指针重置到开头

    return image_stream


# bits to base64
def bits_to_base64(image_stream):
    """
    Convert a binary data stream to a base64 string.
    """
    image_data = image_stream.getvalue()
    base64_string = base64.b64encode(image_data).decode("utf-8")
    return base64_string


async def get_photo_data(imgurl, max_retries=3):
    """
    通过imgurl异步获取图片数据，失败时最多重试3次
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    retries = 0
    while retries < max_retries:
        try:
            # 使用aiohttp进行异步HTTP请求
            async with aiohttp.ClientSession() as session:
                async with session.get(imgurl, headers=headers, timeout=15) as response:
                    # 确保HTTP请求成功
                    if response.status == 200:
                        # 读取响应内容（图片数据），并返回一个BytesIO对象
                        photo_data = BytesIO(await response.read())
                        return photo_data
                    else:
                        # 请求失败，增加重试次数
                        retries += 1
        except Exception as err:
            # 发生异常，增加重试次数
            retries += 1

            # 达到最大重试次数后仍然失败，抛出异常
            if retries >= max_retries:
                raise err


# 下载图片到本地路径
async def download_photo(imgurl, save_path, max_retries=3):
    """
    通过imgurl异步下载图片到本地路径，失败时最多重试3次
    """
    save_path = save_path
    retries = 0
    err = None
    while retries < max_retries:
        try:
            # 获取图片数据
            photo_data = await get_photo_data(imgurl)
            # 将图片数据写入本地文件
            with open(save_path, "wb") as file:
                file.write(photo_data.getvalue())
            return
        except Exception as err:
            # 发生异常，增加重试次数
            err = err
            retries += 1
    # 达到最大重试次数后仍然失败，抛出异常
    if retries >= max_retries:
        raise err


async def get_tg_photo_data(update: Update, context: ContextTypes.DEFAULT_TYPE, max_retries=3):
    """
    从Telegram消息中获取图片数据，失败时最多重试3次
    """
    # 如果消息中包含图片
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id

        retries = 0
        while retries < max_retries:
            try:
                photo = await context.bot.get_file(photo_id)
                photo_url = photo.file_path

                # 下载图片
                response = requests.get(photo_url)
                if response.status_code == 200:
                    image_bytes = BytesIO(response.content)
                    image = Image.open(image_bytes)
                    return image
                else:
                    # 请求失败，增加重试次数
                    retries += 1
            except requests.exceptions.RequestException:
                # 发生异常，增加重试次数
                retries += 1

        # 达到最大重试次数后仍然失败，返回None
        return None
    else:
        # 消息中不包含图片，返回None
        return None

