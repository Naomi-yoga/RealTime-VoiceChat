"""ASR管理器"""
from typing import Optional, Dict, Any
from .base_asr import BaseASR
from ..utils import get_logger

logger = get_logger("asr_manager")


class ASRManager:
    """ASR引擎管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ASR管理器
        
        Args:
            config: ASR配置字典
        """
        self.config = config
        self.current_engine: Optional[BaseASR] = None
        self.current_engine_name: Optional[str] = None
        self.available_engines: Dict[str, type] = {}
        
        # 注册可用的ASR引擎
        self._register_engines()
        
        # 初始化默认引擎
        default_engine = config.get('engine', 'whisper')
        try:
            self.switch_engine(default_engine)
        except Exception as e:
            logger.error(f"初始化默认ASR引擎失败: {e}")
            raise
    
    def _register_engines(self):
        """注册所有可用的ASR引擎"""
        # Whisper ASR
        try:
            from .whisper_asr import WhisperASR
            self.available_engines['whisper'] = WhisperASR
            logger.info("Whisper ASR 已注册")
        except ImportError as e:
            logger.warning(f"Whisper ASR 不可用: {e}")
            logger.warning("请安装: pip install faster-whisper")
    
    def switch_engine(self, engine_name: str):
        """
        切换ASR引擎
        
        Args:
            engine_name: 引擎名称
        """
        if engine_name not in self.available_engines:
            available = ', '.join(self.available_engines.keys())
            raise ValueError(
                f"ASR引擎 '{engine_name}' 不可用。"
                f"可用引擎: {available if available else '无'}"
            )
        
        # 获取引擎配置
        engine_config = self.config.get(engine_name, {})
        
        # 创建引擎实例
        try:
            engine_class = self.available_engines[engine_name]
            self.current_engine = engine_class(**engine_config)
            self.current_engine_name = engine_name
            logger.info(f"已切换到 ASR 引擎: {engine_name}")
        except Exception as e:
            logger.error(f"切换 ASR 引擎失败: {e}")
            raise
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        转录音频
        
        Args:
            audio_data: 音频数据
        
        Returns:
            识别文本
        """
        if self.current_engine is None:
            logger.error("没有可用的ASR引擎")
            return None
        
        return self.current_engine.transcribe(audio_data)
    
    def list_available_engines(self) -> list:
        """
        列出所有可用的ASR引擎
        
        Returns:
            引擎名称列表
        """
        return list(self.available_engines.keys())
    
    def get_current_engine_name(self) -> Optional[str]:
        """获取当前引擎名称"""
        return self.current_engine_name
