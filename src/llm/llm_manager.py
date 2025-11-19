"""LLM管理器"""
from typing import Optional, Dict, Any
from .base_llm import BaseLLM
from .deepseek_llm import DeepSeekLLM
from .openai_llm import OpenAILLM
from ..utils import get_logger

logger = get_logger("llm_manager")


class LLMManager:
    """LLM管理器，负责创建和切换不同的LLM"""
    
    # 支持的LLM类型
    LLM_CLASSES = {
        'deepseek': DeepSeekLLM,
        'openai': OpenAILLM,
        'zhipu': OpenAILLM,  # 使用OpenAI兼容接口
        'kimi': OpenAILLM,   # 使用OpenAI兼容接口
        'ollama': OpenAILLM  # 使用OpenAI兼容接口
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.current_llm: Optional[BaseLLM] = None
        self.current_model_name: Optional[str] = None
    
    def create_llm(self, model_name: str) -> BaseLLM:
        """
        创建LLM实例
        
        Args:
            model_name: 模型名称
        
        Returns:
            LLM实例
        """
        if model_name not in self.config:
            raise ValueError(f"未知模型: {model_name}")
        
        model_config = self.config[model_name]
        
        # 检查API Key
        api_key = model_config.get('api_key')
        if not api_key:
            raise ValueError(f"模型 {model_name} 缺少API Key")
        
        # 获取LLM类
        llm_class = self.LLM_CLASSES.get(model_name)
        if not llm_class:
            raise ValueError(f"不支持的模型类型: {model_name}")
        
        # 创建实例
        try:
            llm = llm_class(
                api_key=api_key,
                model=model_config.get('model', model_name),
                base_url=model_config.get('base_url'),
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 2000)
            )
            logger.info(f"已创建LLM: {model_name}")
            return llm
        except Exception as e:
            logger.error(f"创建LLM失败: {e}")
            raise
    
    def switch_model(self, model_name: str):
        """
        切换模型
        
        Args:
            model_name: 模型名称
        """
        logger.info(f"切换模型: {self.current_model_name} -> {model_name}")
        self.current_llm = self.create_llm(model_name)
        self.current_model_name = model_name
    
    def get_current_llm(self) -> Optional[BaseLLM]:
        """获取当前LLM"""
        return self.current_llm
    
    def list_available_models(self) -> list:
        """列出可用的模型"""
        return list(self.config.keys())
