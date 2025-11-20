"""Edge TTS引擎"""
import asyncio
import edge_tts
from typing import Optional, Iterator
from .base_tts import BaseTTS
from ..utils import get_logger

logger = get_logger("edge_tts")


class EdgeTTSEngine(BaseTTS):
    """Edge TTS引擎"""
    
    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        **kwargs
    ):
        """
        初始化Edge TTS
        
        Args:
            voice: 语音名称
            rate: 语速 (例如: "+0%", "+50%", "-20%")
            pitch: 音调 (例如: "+0Hz", "+50Hz", "-20Hz")
        """
        super().__init__(voice, **kwargs)
        self.rate = rate
        self.pitch = pitch
        logger.info(f"Edge TTS已初始化: voice={voice}")
    
    def synthesize(self, text: str) -> Optional[bytes]:
        """同步合成语音"""
        try:
            return asyncio.run(self._synthesize_async(text))
        except Exception as e:
            logger.error(f"Edge TTS合成错误: {e}")
            return None
    
    async def _synthesize_async(self, text: str) -> Optional[bytes]:
        """异步合成语音"""
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return audio_data
        except Exception as e:
            logger.error(f"Edge TTS异步合成错误: {e}")
            return None
    
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """合成语音并保存到文件"""
        try:
            asyncio.run(self._synthesize_to_file_async(text, output_path))
            return True
        except Exception as e:
            logger.error(f"Edge TTS保存文件错误: {e}")
            return False
    
    async def _synthesize_to_file_async(self, text: str, output_path: str):
        """异步合成并保存"""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        await communicate.save(output_path)
    
    def synthesize_stream(self, text: str) -> Iterator[bytes]:
        """
        流式合成语音
        
        Args:
            text: 文本内容
        
        Yields:
            音频数据块(bytes)
        """
        try:
            # 使用asyncio运行异步流式合成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for chunk in loop.run_until_complete(self._stream_async(text)):
                    yield chunk
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Edge TTS流式合成错误: {e}")
    
    async def _stream_async(self, text: str):
        """异步流式合成"""
        chunks = []
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            
            return chunks
        except Exception as e:
            logger.error(f"Edge TTS异步流式合成错误: {e}")
            return []
