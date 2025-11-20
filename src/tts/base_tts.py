"""TTS基类"""
from abc import ABC, abstractmethod
from typing import Optional, Iterator, AsyncIterator


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
        合成语音（一次性返回完整音频）
        
        Args:
            text: 文本内容
        
        Returns:
            音频数据(bytes)
        """
        pass
    
    def synthesize_stream(self, text: str) -> Iterator[bytes]:
        """
        流式合成语音（生成器，逐块返回音频数据）
        
        Args:
            text: 文本内容
        
        Yields:
            音频数据块(bytes)
        """
        # 默认实现：将完整音频一次返回
        audio = self.synthesize(text)
        if audio:
            yield audio
    
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
