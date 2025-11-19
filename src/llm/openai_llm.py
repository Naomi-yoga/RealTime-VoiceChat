"""OpenAI LLM实现"""
from typing import Generator, List, Dict
from openai import OpenAI
from .base_llm import BaseLLM
from ..utils import get_logger

logger = get_logger("openai")


class OpenAILLM(BaseLLM):
    """OpenAI大模型"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """初始化OpenAI LLM"""
        super().__init__(api_key, model, **kwargs)
        
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(f"OpenAI LLM已初始化: model={model}")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> Generator[str, None, None]:
        """生成响应"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenAI生成错误: {e}")
            yield f"[错误: {str(e)}]"
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI连接检查失败: {e}")
            return False
