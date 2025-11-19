"""实时流语音转文字测试"""
import sys
import time
import threading
import queue
from collections import deque
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from src.core import ConfigManager
from src.asr import ASRManager
from src.audio import VADDetector
from src.utils import setup_logger, get_logger, calculate_rms

# 尝试导入音频输入
try:
    from src.audio import AudioInputHandler
    HAS_AUDIO_INPUT = True
except ImportError:
    AudioInputHandler = None
    HAS_AUDIO_INPUT = False

# 设置日志
setup_logger(level='INFO', console=True)
logger = get_logger("realtime_asr")
console = Console()


class RealtimeASR:
    """实时语音识别"""
    
    def __init__(self, asr_manager: ASRManager, sample_rate: int = 16000):
        """
        初始化实时 ASR
        
        Args:
            asr_manager: ASR 管理器
            sample_rate: 采样率
        """
        self.asr_manager = asr_manager
        self.sample_rate = sample_rate
        
        # 音频缓冲
        self.audio_buffer = deque(maxlen=100)  # 保留最近 100 个块
        self.is_running = False
        
        # VAD 检测器
        self.vad = VADDetector(
            sample_rate=sample_rate,
            aggressiveness=3,
            frame_duration_ms=30,
            silence_duration_ms=700
        )
        
        # 识别队列
        self.recognition_queue = queue.Queue()
        self.recognition_thread = None
        
        # 结果存储
        self.results = []
        self.current_audio_level = 0.0
        self.is_speech_active = False
    
    def start(self):
        """开始实时识别"""
        self.is_running = True
        
        # 启动识别线程
        self.recognition_thread = threading.Thread(target=self._recognition_worker)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        logger.info("实时 ASR 已启动")
    
    def stop(self):
        """停止实时识别"""
        self.is_running = False
        
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
        
        logger.info("实时 ASR 已停止")
    
    def process_audio_chunk(self, audio_chunk: bytes):
        """
        处理音频块
        
        Args:
            audio_chunk: 音频数据块
        """
        if not self.is_running:
            return
        
        # 添加到缓冲区
        self.audio_buffer.append(audio_chunk)
        
        # 计算音频电平
        import numpy as np
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
        self.current_audio_level = calculate_rms(audio_np)
        
        # VAD 检测
        is_speech, complete_audio = self.vad.process_frame(audio_chunk)
        self.is_speech_active = is_speech
        
        # 如果检测到完整语音段落，加入识别队列
        if complete_audio is not None:
            logger.debug("检测到完整语音段落，加入识别队列")
            self.recognition_queue.put(complete_audio)
    
    def _recognition_worker(self):
        """识别工作线程"""
        while self.is_running:
            try:
                # 从队列获取音频
                audio_data = self.recognition_queue.get(timeout=0.1)
                
                # 执行识别
                logger.debug("开始识别...")
                start_time = time.time()
                text = self.asr_manager.transcribe(audio_data)
                elapsed = time.time() - start_time
                
                if text and text.strip():
                    result = {
                        'text': text.strip(),
                        'timestamp': time.strftime('%H:%M:%S'),
                        'elapsed': elapsed
                    }
                    self.results.append(result)
                    logger.info(f"识别结果: {text} (耗时: {elapsed:.2f}s)")
                else:
                    logger.debug("未识别到内容")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"识别错误: {e}")
    
    def get_status_text(self) -> Text:
        """获取状态文本"""
        status = Text()
        
        # 音频电平
        level_bars = int(self.current_audio_level * 50)
        level_color = "green" if self.is_speech_active else "dim"
        status.append("音频电平: ", style="bold")
        status.append("█" * level_bars, style=level_color)
        status.append("\n\n")
        
        # 语音状态
        status.append("语音状态: ", style="bold")
        if self.is_speech_active:
            status.append("● 检测到语音", style="bold green")
        else:
            status.append("○ 静音", style="dim")
        status.append("\n\n")
        
        # 待识别队列
        queue_size = self.recognition_queue.qsize()
        status.append(f"待识别队列: {queue_size}\n\n", style="bold")
        
        # 最近的识别结果
        status.append("最近识别结果:\n", style="bold cyan")
        if self.results:
            for result in self.results[-5:]:  # 显示最近 5 条
                status.append(f"[{result['timestamp']}] ", style="dim")
                status.append(f"{result['text']}\n", style="white")
        else:
            status.append("(暂无结果)\n", style="dim")
        
        return status


def test_realtime_recognition():
    """测试实时语音识别"""
    console.print("\n[bold cyan]实时流语音转文字测试[/bold cyan]\n")
    
    # 检查依赖
    if not HAS_AUDIO_INPUT:
        console.print("[red]错误: AudioInputHandler 不可用[/red]")
        console.print("[yellow]请安装: pip install pyaudio[/yellow]")
        return
    
    # 1. 初始化 ASR
    console.print("[1/4] 初始化 ASR 引擎...")
    try:
        config_manager = ConfigManager()
        asr_config = config_manager.get('asr', default={})
        asr_manager = ASRManager(asr_config)
        console.print(f"[green]✓[/green] 当前引擎: {asr_manager.get_current_engine_name()}")
    except Exception as e:
        console.print(f"[red]✗ ASR 初始化失败: {e}[/red]")
        return
    
    # 2. 初始化音频输入
    console.print("\n[2/4] 初始化音频输入...")
    try:
        audio_input = AudioInputHandler(
            sample_rate=16000,
            channels=1,
            chunk_size=480  # 30ms @ 16kHz
        )
        
        # 列出设备
        devices = audio_input.list_devices()
        console.print(f"[green]✓[/green] 找到 {len(devices)} 个输入设备")
        for dev in devices[:3]:  # 显示前 3 个
            console.print(f"  [{dev['index']}] {dev['name']}")
            
    except Exception as e:
        console.print(f"[red]✗ 音频输入初始化失败: {e}[/red]")
        return
    
    # 3. 创建实时 ASR
    console.print("\n[3/4] 创建实时 ASR 实例...")
    realtime_asr = RealtimeASR(asr_manager, sample_rate=16000)
    console.print("[green]✓[/green] 实时 ASR 已创建")
    
    # 4. 开始录音和识别
    console.print("\n[4/4] 开始实时识别...")
    console.print("\n[yellow]提示:[/yellow]")
    console.print("  - 对着麦克风说话，程序会自动检测语音并识别")
    console.print("  - 按 Ctrl+C 停止")
    console.print("\n" + "=" * 50 + "\n")
    
    try:
        # 启动实时 ASR
        realtime_asr.start()
        
        # 定义音频回调
        def audio_callback(audio_chunk: bytes):
            realtime_asr.process_audio_chunk(audio_chunk)
        
        # 启动录音
        audio_input.start(callback=audio_callback)
        
        # 实时显示状态
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                status_panel = Panel(
                    realtime_asr.get_status_text(),
                    title="[bold]实时语音识别状态[/bold]",
                    border_style="cyan"
                )
                live.update(status_panel)
                time.sleep(0.25)
                
    except KeyboardInterrupt:
        console.print("\n\n[yellow]检测到中断，正在停止...[/yellow]")
    except Exception as e:
        console.print(f"\n\n[red]错误: {e}[/red]")
        logger.error(f"实时识别错误: {e}", exc_info=True)
    finally:
        # 清理资源
        audio_input.stop()
        realtime_asr.stop()
        
        # 显示总结
        console.print("\n" + "=" * 50)
        console.print(f"[bold]识别总结[/bold]")
        console.print("=" * 50)
        console.print(f"总共识别: {len(realtime_asr.results)} 段")
        
        if realtime_asr.results:
            console.print("\n[bold cyan]完整识别结果:[/bold cyan]")
            for i, result in enumerate(realtime_asr.results, 1):
                console.print(f"{i}. [{result['timestamp']}] {result['text']}")
                console.print(f"   (耗时: {result['elapsed']:.2f}秒)")


def main():
    """主函数"""
    try:
        test_realtime_recognition()
    except Exception as e:
        console.print(f"[red]程序错误: {e}[/red]")
        logger.error(f"程序错误: {e}", exc_info=True)
    
    console.print("\n[green]测试完成[/green]")


if __name__ == "__main__":
    main()
