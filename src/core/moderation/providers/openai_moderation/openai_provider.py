# src/core/moderation/providers/openai_provider.py

from typing import List, Union, Dict, Optional
import aiohttp
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ModerationResult, ContentType, ModerationCategory
from src.core.moderation.utils.video import VideoProcessor
from src.core.moderation.providers.base import IModerationProvider
from src.core.tools.base64tools import base64_img_url, bits_to_base64
from src.core.tools.task_keeper import TaskKeeper
import cv2
import asyncio
import os
from io import BytesIO
from src.core.moderation.providers.openai_moderation.OpenaiCategoryTypes import OpenAISettingsType
from src.core.moderation.config import ModerationConfig

class OpenAIModerationProvider(IModerationProvider):
    """OpenAI审核服务提供者"""
    
    def __init__(self):
        self.api_key = ModerationConfig.OPENAI_API_KEY
        self.model = ModerationConfig.OPENAI_MODERATION_MODEL
        self.api_base = ModerationConfig.OPENAI_API_BASE
        self.base_url = f"{self.api_base}/moderations"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def _make_request(self, inputs: List[Dict], max_retries: int = 3) -> Dict:
        """发送请求到OpenAI API"""
        last_error = None
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        json={"model": self.model, "input": inputs},
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise ValueError(f"OpenAI API error: {error_text}")
                        return await response.json()
            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    raise ValueError(f"Moderation failed after {max_retries} attempts: {str(last_error)}")
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避

    async def _prepare_input(self, input_data: ModerationInputContent) -> List[Dict]:
        """准备API输入数据"""
        api_inputs = []
        
        # 处理文本输入
        if input_data.text is not None:
            api_inputs.append({
                "type": "text",
                "text": input_data.text
            })
            
        # 处理图片输入
        if input_data.image_urls is not None:
            for image_url in input_data.image_urls:
                url = str(image_url)  # 转换 HttpUrl 为字符串
                base64_image = None
                
            if os.path.exists(url):  # 如果是本地文件路径
                try:
                    with open(url, 'rb') as img_file:
                        base64_image = bits_to_base64(BytesIO(img_file.read()))
                except Exception as e:
                    print(f"Error reading local file {url}: {str(e)}")
            else:  # 假设是URL
                try:
                    base64_image = await base64_img_url(url)
                except Exception as e:
                    print(f"Error fetching URL {url}: {str(e)}")

            if base64_image:
                api_inputs.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            
        return api_inputs

    def _process_api_response(self, 
                              response: Dict, 
                              input_data: ModerationInputContent, 
                              settings: Optional[OpenAISettingsType] = None
                            ) -> ModerationResult:
        """处理API响应"""
        # 合并所有结果
        flagged = False
        categories = {}  # { ["str": bool]}
        category_scores = {}  # { ["str": float]}
        
        # 对于每个结果
        for result in response["results"]:
            # 处理每个类别
            for category, score in result["category_scores"].items():
                # 如果设置了审核类别, 则只处理设置的类别
                if settings:
                    if not settings["categories"].get(category, False):
                        continue
                    # 记录类别, 更新分数为所有类别的最大值
                    if category not in category_scores or score > category_scores[category]:
                        category_scores[category] = score
                        categories[category] = result["categories"][category]
                        if score > settings["sensitivity"].get(category, 0.8):
                            flagged = True
                # 如果没有设置审核类别
                else:
                    # 记录类别, 更新分数为所有类别的最大值
                    if category not in category_scores or score > category_scores[category]:
                        category_scores[category] = score
                        categories[category] = result["categories"][category]
                        flagged = flagged or result['flagged']

        return ModerationResult(
            flagged=flagged,
            provider=self.provider_name,
            raw_response=response,
            categories=categories,
            category_scores=category_scores
        )


    async def check_content(
        self, 
        content: ModerationInputContent,
        settings: Optional[OpenAISettingsType] = None 
    ) -> ModerationResult:
        """审核内容"""
        temp_files = []  # 跟踪临时文件
        try:
            if isinstance(content, list):
                content = content[0]
                
            if content.type == ContentType.VIDEO:
                # 处理视频
                frame_paths = await VideoProcessor.process_video(content.video)
                temp_files.extend(frame_paths)  # 记录临时文件
                
                # 创建所有帧的处理任务
                async def process_single_frame(frame_path: str):
                    frame_input = ModerationInputContent(
                        type=ContentType.IMAGE_URL,
                        image_urls=[frame_path]
                    )
                    api_inputs = await self._prepare_input(frame_input)
                    if api_inputs:  # 确保有有效的输入
                        return await self._make_request(api_inputs)
                    return None
                
                # 创建并管理任务
                tasks = [
                    TaskKeeper.create_task(process_single_frame(frame_path))
                    for frame_path in frame_paths
                ]
                
                # 等待所有任务完成
                all_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 过滤出成功的结果
                valid_results = [
                    result for result in all_results 
                    if result is not None and not isinstance(result, Exception)
                ]
                
                # 合并所有帧的结果
                if valid_results:
                    # 合并所有响应为一个
                    merged_response = {
                        "results": []
                    }
                    for result in valid_results:
                        merged_response["results"].extend(result["results"])
                    
                    return self._process_api_response(merged_response, content, settings)
                else:
                    raise ValueError("No valid frames could be processed")
            else:
                # 处理普通内容（文本或单张图片）
                api_inputs = await self._prepare_input(content)
                if not api_inputs:
                    raise ValueError("No valid input could be prepared")
                response = await self._make_request(api_inputs)
                
                return self._process_api_response(response, content, settings)
            
        except Exception as e:
            raise ValueError(f"Moderation failed: {str(e)}")
        finally:
            # 清理临时文件
            for path in temp_files:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass  # 忽略清理错误

