"""TTS管理器"""
from typing import Optional, Dict, Any, Iterator
from .base_tts import BaseTTS
from ..utils import get_logger

logger = get_logger("tts_manager")


class TTSManager:
    """TTS引擎管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化TTS管理器
        
        Args:
            config: TTS配置字典
        """
        self.config = config
        self.current_engine: Optional[BaseTTS] = None
        self.current_engine_name: Optional[str] = None
        self.available_engines: Dict[str, type] = {}
        
        # 注册可用的TTS引擎
        self._register_engines()
        
        # 初始化默认引擎
        # 优先使用voice_packs配置
        active_voice = config.get('active_voice')
        voice_packs = config.get('voice_packs', {})
        
        if active_voice and active_voice in voice_packs:
            # 使用语音包配置
            voice_pack = voice_packs[active_voice]
            default_engine = voice_pack.get('engine', config.get('engine', 'edge'))
            default_voice = voice_pack.get('voice', 'zh-CN-XiaoxiaoNeural')
            logger.info(f"使用语音包: {active_voice} (引擎: {default_engine}, 语音: {default_voice})")
        else:
            # 使用默认配置
            default_engine = config.get('engine', 'edge')
            default_voice = config.get('voice', 'zh-CN-XiaoxiaoNeural')
            if active_voice:
                logger.warning(f"语音包 '{active_voice}' 不存在，使用默认配置")
        
        try:
            self.switch_engine(default_engine, voice=default_voice)
        except Exception as e:
            logger.error(f"初始化默认TTS引擎失败: {e}")
            raise
    
    def _register_engines(self):
        """注册所有可用的TTS引擎"""
        # Edge TTS
        try:
            from .edge_tts_engine import EdgeTTSEngine
            self.available_engines['edge'] = EdgeTTSEngine
            logger.info("Edge TTS 已注册")
        except ImportError as e:
            logger.warning(f"Edge TTS 不可用: {e}")
            logger.warning("请安装: pip install edge-tts")
    
    def switch_engine(self, engine_name: str, voice: Optional[str] = None):
        """
        切换TTS引擎
        
        Args:
            engine_name: 引擎名称
            voice: 语音名称（可选）
        """
        if engine_name not in self.available_engines:
            available = ', '.join(self.available_engines.keys())
            raise ValueError(
                f"TTS引擎 '{engine_name}' 不可用。"
                f"可用引擎: {available if available else '无'}"
            )
        
        # 获取引擎配置
        engine_config = self.config.get(engine_name, {}).copy()
        
        # 如果指定了语音，覆盖配置中的语音
        if voice:
            engine_config['voice'] = voice
        
        # 创建引擎实例
        try:
            engine_class = self.available_engines[engine_name]
            self.current_engine = engine_class(**engine_config)
            self.current_engine_name = engine_name
            logger.info(f"已切换到 TTS 引擎: {engine_name}")
        except Exception as e:
            logger.error(f"切换 TTS 引擎失败: {e}")
            raise
    
    def synthesize(self, text: str) -> Optional[bytes]:
        """
        合成语音（一次性返回完整音频）
        
        Args:
            text: 文本内容
        
        Returns:
            音频数据
        """
        if self.current_engine is None:
            logger.error("没有可用的TTS引擎")
            return None
        
        return self.current_engine.synthesize(text)
    
    def synthesize_stream(self, text: str) -> Iterator[bytes]:
        """
        流式合成语音
        
        Args:
            text: 文本内容
        
        Yields:
            音频数据块
        """
        if self.current_engine is None:
            logger.error("没有可用的TTS引擎")
            return
        
        yield from self.current_engine.synthesize_stream(text)
    
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        合成语音并保存到文件
        
        Args:
            text: 文本内容
            output_path: 输出文件路径
        
        Returns:
            是否成功
        """
        if self.current_engine is None:
            logger.error("没有可用的TTS引擎")
            return False
        
        return self.current_engine.synthesize_to_file(text, output_path)
    
    def list_available_engines(self) -> list:
        """
        列出所有可用的TTS引擎
        
        Returns:
            引擎名称列表
        """
        return list(self.available_engines.keys())
    
    def get_current_engine_name(self) -> Optional[str]:
        """获取当前引擎名称"""
        return self.current_engine_name
    
    def get_current_voice(self) -> Optional[str]:
        """获取当前语音名称"""
        if self.current_engine:
            return self.current_engine.voice
        return None
