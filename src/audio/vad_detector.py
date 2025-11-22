"""语音活动检测(VAD)模块"""
import numpy as np
from typing import Optional
from ..utils import get_logger, calculate_rms

# 尝试导入 webrtcvad，如果不可用则设为 None
try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    webrtcvad = None
    HAS_WEBRTCVAD = False

logger = get_logger("vad")


class VADDetector:
    """语音活动检测器"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        aggressiveness: int = 3,
        frame_duration_ms: int = 30,
        padding_duration_ms: int = 300,
        silence_duration_ms: int = 700
    ):
        """
        初始化VAD检测器
        
        Args:
            sample_rate: 采样率 (8000, 16000, 32000, 48000)
            aggressiveness: 激进程度 (0-3)，越高越激进
            frame_duration_ms: 帧长度(毫秒) (10, 20, 30)
            padding_duration_ms: 语音前后填充时长(毫秒)
            silence_duration_ms: 认定为静音的时长(毫秒)
        """
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.silence_duration_ms = silence_duration_ms
        
        # 初始化 WebRTC VAD
        if not HAS_WEBRTCVAD:
            logger.warning("webrtcvad 未安装，VAD 功能将受限。请安装: pip install webrtcvad")
            self.vad = None
        else:
            self.vad = webrtcvad.Vad(aggressiveness)
        
        # 计算帧大小（样本数）
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # 状态变量
        self.is_speech = False
        self.triggered = False
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.num_silence_frames = int(silence_duration_ms / frame_duration_ms)
        self.ring_buffer = []
        self.silence_counter = 0
        
        logger.info(f"VAD检测器已初始化: aggressiveness={aggressiveness}, "
                   f"frame_duration={frame_duration_ms}ms")
    
    def process_frame(self, frame: bytes) -> tuple[bool, Optional[bytes]]:
        """
        处理单帧音频
        
        Args:
            frame: 音频帧数据（bytes格式）
        
        Returns:
            (is_speech, audio_data): 是否检测到语音，以及完整语音数据（如果有）
        """
        # 确保帧长度正确
        expected_size = self.frame_size * 2  # int16 = 2 bytes
        if len(frame) != expected_size:
            # 只在第一次不匹配时记录警告，避免日志过多
            if not hasattr(self, '_size_warning_logged'):
                logger.warning(f"VAD帧大小不匹配: 期望={expected_size}字节, 实际={len(frame)}字节, "
                           f"frame_size={self.frame_size}, sample_rate={self.sample_rate}")
                self._size_warning_logged = True
            return self.is_speech, None
        
        # VAD检测
        try:
            is_speech = self.vad.is_speech(frame, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD检测错误: {e}")
            return self.is_speech, None
        
        # 状态机逻辑
        if not self.triggered:
            # 未触发状态：等待语音开始
            self.ring_buffer.append((frame, is_speech))
            if len(self.ring_buffer) > self.num_padding_frames:
                self.ring_buffer.pop(0)
            
            # 检查是否有足够的语音帧来触发
            num_voiced = sum(1 for _, speech in self.ring_buffer if speech)
            if num_voiced > 0.5 * len(self.ring_buffer):
                self.triggered = True
                self.is_speech = True
                self.silence_counter = 0
                logger.debug("检测到语音开始")
        else:
            # 已触发状态：等待语音结束
            self.ring_buffer.append((frame, is_speech))
            
            if is_speech:
                self.silence_counter = 0
            else:
                self.silence_counter += 1
            
            # 如果静音帧数超过阈值，认为语音结束
            if self.silence_counter >= self.num_silence_frames:
                self.triggered = False
                self.is_speech = False
                logger.debug("检测到语音结束")
                
                # 返回完整语音数据
                audio_data = b''.join(f for f, _ in self.ring_buffer)
                self.ring_buffer = []
                return False, audio_data
        
        return self.is_speech, None
    
    def reset(self):
        """重置VAD状态"""
        self.is_speech = False
        self.triggered = False
        self.ring_buffer = []
        self.silence_counter = 0
        logger.debug("VAD状态已重置")
    
    @staticmethod
    def simple_vad(audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        简单的基于能量的VAD
        
        Args:
            audio_data: 音频数据
            threshold: 能量阈值
        
        Returns:
            是否包含语音
        """
        rms = calculate_rms(audio_data)
        return rms > threshold
