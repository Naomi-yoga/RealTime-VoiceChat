"""音频输出处理器"""
import queue
import threading
from typing import Optional
from ..utils import get_logger

# 尝试导入 pyaudio
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pyaudio = None
    HAS_PYAUDIO = False

logger = get_logger("audio_output")


class AudioOutputHandler:
    """音频输出处理器"""
    
    def __init__(
        self,
        sample_rate: int = 24000,
        channels: int = 1,
        device_index: Optional[int] = None,
        format: str = "int16"
    ):
        """
        初始化音频输出处理器
        
        Args:
            sample_rate: 采样率
            channels: 声道数
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
        
        # 播放队列
        self.play_queue = queue.Queue()
        
        # 播放线程
        self.is_playing = False
        self.play_thread: Optional[threading.Thread] = None
        
        logger.info(
            f"音频输出处理器初始化: sample_rate={sample_rate}, "
            f"channels={channels}"
        )
    
    def start(self):
        """开始播放"""
        if self.is_playing:
            logger.warning("播放已经在进行中")
            return
        
        try:
            # 打开音频流
            self.stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.device_index
            )
            
            self.is_playing = True
            
            # 启动播放线程
            self.play_thread = threading.Thread(target=self._play_loop)
            self.play_thread.daemon = True
            self.play_thread.start()
            
            logger.info("音频播放已开始")
            
        except Exception as e:
            logger.error(f"启动播放失败: {e}")
            raise
    
    def stop(self):
        """停止播放"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        
        # 清空队列
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
            except queue.Empty:
                break
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.play_thread:
            self.play_thread.join(timeout=1.0)
            self.play_thread = None
        
        logger.info("音频播放已停止")
    
    def play(self, audio_data: bytes):
        """
        播放音频数据
        
        Args:
            audio_data: 音频数据
        """
        if not self.is_playing:
            logger.warning("播放器未启动")
            return
        
        self.play_queue.put(audio_data)
    
    def play_sync(self, audio_data: bytes):
        """
        同步播放音频数据（阻塞直到播放完成）
        
        Args:
            audio_data: 音频数据
        """
        if not self.stream:
            self.start()
        
        try:
            self.stream.write(audio_data)
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
    
    def _play_loop(self):
        """播放循环"""
        while self.is_playing:
            try:
                # 从队列获取音频数据
                audio_data = self.play_queue.get(timeout=0.1)
                
                if audio_data and self.stream:
                    self.stream.write(audio_data)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"播放循环错误: {e}")
    
    def is_queue_empty(self) -> bool:
        """检查播放队列是否为空"""
        return self.play_queue.empty()
    
    def clear_queue(self):
        """清空播放队列"""
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
            except queue.Empty:
                break
        logger.debug("播放队列已清空")
    
    def list_devices(self) -> list:
        """
        列出所有音频输出设备
        
        Returns:
            设备信息列表
        """
        devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxOutputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        return devices
    
    def __del__(self):
        """析构函数"""
        self.stop()
        if self.pa:
            self.pa.terminate()
