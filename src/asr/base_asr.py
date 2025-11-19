"""ASR基类"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseASR(ABC):
    """ASR基类"""
    
    def __init__(self, language: str = "zh", **kwargs):
        """
        初始化ASR
        
        Args:
            language: 识别语言
            **kwargs: 其他参数
        """
        self.language = language
        self.kwargs = kwargs
    
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        转录音频
        
        Args:
            audio_data: 音频数据
        
        Returns:
            识别文本
        """
        pass
