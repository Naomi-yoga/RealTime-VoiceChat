"""音频工具函数"""
import numpy as np
from collections import deque
from typing import Optional


def calculate_rms(audio_data: np.ndarray) -> float:
    """
    计算音频数据的RMS（均方根）值，用于音量检测
    
    Args:
        audio_data: 音频数据数组
    
    Returns:
        RMS值
    """
    if len(audio_data) == 0:
        return 0.0
    return np.sqrt(np.mean(audio_data.astype(float) ** 2))


def normalize_audio(audio_data: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """
    归一化音频数据
    
    Args:
        audio_data: 音频数据
        target_rms: 目标RMS值
    
    Returns:
        归一化后的音频数据
    """
    current_rms = calculate_rms(audio_data)
    if current_rms == 0:
        return audio_data
    
    scaling_factor = target_rms / current_rms
    normalized = audio_data * scaling_factor
    
    # 防止削波
    max_val = np.abs(normalized).max()
    if max_val > 1.0:
        normalized = normalized / max_val
    
    return normalized


class AudioBuffer:
    """音频缓冲区"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化音频缓冲区
        
        Args:
            max_size: 最大缓冲帧数
        """
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size
    
    def add(self, data: np.ndarray):
        """添加音频数据到缓冲区"""
        self.buffer.append(data)
    
    def get_all(self) -> Optional[np.ndarray]:
        """获取所有缓冲数据并清空"""
        if not self.buffer:
            return None
        
        data = np.concatenate(list(self.buffer))
        self.buffer.clear()
        return data
    
    def get_last_n_frames(self, n: int) -> Optional[np.ndarray]:
        """获取最后n帧数据"""
        if not self.buffer:
            return None
        
        frames = list(self.buffer)[-n:]
        if not frames:
            return None
        
        return np.concatenate(frames)
    
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
    
    def __len__(self):
        """返回缓冲区中的帧数"""
        return len(self.buffer)
    
    @property
    def is_empty(self) -> bool:
        """检查缓冲区是否为空"""
        return len(self.buffer) == 0


def convert_audio_format(
    audio_data: np.ndarray,
    from_dtype: str,
    to_dtype: str
) -> np.ndarray:
    """
    转换音频数据格式
    
    Args:
        audio_data: 音频数据
        from_dtype: 源数据类型
        to_dtype: 目标数据类型
    
    Returns:
        转换后的音频数据
    """
    dtype_map = {
        'int16': (np.int16, 32768.0),
        'int32': (np.int32, 2147483648.0),
        'float32': (np.float32, 1.0),
        'float64': (np.float64, 1.0),
    }
    
    if from_dtype not in dtype_map or to_dtype not in dtype_map:
        raise ValueError(f"Unsupported dtype: {from_dtype} or {to_dtype}")
    
    from_type, from_scale = dtype_map[from_dtype]
    to_type, to_scale = dtype_map[to_dtype]
    
    # 转换到 float
    if from_dtype.startswith('int'):
        audio_float = audio_data.astype(np.float64) / from_scale
    else:
        audio_float = audio_data.astype(np.float64)
    
    # 转换到目标类型
    if to_dtype.startswith('int'):
        converted = (audio_float * to_scale).astype(to_type)
    else:
        converted = audio_float.astype(to_type)
    
    return converted
