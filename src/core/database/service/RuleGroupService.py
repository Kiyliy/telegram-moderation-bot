from typing import Optional, List, Dict, Any
from src.core.database.models.db_rule_group import RuleGroup
from src.core.database.db.RuleGroupDatabase import RuleGroupDatabase
from src.core.database.service.chatsService import ChatService
from src.core.database.service.UserModerationService import UserModerationService
import time


class RuleGroupService:
    """规则组服务类"""
    
    def __init__(self):
        self.rule_group_db = RuleGroupDatabase()
        self.chat_service = ChatService()
        self.moderation_service = UserModerationService()
        
    async def create_rule_group(
        self,
        name: str,
        owner_id: int,
        description: str = None,
        settings: Dict = None
    ) -> Optional[RuleGroup]:
        """
        创建规则组
        
        Args:
            name: 规则组名称
            owner_id: 所有者ID
            description: 描述
            settings: 设置
            
        Returns:
            创建的规则组对象
        """
        # 创建规则组
        group_id = await self.rule_group_db.create_rule_group(
            name=name,
            owner_id=owner_id,
            description=description,
            settings=settings
        )
        
        if not group_id:
            return None
            
        # 返回创建的规则组
        return await self.rule_group_db.get_rule_group(group_id)
        
    async def update_rule_group(
        self,
        group_id: int,
        name: str = None,
        description: str = None,
        settings: Dict = None
    ) -> bool:
        """
        更新规则组
        
        Args:
            group_id: 规则组ID
            name: 新名称
            description: 新描述
            settings: 新设置
            
        Returns:
            是否更新成功
        """
        return await self.rule_group_db.update_rule_group(
            group_id=group_id,
            name=name,
            description=description,
            settings=settings
        )
        
    async def delete_rule_group(
        self,
        group_id: int
    ) -> bool:
        """
        删除规则组
        
        注意：删除前需要确保没有群组绑定到该规则组
        
        Args:
            group_id: 规则组ID
            
        Returns:
            是否删除成功
        """
        # 检查是否有群组绑定
        chats = await self.chat_service.get_chats_by_rule_group(group_id)
        if chats:
            return False
            
        # 删除规则组
        return await self.rule_group_db.delete_rule_group(group_id)
        
    async def get_rule_group(
        self,
        group_id: int
    ) -> Optional[RuleGroup]:
        """
        获取规则组信息
        
        Args:
            group_id: 规则组ID
            
        Returns:
            规则组对象
        """
        return await self.rule_group_db.get_rule_group(group_id)
        
    async def get_owner_rule_groups(
        self,
        owner_id: int
    ) -> List[RuleGroup]:
        """
        获取管理员的所有规则组
        
        Args:
            owner_id: 管理员ID
            
        Returns:
            规则组列表
        """
        return await self.rule_group_db.get_owner_rule_groups(owner_id)
        
    async def get_rule_group_settings(
        self,
        group_id: int
    ) -> Optional[Dict]:
        """
        获取规则组设置
        
        Args:
            group_id: 规则组ID
            
        Returns:
            设置字典
        """
        return await self.rule_group_db.get_rule_group_settings(group_id)
        
    async def update_rule_group_settings(
        self,
        group_id: int,
        settings: Dict
    ) -> bool:
        """
        更新规则组设置
        
        Args:
            group_id: 规则组ID
            settings: 新设置
            
        Returns:
            是否更新成功
        """
        return await self.rule_group_db.update_rule_group(
            group_id=group_id,
            settings=settings
        )
        
    async def get_rule_group_stats(
        self,
        group_id: int
    ) -> Dict[str, Any]:
        """
        获取规则组统计信息
        
        Args:
            group_id: 规则组ID
            
        Returns:
            统计信息字典，包含：
            - chat_count: 群组数量
            - violation_stats: 违规统计
            - banned_users: 封禁用户数
        """
        # 获取群组数量
        chats = await self.chat_service.get_chats_by_rule_group(group_id)
        chat_count = len(chats)
        
        # 获取违规统计
        violation_stats = await self.moderation_service.get_violation_stats(rule_group_id=group_id)
        
        # 获取封禁用户数
        banned_users = await self.moderation_service.get_banned_users(rule_group_id=group_id)
        
        return {
            'chat_count': chat_count,
            'violation_stats': violation_stats,
            'banned_users_count': len(banned_users)
        }
        
    async def bind_chat(
        self,
        chat_id: int,
        rule_group_id: int
    ) -> bool:
        """
        将群组绑定到规则组
        
        Args:
            chat_id: 群组ID
            rule_group_id: 规则组ID
            
        Returns:
            是否绑定成功
        """
        return await self.chat_service.bind_chat_to_rule_group(
            chat_id=chat_id,
            rule_group_id=rule_group_id
        )
        
    async def unbind_chat(
        self,
        chat_id: int
    ) -> bool:
        """
        解绑群组
        
        Args:
            chat_id: 群组ID
            
        Returns:
            是否解绑成功
        """
        return await self.chat_service.unbind_chat_from_rule_group(chat_id)
        
    async def get_default_settings(self) -> Dict:
        """获取默认设置"""
        return {
            "warning": {
                "max_warnings": 3,
                "reset_after_days": 30
            },
            "punishment": {
                "mute_durations": [300, 3600, 86400],
                "ban_threshold": 5
            },
            "moderation": {
                "rules": {
                    "nsfw": True,
                    "spam": True,
                    "violence": False
                },
                "sensitivity": {
                    "nsfw": 0.8,
                    "spam": 0.7,
                    "violence": 0.9
                }
            }
        } 