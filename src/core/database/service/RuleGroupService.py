from typing import Optional, List, Dict, Any
from src.core.database.models.db_rule_group import RuleGroup
from src.core.database.db.RuleGroupDatabase import RuleGroupDatabase
from src.core.database.service.chatsService import ChatService
from src.core.database.service.UserModerationService import UserModerationService
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
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
        # 如果没有提供设置，使用默认设置
        if settings is None:
            settings = await self.get_default_settings()
            
        # 创建规则组
        rule_id = await self.rule_group_db.create_rule_group(
            name=name,
            owner_id=owner_id,
            description=description,
            settings=settings
        )
        
        if not rule_id:
            return None
            
        # 返回创建的规则组
        return await self.rule_group_db.get_rule_group(rule_id)
        
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
        # 如果要更新设置，先获取当前设置
        if settings is not None:
            current_settings = await self.get_rule_group_settings(group_id)
            if current_settings:
                # 合并设置
                settings = {**current_settings, **settings}
        
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
        
        Args:
            group_id: 规则组ID
            
        Returns:
            是否删除成功
        """
        # 检查是否有群组绑定到此规则组
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
        # 获取当前设置
        current_settings = await self.get_rule_group_settings(group_id)
        if current_settings:
            # 合并设置
            settings = {**current_settings, **settings}
            
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
            统计信息字典
        """
        stats = {
            "total_chats": 0,
            "total_violations": 0,
            "violations_by_type": {},
            "total_users": 0,
            "muted_users": 0,
            "banned_users": 0
        }
        
        # 获取规则组内的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(group_id)
        stats["total_chats"] = len(chats)
        
        # 统计每个群组的信息
        for chat in chats:
            # 获取违规统计
            violations = await self.moderation_service.get_violation_stats(
                chat_id=chat.chat_id
            )
            for vtype, vstats in violations.items():
                if vtype not in stats["violations_by_type"]:
                    stats["violations_by_type"][vtype] = {
                        "count": 0,
                        "user_count": 0
                    }
                stats["violations_by_type"][vtype]["count"] += vstats["count"]
                stats["violations_by_type"][vtype]["user_count"] += vstats["user_count"]
                stats["total_violations"] += vstats["count"]
                stats["total_users"] += vstats["user_count"]
            
            # 获取禁言和封禁用户数
            muted = await self.moderation_service.get_muted_users(chat.chat_id)
            banned = await self.moderation_service.get_banned_users(chat.chat_id)
            stats["muted_users"] += len(muted)
            stats["banned_users"] += len(banned)
            
        return stats
        
    async def bind_chat(
        self,
        chat_id: int,
        rule_group_id: int
    ) -> bool:
        """
        绑定群组到规则组
        
        Args:
            chat_id: 群组ID
            rule_group_id: 规则组ID
            
        Returns:
            是否绑定成功
        """
        result = await self.chat_service.bind_chat_to_rule_group(
            chat_id=chat_id,
            rule_group_id=rule_group_id
        )
        return result["success"]
        
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
        result = await self.chat_service.unbind_chat_from_rule_group(chat_id)
        return result["success"] 