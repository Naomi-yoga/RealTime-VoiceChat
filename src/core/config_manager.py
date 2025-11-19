"""配置管理器"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from ..utils import get_logger

logger = get_logger("config")


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载环境变量
        load_dotenv()
        
        # 确定配置文件路径
        if config_path is None:
            # 使用默认配置
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "default_config.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # 加载配置
        self._load_config()
        
        # 使用环境变量覆盖API密钥
        self._override_from_env()
        
        logger.info(f"配置已加载: {self.config_path}")
    
    def _load_config(self):
        """从文件加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.debug(f"配置文件加载成功: {self.config_path}")
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
    
    def _override_from_env(self):
        """使用环境变量覆盖配置"""
        env_mappings = {
            'DEEPSEEK_API_KEY': ['models', 'deepseek', 'api_key'],
            'OPENAI_API_KEY': ['models', 'openai', 'api_key'],
            'ZHIPU_API_KEY': ['models', 'zhipu', 'api_key'],
            'AZURE_SPEECH_KEY': ['asr', 'azure', 'api_key'],
            'AZURE_SPEECH_REGION': ['asr', 'azure', 'region'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_config(config_path, value)
                logger.debug(f"从环境变量覆盖配置: {env_var}")
    
    def _set_nested_config(self, path: list, value: Any):
        """设置嵌套配置值"""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, *keys, default=None) -> Any:
        """
        获取配置值
        
        Args:
            *keys: 配置键路径
            default: 默认值
        
        Returns:
            配置值
        
        Example:
            config.get('models', 'deepseek', 'api_key')
        """
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, *keys, value: Any):
        """
        设置配置值
        
        Args:
            *keys: 配置键路径
            value: 配置值
        
        Example:
            config.set('models', 'active', value='openai')
        """
        if not keys:
            raise ValueError("至少需要一个键")
        
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        logger.debug(f"配置已更新: {'.'.join(keys)} = {value}")
    
    def save(self, path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            path: 保存路径，如果为None则保存到当前配置文件
        """
        save_path = Path(path) if path else self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模型配置
        
        Args:
            model_name: 模型名称，如果为None则使用活动模型
        
        Returns:
            模型配置字典
        """
        if model_name is None:
            model_name = self.get('models', 'active', default='deepseek')
        
        model_config = self.get('models', model_name, default={})
        if not model_config:
            logger.warning(f"模型配置不存在: {model_name}")
        
        return model_config
    
    def get_asr_config(self) -> Dict[str, Any]:
        """获取语音识别配置"""
        return self.get('asr', default={})
    
    def get_tts_config(self) -> Dict[str, Any]:
        """获取语音合成配置"""
        return self.get('tts', default={})
    
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return self.get('audio', default={})
    
    def get_conversation_config(self) -> Dict[str, Any]:
        """获取对话配置"""
        return self.get('conversation', default={})
    
    def __repr__(self) -> str:
        return f"ConfigManager(config_path='{self.config_path}')"
