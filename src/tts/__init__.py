"""语音合成模块"""
from .base_tts import BaseTTS
from .edge_tts_engine import EdgeTTSEngine
from .tts_manager import TTSManager

__all__ = ['BaseTTS', 'EdgeTTSEngine', 'TTSManager']
