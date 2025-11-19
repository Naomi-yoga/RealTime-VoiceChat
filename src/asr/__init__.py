"""语音识别模块"""
from .base_asr import BaseASR
from .asr_manager import ASRManager

# 可选导入具体实现
try:
    from .whisper_asr import WhisperASR
except ImportError:
    WhisperASR = None

__all__ = ['BaseASR', 'ASRManager', 'WhisperASR']
