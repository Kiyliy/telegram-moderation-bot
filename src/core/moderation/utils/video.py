import cv2
import tempfile
import aiohttp
import asyncio
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

class VideoProcessor:
    """视频处理工具"""
    
    @staticmethod
    async def download_video(url: str) -> str:
        """异步下载视频到临时文件"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download video: {response.status}")
                    
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                async for chunk in response.content.iter_chunked(8192):
                    temp.write(chunk)
                temp.close()
                return temp.name

    @staticmethod
    async def extract_frames(video_path: str, frame_interval: int = 30) -> List[str]:
        """异步提取视频帧"""
        def _extract_frames():
            frames = []
            temp_dir = tempfile.mkdtemp()
            
            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise ValueError("Failed to open video")
                    
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    if frame_count % frame_interval == 0:
                        frame_path = os.path.join(temp_dir, f"frame_{frame_count}.jpg")
                        cv2.imwrite(frame_path, frame)
                        frames.append(frame_path)
                        
                    frame_count += 1
                    
            finally:
                if 'cap' in locals():
                    cap.release()
                    
            return frames

        # 使用 ThreadPoolExecutor 执行 CPU 密集型操作
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, _extract_frames)

    @staticmethod
    async def process_video(url: str) -> List[str]:
        """处理视频并返回帧图片路径列表"""
        video_path = None
        try:
            # 下载视频
            video_path = await VideoProcessor.download_video(url)
            # 提取帧
            return await VideoProcessor.extract_frames(video_path)
        finally:
            # 清理视频临时文件
            if video_path and os.path.exists(video_path):
                try:
                    os.unlink(video_path)
                except Exception:
                    pass  # 忽略清理错误
