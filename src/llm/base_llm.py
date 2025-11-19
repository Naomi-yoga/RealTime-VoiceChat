"""LLM基类"""
from abc import ABC, abstractmethod
from typing import Generator, List, Dict


class BaseLLM(ABC):
    """LLM基类"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化LLM
        
        Args:
            api_key: API密钥
            model: 模型名称
            **kwargs: 其他参数
        """
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> Generator[str, None, None]:
        """
        生成响应
        
        Args:
            messages: 对话消息列表
            stream: 是否流式输出
        
        Yields:
            响应文本片段
        """
        pass
    
    @abstractmethod
    def check_connection(self) -> bool:
        """
        检查连接
        
        Returns:
            是否连接成功
        """
        pass
