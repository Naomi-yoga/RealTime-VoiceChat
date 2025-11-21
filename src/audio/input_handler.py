"""音频输入处理器"""
import queue
import threading
from typing import Optional, Callable
import numpy as np
from ..utils import get_logger

# 尝试导入 pyaudio
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pyaudio = None
    HAS_PYAUDIO = False

logger = get_logger("audio_input")


class AudioInputHandler:
    """音频输入处理器"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        device_index: Optional[int] = None,
        format: str = "int16"
    ):
        """
        初始化音频输入处理器
        
        Args:
            sample_rate: 采样率
            channels: 声道数
            chunk_size: 块大小
            device_index: 设备索引，None 为默认设备
            format: 音频格式
        """
        if not HAS_PYAUDIO:
            raise ImportError(
                "pyaudio 未安装。请运行: pip install pyaudio\n"
                "Windows 用户可能需要从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载预编译版本"
            )
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        
        # 音频格式映射
        self.format_map = {
            'int16': pyaudio.paInt16,
            'int32': pyaudio.paInt32,
            'float32': pyaudio.paFloat32,
        }
        self.format = self.format_map.get(format, pyaudio.paInt16)
        
        # PyAudio 实例
        self.pa = pyaudio.PyAudio()
        
        # 音频流
        self.stream: Optional[pyaudio.Stream] = None
        
        # 音频队列
        self.audio_queue = queue.Queue()
        
        # 录音线程
        self.is_recording = False
        self.record_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.callback: Optional[Callable] = None
        
        logger.info(
            f"音频输入处理器初始化: sample_rate={sample_rate}, "
            f"channels={channels}, chunk_size={chunk_size}"
        )
    
    def start(self, callback: Optional[Callable] = None):
        """
        开始录音
        
        Args:
            callback: 音频数据回调函数 callback(audio_chunk: bytes)
        """
        if self.is_recording:
            logger.warning("录音已经在进行中")
            return
        
        self.callback = callback
        
        try:
            # 打开音频流
            self.stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback if callback else None
            )
            
            self.is_recording = True
            
            if callback:
                # 使用回调模式
                logger.info("使用回调模式开始录音")
            else:
                # 使用队列模式（阻塞读取）
                self.record_thread = threading.Thread(target=self._record_loop)
                self.record_thread.daemon = True
                self.record_thread.start()
                logger.info("使用队列模式开始录音")
                
        except Exception as e:
            logger.error(f"启动录音失败: {e}")
            raise
    
    def stop(self):
        """停止录音"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.record_thread:
            self.record_thread.join(timeout=1.0)
            self.record_thread = None
        
        logger.info("录音已停止")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio 流回调"""
        if self.callback:
            self.callback(in_data)
        else:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _record_loop(self):
        """录音循环（非回调模式）"""
        while self.is_recording:
            try:
                if self.stream:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_queue.put(data)
            except Exception as e:
                logger.error(f"录音循环错误: {e}")
                break
    
    def read(self, timeout: float = None) -> Optional[bytes]:
        """
        从队列读取音频数据
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            音频数据
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_audio_level(self, audio_data: bytes) -> float:
        """
        获取音频电平
        
        Args:
            audio_data: 音频数据
        
        Returns:
            音频电平 (0.0 - 1.0)
        """
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        return np.abs(audio_np).mean() / 32768.0
    
    def list_devices(self) -> list:
        """
        列出所有音频输入设备
        
        Returns:
            设备信息列表
        """
        devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        return devices
    
    def __del__(self):
        """析构函数"""
        self.stop()
        if self.pa:
            self.pa.terminate()
