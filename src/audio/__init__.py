"""音频处理模块"""
from .vad_detector import VADDetector

# 可选导入音频处理器（需要 pyaudio）
try:
    from .input_handler import AudioInputHandler
    from .output_handler import AudioOutputHandler
    __all__ = ['VADDetector', 'AudioInputHandler', 'AudioOutputHandler']
except ImportError:
    AudioInputHandler = None
    AudioOutputHandler = None
    __all__ = ['VADDetector']
