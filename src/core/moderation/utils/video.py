import cv2
import tempfile
import requests
from typing import List
import os

class VideoProcessor:
    """视频处理工具"""
    
    @staticmethod
    async def download_video(url: str) -> str:
        """下载视频到临时文件"""
        resp = requests.get(url, stream=True)
        if resp.status_code != 200:
            raise ValueError(f"Failed to download video: {resp.status_code}")
            
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                temp.write(chunk)
        temp.close()
        return temp.name

    @staticmethod
    async def extract_frames(video_path: str, frame_interval: int = 30) -> List[str]:
        """提取视频帧"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video")

        frames = []
        frame_count = 0
        temp_dir = tempfile.mkdtemp()

        try:
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
            cap.release()
            
        return frames

    @staticmethod
    async def process_video(url: str) -> List[str]:
        """处理视频并返回帧图片路径列表"""
        try:
            video_path = await VideoProcessor.download_video(url)
            frames = await VideoProcessor.extract_frames(video_path)
            return frames
        finally:
            # 清理临时文件
            if 'video_path' in locals():
                os.unlink(video_path)
