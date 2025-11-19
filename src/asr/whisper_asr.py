"""Whisper ASR实现"""
import io
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from .base_asr import BaseASR
from ..utils import get_logger

logger = get_logger("whisper")


class WhisperASR(BaseASR):
    """Whisper语音识别"""
    
    def __init__(
        self,
        model: str = "base",
        language: str = "zh",
        device: str = "cpu",
        compute_type: str = "int8",
        **kwargs
    ):
        """
        初始化Whisper ASR
        
        Args:
            model: 模型大小 (tiny, base, small, medium, large)
            language: 识别语言
            device: 设备 (cpu, cuda)
            compute_type: 计算类型 (int8, float16, float32)
        """
        super().__init__(language, **kwargs)
        
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        
        # 加载模型
        logger.info(f"正在加载Whisper模型: {model}")
        self.model = WhisperModel(
            model,
            device=device,
            compute_type=compute_type
        )
        logger.info("Whisper模型加载完成")
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """转录音频"""
        try:
            # 将bytes转换为numpy数组
            # 假设音频是16bit PCM
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_np.astype(np.float32) / 32768.0
            
            # 转录
            segments, info = self.model.transcribe(
                audio_float,
                language=self.language if self.language != "auto" else None,
                beam_size=5
            )
            
            # 合并所有段落
            text = " ".join([segment.text for segment in segments])
            
            logger.debug(f"识别结果: {text}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Whisper转录错误: {e}")
            return None
