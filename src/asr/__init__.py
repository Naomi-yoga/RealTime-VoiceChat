"""语音识别模块"""
from .base_asr import BaseASR
from .whisper_asr import WhisperASR

__all__ = ['BaseASR', 'WhisperASR']
