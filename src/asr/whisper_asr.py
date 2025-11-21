"""Whisper ASR实现"""
import numpy as np
from typing import Optional
from .base_asr import BaseASR
from ..utils import get_logger

# 尝试导入 faster-whisper
try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_FASTER_WHISPER = False

logger = get_logger("whisper")


class WhisperASR(BaseASR):
    """Whisper语音识别"""
    
    def __init__(
        self,
        model: str = "base",
        language: str = "zh",
        device: str = "cpu",
        compute_type: str = "int8",
        local_model_path: str = None,
        **kwargs
    ):
        """
        初始化Whisper ASR
        
        Args:
            model: 模型大小 (tiny, base, small, medium, large) 或本地路径
            language: 识别语言
            device: 设备 (cpu, cuda)
            compute_type: 计算类型 (int8, float16, float32)
            local_model_path: 本地模型路径（优先使用）
        """
        super().__init__(language, **kwargs)
        
        if not HAS_FASTER_WHISPER:
            raise ImportError(
                "faster-whisper 未安装。请运行: pip install faster-whisper"
            )
        
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        
        # 确定模型路径
        import os
        from pathlib import Path
        
        # 优先使用 local_model_path
        if local_model_path and os.path.exists(local_model_path):
            model_path = local_model_path
            logger.info(f"使用本地模型: {model_path}")
        else:
            # 检查项目 models 目录
            project_model_dir = Path(__file__).parent.parent.parent / "models" / f"whisper-{model}"
            if project_model_dir.exists():
                model_path = str(project_model_dir)
                logger.info(f"使用项目本地模型: {model_path}")
            else:
                # 使用模型名称，从 Hugging Face 下载
                model_path = model
                logger.info(f"正在加载Whisper模型: {model}")
                logger.info("首次运行需要从网络下载模型文件，请耐心等待...")
                logger.info(f"模型将缓存到: ~/.cache/huggingface/hub/")
                logger.info("提示: 可以手动下载模型到 models/ 目录避免网络下载")
        
        # 加载模型
        try:
            self.model = WhisperModel(
                model_path,
                device=device,
                compute_type=compute_type
            )
            logger.info("✓ Whisper模型加载完成")
        except Exception as e:
            logger.error(f"加载Whisper模型失败: {e}")
            if not os.path.exists(str(model_path)):
                logger.error("提示: 如果是网络问题，可以:")
                logger.error("  1. 设置镜像: set HF_ENDPOINT=https://hf-mirror.com")
                logger.error("  2. 手动下载模型: python scripts/download_whisper_model.py")
            raise
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """转录音频"""
        try:
            # 将bytes转换为numpy数组
            # 假设音频是16bit PCM
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_np.astype(np.float32) / 32768.0
            
            # 转录
            segments, info = self.model.transcribe(
                audio_float,
                language=self.language if self.language != "auto" else None,
                beam_size=5,
                best_of=5,  # 增加候选数量
                temperature=0.0,  # 使用贪心解码，提高稳定性
                condition_on_previous_text=True,  # 利用上下文
                vad_filter=True,  # 启用VAD过滤
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=500
                )
            )
            
            # 合并所有段落
            text = " ".join([segment.text for segment in segments])
            
            logger.debug(f"识别结果: {text}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Whisper转录错误: {e}")
            return None
