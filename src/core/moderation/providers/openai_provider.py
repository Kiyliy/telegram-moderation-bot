# src/core/moderation/providers/openai_provider.py

from typing import List, Union, Dict
import aiohttp
from src.core.moderation.base import BaseProvider
from src.core.moderation.models import ModerationInput, ModerationResult, ContentType, ModerationCategory, ModerationResponse
from src.core.moderation.utils.video import VideoProcessor
from src.core.moderation.providers.base import IModerationProvider

class OpenAIModerationProvider(IModerationProvider):
    """OpenAI审核服务提供者"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", model: str = "omni-moderation-latest"):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.base_url = f"{self.api_base}/moderations"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def _process_video(self, url: str) -> List[ModerationInput]:
        """处理视频内容"""
        frame_paths = await VideoProcessor.process_video(url)
        return [
            ModerationInput(
                type=ContentType.IMAGE,
                content=frame_path
            ) for frame_path in frame_paths
        ]

    async def _check_single(self, input_data: ModerationInput) -> Dict:
        """检查单个内容"""
        payload = {
            "model": self.model,
            "input": []
        }

        if input_data.type == ContentType.TEXT:
            payload["input"].append({
                "type": "text",
                "text": input_data.content
            })
        elif input_data.type == ContentType.IMAGE:
            if isinstance(input_data.content, list):
                for url in input_data.content:
                    payload["input"].append({
                        "type": "image_url",
                        "image_url": {"url": url}
                    })
            else:
                payload["input"].append({
                    "type": "image_url",
                    "image_url": {"url": input_data.content}
                })

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return await response.json()

    async def check_content(
        self, 
        content: Union[ModerationInput, List[ModerationInput]]
    ) -> ModerationResult:
        """审核内容"""
        if isinstance(content, ModerationInput):
            content = [content]

        results = []
        for input_data in content:
            if input_data.type == ContentType.VIDEO:
                # 处理视频
                video_frames = await self._process_video(input_data.content)
                for frame in video_frames:
                    result = await self._check_single(frame)
                    results.append(result)
            else:
                # 处理文本或图片
                result = await self._check_single(input_data)
                results.append(result)

        # 合并结果
        final_result = self._merge_results(results, content[0])
        return final_result

    def _merge_results(self, results: List[Dict], input_data: ModerationInput) -> ModerationResult:
        """合并多个结果"""
        
        categories = {}
        flagged = False

        # 遍历所有结果,取最高分
        for result in results:
            for category, score in result["results"][0]["category_scores"].items():
                if category not in categories:
                    categories[category] = ModerationCategory(
                        flagged=False,
                        score=0.0
                    )
                categories[category].score = max(
                    categories[category].score,
                    score
                )
                if score > 0.5:  # 可配置的阈值
                    categories[category].flagged = True
                    flagged = True

        return ModerationResult(
            flagged=flagged,
            categories=categories,
            provider=self.provider_name,
            raw_response=results,
            input_type=input_data.type,
            input_content=input_data.content
        )

class OpenAIProvider(BaseProvider):
    async def check_contents(
        self, 
        inputs: List[ModerationInput]
    ) -> ModerationResponse:
        # OpenAI 只支持文本,所以我们需要过滤
        text_inputs = [
            input.content for input in inputs 
            if input.type == "text"
        ]
        
        if not text_inputs:
            return ModerationResponse(
                id="no-text-content",
                results=[],
                raw_response={}
            )
            
        response = await self.client.moderations.create(
            input=text_inputs
        )
        
        return ModerationResponse(
            id=response.id,
            results=[
                ModerationResult(
                    flagged=result.flagged,
                    categories=result.categories,
                    category_scores=result.category_scores,
                    content=text_inputs[i],
                    content_type="text"
                )
                for i, result in enumerate(response.results)
            ],
            raw_response=response.model_dump()
        )