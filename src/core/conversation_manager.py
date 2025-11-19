"""对话管理器"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from ..utils import get_logger

logger = get_logger("conversation")


class ConversationManager:
    """对话管理器，负责维护对话历史和上下文"""
    
    def __init__(
        self,
        system_prompt: str = "你是一个友好、专业的AI助手。",
        max_history: int = 10,
        save_history: bool = True,
        history_file: str = "conversation_history.json"
    ):
        """
        初始化对话管理器
        
        Args:
            system_prompt: 系统提示词
            max_history: 最大保留对话轮数
            save_history: 是否保存对话历史
            history_file: 历史文件路径
        """
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.save_history = save_history
        self.history_file = Path(history_file)
        
        # 对话历史 [{"role": "user/assistant/system", "content": "..."}]
        self.messages: List[Dict[str, str]] = []
        
        # 添加系统提示词
        if system_prompt:
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 尝试加载历史对话
        if save_history and self.history_file.exists():
            self._load_history()
        
        logger.info("对话管理器已初始化")
    
    def add_user_message(self, content: str):
        """
        添加用户消息
        
        Args:
            content: 用户消息内容
        """
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
        logger.debug(f"添加用户消息: {content[:50]}...")
    
    def add_assistant_message(self, content: str):
        """
        添加助手回复
        
        Args:
            content: 助手回复内容
        """
        self.messages.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
        logger.debug(f"添加助手回复: {content[:50]}...")
        
        # 自动保存
        if self.save_history:
            self._save_history()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        获取对话消息列表（用于API调用）
        
        Returns:
            消息列表
        """
        # 只返回 role 和 content 字段（去除 timestamp）
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]
    
    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """
        获取最后n条消息
        
        Args:
            n: 消息数量
        
        Returns:
            消息列表
        """
        return self.messages[-n:] if n > 0 else []
    
    def clear_history(self, keep_system_prompt: bool = True):
        """
        清空对话历史
        
        Args:
            keep_system_prompt: 是否保留系统提示词
        """
        if keep_system_prompt and self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []
        
        logger.info("对话历史已清空")
        
        if self.save_history:
            self._save_history()
    
    def _trim_history(self):
        """修剪对话历史，保持在最大长度内"""
        # 保留系统提示词
        system_msg = None
        if self.messages and self.messages[0]["role"] == "system":
            system_msg = self.messages[0]
            messages = self.messages[1:]
        else:
            messages = self.messages
        
        # 如果超过最大历史，删除最早的对话
        if len(messages) > self.max_history * 2:  # 每轮对话2条消息
            messages = messages[-(self.max_history * 2):]
        
        # 重新组合
        if system_msg:
            self.messages = [system_msg] + messages
        else:
            self.messages = messages
    
    def _save_history(self):
        """保存对话历史到文件"""
        try:
            # 创建目录
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "system_prompt": self.system_prompt,
                    "messages": self.messages,
                    "saved_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"对话历史已保存: {self.history_file}")
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")
    
    def _load_history(self):
        """从文件加载对话历史"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复对话历史
            if "messages" in data:
                self.messages = data["messages"]
                logger.info(f"已加载对话历史: {len(self.messages)} 条消息")
            
        except Exception as e:
            logger.warning(f"加载对话历史失败: {e}")
    
    def update_system_prompt(self, prompt: str):
        """
        更新系统提示词
        
        Args:
            prompt: 新的系统提示词
        """
        self.system_prompt = prompt
        
        # 更新或添加系统消息
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = prompt
        else:
            self.messages.insert(0, {
                "role": "system",
                "content": prompt
            })
        
        logger.info("系统提示词已更新")
    
    def get_conversation_summary(self) -> str:
        """
        获取对话摘要
        
        Returns:
            对话摘要文本
        """
        # 统计消息数量
        user_count = sum(1 for msg in self.messages if msg["role"] == "user")
        assistant_count = sum(1 for msg in self.messages if msg["role"] == "assistant")
        
        return f"对话轮数: {min(user_count, assistant_count)}, " \
               f"用户消息: {user_count}, 助手回复: {assistant_count}"
    
    def __repr__(self) -> str:
        return f"ConversationManager(messages={len(self.messages)}, max_history={self.max_history})"
