"""TTS基类"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseTTS(ABC):
    """TTS基类"""
    
    def __init__(self, voice: str, **kwargs):
        """
        初始化TTS
        
        Args:
            voice: 语音名称
            **kwargs: 其他参数
        """
        self.voice = voice
        self.kwargs = kwargs
    
    @abstractmethod
    def synthesize(self, text: str) -> Optional[bytes]:
        """
        合成语音
        
        Args:
            text: 文本内容
        
        Returns:
            音频数据(bytes)
        """
        pass
    
    @abstractmethod
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        合成语音并保存到文件
        
        Args:
            text: 文本内容
            output_path: 输出文件路径
        
        Returns:
            是否成功
        """
        pass
