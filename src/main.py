"""RT-VoiceChat-CLI 主程序"""
import sys
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from .core import ConfigManager, ConversationManager
from .llm import LLMManager
from .asr import ASRManager
from .tts import TTSManager
from .audio import AudioInputHandler, AudioOutputHandler, VADDetector
from .utils import setup_logger, get_logger

console = Console()


class VoiceChatCLI:
    """语音聊天CLI应用"""
    
    def __init__(self, config_path: str = None):
        """初始化应用"""
        # 加载配置
        self.config_manager = ConfigManager(config_path)
        
        # 设置日志
        log_config = self.config_manager.get('logging', default={})
        setup_logger(
            level=log_config.get('level', 'INFO'),
            log_file=log_config.get('file'),
            console=log_config.get('console', True)
        )
        
        self.logger = get_logger("main")
        self.logger.info("=" * 50)
        self.logger.info("RT-VoiceChat-CLI 启动中...")
        
        # 初始化组件
        self._init_components()
    
    def _init_components(self):
        """初始化各个组件"""
        # 对话管理器
        conv_config = self.config_manager.get_conversation_config()
        self.conversation = ConversationManager(
            system_prompt=conv_config.get('system_prompt'),
            max_history=conv_config.get('max_history', 10),
            save_history=conv_config.get('save_history', True),
            history_file=conv_config.get('history_file', 'conversation_history.json')
        )
        
        # LLM管理器
        models_config = self.config_manager.get('models', default={})
        active_model = models_config.pop('active', 'deepseek')
        
        self.llm_manager = LLMManager(models_config)
        
        # 切换到活动模型
        try:
            self.llm_manager.switch_model(active_model)
            self.logger.info(f"已激活模型: {active_model}")
        except Exception as e:
            self.logger.error(f"激活模型失败: {e}")
            console.print(f"[red]错误: 无法激活模型 {active_model}[/red]")
            console.print("[yellow]请检查配置文件中的API Key是否正确[/yellow]")
            sys.exit(1)
        
        # ASR管理器（语音识别）
        asr_config = self.config_manager.get('asr', default={})
        try:
            self.asr_manager = ASRManager(asr_config)
            self.logger.info("ASR管理器初始化成功")
        except Exception as e:
            self.logger.warning(f"ASR管理器初始化失败: {e}")
            self.asr_manager = None
        
        # TTS管理器（语音合成）
        tts_config = self.config_manager.get('tts', default={})
        try:
            self.tts_manager = TTSManager(tts_config)
            self.logger.info("TTS管理器初始化成功")
        except Exception as e:
            self.logger.warning(f"TTS管理器初始化失败: {e}")
            self.tts_manager = None
        
        # 音频配置
        audio_config = self.config_manager.get('audio', default={})
        self.audio_input_config = audio_config.get('input', {})
        self.audio_output_config = audio_config.get('output', {})
        self.vad_config = audio_config.get('vad', {})
        
        self.logger.info("所有组件初始化完成")
    
    def run_text_mode(self):
        """运行纯文本模式（用于测试）"""
        console.print(Panel.fit(
            "[bold cyan]RT-VoiceChat-CLI[/bold cyan]\n"
            "[yellow]文本模式 (测试版)[/yellow]\n"
            f"当前模型: {self.llm_manager.current_model_name}",
            border_style="cyan"
        ))
        
        console.print("\n[green]提示:[/green]")
        console.print("  - 输入文本与AI对话")
        console.print("  - 输入 /quit 或 /exit 退出")
        console.print("  - 输入 /clear 清空对话历史")
        console.print("  - 输入 /model 切换模型")
        console.print()
        
        while True:
            try:
                # 获取用户输入
                user_input = console.input("[bold cyan]你:[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    if user_input in ['/quit', '/exit', '/q']:
                        console.print("[yellow]再见！[/yellow]")
                        break
                    elif user_input == '/clear':
                        self.conversation.clear_history()
                        console.print("[green]对话历史已清空[/green]")
                        continue
                    elif user_input == '/model':
                        self._switch_model_interactive()
                        continue
                    elif user_input == '/help':
                        self._show_help()
                        continue
                    else:
                        console.print(f"[red]未知命令: {user_input}[/red]")
                        continue
                
                # 添加用户消息
                self.conversation.add_user_message(user_input)
                
                # 生成AI响应
                console.print("[bold green]AI:[/bold green] ", end="")
                
                response_text = ""
                try:
                    llm = self.llm_manager.get_current_llm()
                    messages = self.conversation.get_messages()
                    
                    for token in llm.generate(messages, stream=True):
                        console.print(token, end="")
                        response_text += token
                    
                    console.print()  # 换行
                    
                    # 保存助手回复
                    if response_text:
                        self.conversation.add_assistant_message(response_text)
                    
                except Exception as e:
                    console.print(f"\n[red]生成响应时出错: {e}[/red]")
                    self.logger.error(f"生成响应错误: {e}", exc_info=True)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]检测到中断，退出程序[/yellow]")
                break
            except EOFError:
                # 非交互式环境或输入流关闭
                console.print("\n[yellow]输入流已关闭，退出程序[/yellow]")
                self.logger.info("检测到 EOFError，程序正常退出")
                break
            except Exception as e:
                console.print(f"[red]发生错误: {e}[/red]")
                self.logger.error(f"主循环错误: {e}", exc_info=True)
    
    def _switch_model_interactive(self):
        """交互式切换模型"""
        available_models = self.llm_manager.list_available_models()
        
        console.print("\n[cyan]可用模型:[/cyan]")
        for i, model in enumerate(available_models, 1):
            current = "✓" if model == self.llm_manager.current_model_name else " "
            console.print(f"  [{current}] {i}. {model}")
        
        try:
            choice = console.input("\n[cyan]选择模型 (输入序号或名称):[/cyan] ").strip()
            
            # 尝试解析为序号
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(available_models):
                    model_name = available_models[index]
                else:
                    console.print("[red]无效的序号[/red]")
                    return
            else:
                model_name = choice
            
            # 切换模型
            self.llm_manager.switch_model(model_name)
            console.print(f"[green]已切换到模型: {model_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]切换模型失败: {e}[/red]")
    
    def _show_help(self):
        """显示帮助信息"""
        console.print("\n[bold cyan]可用命令:[/bold cyan]")
        console.print("  /quit, /exit, /q  - 退出程序")
        console.print("  /clear            - 清空对话历史")
        console.print("  /model            - 切换模型")
        console.print("  /help             - 显示此帮助信息")
        console.print()
    
    def run_voice_mode(self):
        """运行语音模式"""
        # 检查必要的组件
        if not self.asr_manager:
            console.print("[red]错误: ASR管理器未初始化，无法使用语音模式[/red]")
            console.print("[yellow]请检查配置文件中的ASR设置[/yellow]")
            return
        
        if not self.tts_manager:
            console.print("[red]错误: TTS管理器未初始化，无法使用语音模式[/red]")
            console.print("[yellow]请检查配置文件中的TTS设置[/yellow]")
            return
        
        console.print(Panel.fit(
            "[bold cyan]RT-VoiceChat-CLI[/bold cyan]\n"
            "[bold green]语音模式[/bold green]\n"
            f"模型: {self.llm_manager.current_model_name}\n"
            f"ASR: {self.asr_manager.get_current_engine_name()}\n"
            f"TTS: {self.tts_manager.get_current_engine_name()}",
            border_style="cyan"
        ))
        
        console.print("\n[green]提示:[/green]")
        console.print("  - 对着麦克风说话，系统会自动检测语音")
        console.print("  - 静音一段时间后自动识别并生成回复")
        console.print("  - 按 Ctrl+C 退出")
        console.print()
        
        # 初始化音频组件
        try:
            # 计算VAD需要的帧大小（如果启用VAD）
            vad_enabled = self.vad_config.get('enabled', True)
            sample_rate = self.audio_input_config.get('sample_rate', 16000)
            
            if vad_enabled:
                # VAD需要特定大小的帧（30ms，16kHz = 480样本 = 960字节）
                frame_duration_ms = self.vad_config.get('frame_duration_ms', 30)
                vad_chunk_size = int(sample_rate * frame_duration_ms / 1000) * 2  # *2 for int16
                chunk_size = vad_chunk_size
                console.print(f"[cyan]VAD已启用，使用chunk_size={chunk_size}字节[/cyan]")
            else:
                chunk_size = self.audio_input_config.get('chunk_size', 1024)
            
            # 音频输入
            audio_input = AudioInputHandler(
                sample_rate=sample_rate,
                channels=self.audio_input_config.get('channels', 1),
                chunk_size=chunk_size,
                device_index=self.audio_input_config.get('device_index'),
                format=self.audio_input_config.get('format', 'int16')
            )
            
            # 音频输出
            audio_output = AudioOutputHandler(
                sample_rate=self.audio_output_config.get('sample_rate', 24000),
                channels=self.audio_output_config.get('channels', 1),
                device_index=self.audio_output_config.get('device_index'),
                format='int16'
            )
            
            # VAD检测器
            if vad_enabled:
                try:
                    vad = VADDetector(
                        sample_rate=sample_rate,
                        aggressiveness=self.vad_config.get('aggressiveness', 3),
                        frame_duration_ms=self.vad_config.get('frame_duration_ms', 30),
                        padding_duration_ms=self.vad_config.get('padding_duration_ms', 300),
                        silence_duration_ms=self.vad_config.get('silence_duration_ms', 700)
                    )
                    if vad.vad is None:
                        console.print("[yellow]警告: webrtcvad未安装，VAD功能受限[/yellow]")
                        console.print("[yellow]将使用简单的能量检测[/yellow]")
                        vad = None
                        vad_enabled = False
                except Exception as e:
                    console.print(f"[yellow]VAD初始化失败: {e}[/yellow]")
                    console.print("[yellow]将禁用VAD检测[/yellow]")
                    vad = None
                    vad_enabled = False
            else:
                vad = None
                console.print("[yellow]VAD检测已禁用[/yellow]")
            
            # 启动音频输出
            audio_output.start()
            
            # 音频缓冲区
            audio_buffer = []
            is_listening = False
            silence_counter = 0  # 用于简单能量检测的静音计数器
            listening_start_time = None  # 开始监听的时间
            max_listening_duration = 10.0  # 最大监听时长（秒），防止无限等待
            
            # VAD降级机制：如果VAD长时间未触发但检测到能量，自动切换到能量检测
            vad_fallback_enabled = True  # 是否启用VAD降级
            vad_fallback_trigger_count = 0  # VAD未触发但能量高的次数
            vad_fallback_threshold = 10  # 连续10次（约0.3秒）能量高但VAD未触发，则降级
            use_energy_fallback = False  # 是否已切换到能量检测
            
            console.print("[green]✓ 音频系统已就绪，开始监听...[/green]")
            console.print(f"[dim]采样率: {sample_rate}Hz, Chunk大小: {chunk_size}字节[/dim]")
            if vad and hasattr(vad, 'vad') and vad.vad:
                console.print(f"[dim]VAD: 已启用 (aggressiveness={vad.aggressiveness})[/dim]")
                console.print(f"[dim]VAD参数: 静音时长={self.vad_config.get('silence_duration_ms', 700)}ms[/dim]")
            else:
                console.print("[dim]VAD: 使用简单能量检测[/dim]")
            console.print("[yellow]提示: 请对着麦克风说话，系统会自动检测语音[/yellow]")
            console.print()
            
            # 添加调试计数器
            callback_count = [0]  # 使用列表以便在闭包中修改
            last_energy_log = [0]  # 上次打印能量的时间
            
            def audio_callback(audio_chunk: bytes):
                """音频输入回调"""
                nonlocal audio_buffer, is_listening, silence_counter, listening_start_time
                nonlocal use_energy_fallback, vad_fallback_trigger_count
                import time
                import numpy as np
                
                callback_count[0] += 1
                
                # 计算音频能量
                audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
                energy = np.abs(audio_np).mean()
                
                # 每100次回调打印一次调试信息（约每3秒）
                if callback_count[0] % 100 == 0:
                    self.logger.debug(f"音频回调 #{callback_count[0]}, 能量: {energy:.1f}, 监听状态: {is_listening}, 缓冲区: {len(audio_buffer)}")
                
                # 能量阈值和静音阈值
                energy_threshold = 300  # 能量阈值
                energy_silence_threshold = 20  # 能量检测的静音帧数（约0.6秒）
                
                # 检查是否使用VAD
                has_vad = vad and hasattr(vad, 'vad') and vad.vad is not None
                
                # VAD降级检查：如果能量高但VAD长时间未触发，切换到能量检测
                # VAD降级检查：如果能量高但VAD长时间未触发，切换到能量检测
                if has_vad and vad_fallback_enabled and not use_energy_fallback and not is_listening:
                    if energy > energy_threshold:
                        vad_fallback_trigger_count += 1
                        # 每10次打印一次调试信息
                        if vad_fallback_trigger_count % 10 == 0:
                            console.print(f"[yellow]检测到音频能量: {energy:.0f}，VAD未触发 (计数: {vad_fallback_trigger_count}/{vad_fallback_threshold})[/yellow]")
                        if vad_fallback_trigger_count >= vad_fallback_threshold:
                            use_energy_fallback = True
                            console.print(f"[yellow]⚠ VAD未响应，自动切换到能量检测模式（能量: {energy:.0f}）[/yellow]")
                    else:
                        vad_fallback_trigger_count = 0
                
                if has_vad and not use_energy_fallback:
                    # 使用VAD检测
                    # 检查帧大小是否匹配
                    expected_frame_size = vad.frame_size * 2  # int16 = 2 bytes
                    actual_frame_size = len(audio_chunk)
                    
                    # 每50次回调检查一次VAD状态（用于调试）
                    if callback_count[0] % 50 == 0 and not is_listening:
                        if actual_frame_size != expected_frame_size:
                            console.print(f"[red]⚠ VAD帧大小不匹配: 期望={expected_frame_size}字节, 实际={actual_frame_size}字节[/red]")
                            console.print(f"[red]   这会导致VAD无法工作！请检查chunk_size配置[/red]")
                    
                    is_speech, complete_audio = vad.process_frame(audio_chunk)
                    
                    # 每50次回调检查一次VAD状态（用于调试）
                    if callback_count[0] % 50 == 0 and not is_listening:
                        # 显示VAD状态和音频能量
                        vad_triggered = hasattr(vad, 'triggered') and vad.triggered
                        vad_is_speech = hasattr(vad, 'is_speech') and vad.is_speech
                        ring_buffer_len = len(vad.ring_buffer) if hasattr(vad, 'ring_buffer') else 0
                        silence_counter = vad.silence_counter if hasattr(vad, 'silence_counter') else 0
                        
                        # console.print(f"[dim]VAD调试: triggered={vad_triggered}, is_speech={vad_is_speech}, "
                        #             f"ring_buffer={ring_buffer_len}, silence={silence_counter}, 能量={energy:.0f}[/dim]")
                        
                        if energy > energy_threshold and not vad_triggered:
                            # 计算ring_buffer中语音帧的比例
                            if hasattr(vad, 'ring_buffer') and len(vad.ring_buffer) > 0:
                                num_voiced = sum(1 for _, speech in vad.ring_buffer if speech)
                                voiced_ratio = num_voiced / len(vad.ring_buffer)
                                console.print(f"[yellow]能量高但VAD未触发: 能量={energy:.0f}, "
                                            f"语音帧比例={voiced_ratio:.2%} (需要>50%才能触发)[/yellow]")
                            else:
                                console.print(f"[yellow]检测到音频能量: {energy:.0f}，但VAD未触发（可能需要调整VAD参数）[/yellow]")
                    
                    if is_speech:
                        if not is_listening:
                            is_listening = True
                            listening_start_time = time.time()
                            console.print(f"[cyan]🎤 检测到语音（VAD）... (能量: {energy:.0f})[/cyan]")
                            audio_buffer = []
                        
                        # 持续收集音频
                        audio_buffer.append(audio_chunk)
                        
                        # 检查超时（防止无限等待）
                        if listening_start_time:
                            elapsed = time.time() - listening_start_time
                            if elapsed > max_listening_duration:
                                console.print(f"[yellow]⚠ 监听超时（{max_listening_duration}秒），强制处理...[/yellow]")
                                is_listening = False
                                listening_start_time = None
                                if len(audio_buffer) > 0:
                                    self._process_voice_input(
                                        b''.join(audio_buffer),
                                        audio_output,
                                        audio_input
                                    )
                                    audio_buffer = []
                    else:
                        # 如果检测到完整语音段（语音结束）
                        if complete_audio:
                            is_listening = False
                            listening_start_time = None
                            audio_length = len(complete_audio)
                            duration_ms = (audio_length / 2 / sample_rate) * 1000  # int16 = 2 bytes
                            console.print(f"[cyan]✓ 语音结束（VAD），开始处理... (长度: {audio_length}字节, 约{duration_ms:.0f}ms)[/cyan]")
                            self._process_voice_input(
                                complete_audio,
                                audio_output,
                                audio_input
                            )
                            audio_buffer = []
                        elif is_listening and len(audio_buffer) > 0:
                            # 静音但之前有语音，继续收集（等待VAD确认结束）
                            audio_buffer.append(audio_chunk)
                else:
                    # VAD不可用或已降级，使用能量检测
                    if energy > energy_threshold:
                        if not is_listening:
                            is_listening = True
                            listening_start_time = time.time()
                            silence_counter = 0
                            console.print(f"[cyan]🎤 检测到语音（能量检测）... (能量: {energy:.0f})[/cyan]")
                            audio_buffer = []
                        audio_buffer.append(audio_chunk)
                        silence_counter = 0
                    else:
                        if is_listening:
                            silence_counter += 1
                            audio_buffer.append(audio_chunk)  # 继续收集，可能还有尾音
                            
                            # 静音一段时间后处理
                            if silence_counter >= energy_silence_threshold and len(audio_buffer) > 0:
                                is_listening = False
                                listening_start_time = None
                                silence_counter = 0
                                console.print(f"[cyan]✓ 语音结束（能量检测），开始处理... (收集了 {len(audio_buffer)} 个音频块)[/cyan]")
                                self._process_voice_input(
                                    b''.join(audio_buffer),
                                    audio_output,
                                    audio_input
                                )
                                audio_buffer = []
            
            # 开始录音
            audio_input.start(callback=audio_callback)
            
            console.print("[bold green]正在监听中... (按 Ctrl+C 退出)[/bold green]")
            console.print("[dim]提示: 如果长时间没有响应，可以尝试：[/dim]")
            console.print("[dim]  1. 检查麦克风是否正常工作[/dim]")
            console.print("[dim]  2. 调整系统音量设置[/dim]")
            if vad and hasattr(vad, 'aggressiveness') and vad.aggressiveness >= 3:
                console.print(f"[yellow]  3. 当前VAD aggressiveness={vad.aggressiveness}（很激进），建议降低到1-2[/yellow]")
                console.print("[yellow]     编辑 config/default_config.yaml，将 vad.aggressiveness 改为 1 或 2[/yellow]")
            console.print()
            
            # 主循环
            try:
                import time
                last_debug_time = time.time()
                while True:
                    time.sleep(0.1)
                    
                    # 每5秒打印一次状态（如果没有任何活动）
                    current_time = time.time()
                    if current_time - last_debug_time > 5:
                        if callback_count[0] == 0:
                            console.print("[yellow]⚠ 警告: 音频回调似乎没有被调用，请检查麦克风连接[/yellow]")
                        elif not is_listening and len(audio_buffer) == 0:
                            # 显示当前音频能量（用于调试）
                            if callback_count[0] > 0:
                                console.print(f"[dim]状态: 监听中... (已接收 {callback_count[0]} 个音频块)[/dim]")
                        last_debug_time = current_time
            except KeyboardInterrupt:
                console.print("\n[yellow]正在退出...[/yellow]")
            finally:
                # 清理资源
                audio_input.stop()
                audio_output.stop()
                console.print("[green]✓ 已退出语音模式[/green]")
                
        except ImportError as e:
            console.print(f"[red]错误: 缺少必要的依赖: {e}[/red]")
            console.print("[yellow]请安装: pip install pyaudio[/yellow]")
        except Exception as e:
            console.print(f"[red]启动语音模式失败: {e}[/red]")
            self.logger.error(f"语音模式错误: {e}", exc_info=True)
    
    def _process_voice_input(self, audio_data: bytes, audio_output: AudioOutputHandler, audio_input: AudioInputHandler):
        """处理语音输入"""
        try:
            # 1. ASR识别
            console.print("[yellow]🔍 正在识别语音...[/yellow]")
            text = self.asr_manager.transcribe(audio_data)
            
            if not text or len(text.strip()) == 0:
                console.print("[yellow]未识别到有效文本[/yellow]\n")
                return
            
            console.print(f"[bold cyan]你说:[/bold cyan] {text}")
            
            # 2. 添加到对话历史
            self.conversation.add_user_message(text)
            
            # 3. LLM生成回复
            console.print("[yellow]🤔 AI正在思考...[/yellow]")
            llm = self.llm_manager.get_current_llm()
            messages = self.conversation.get_messages()
            
            response_text = ""
            try:
                for token in llm.generate(messages, stream=True):
                    response_text += token
                    # 可以在这里显示流式输出（可选）
                
                if not response_text:
                    console.print("[red]AI未生成回复[/red]\n")
                    return
                
                console.print(f"[bold green]AI:[/bold green] {response_text}")
                
                # 保存回复
                self.conversation.add_assistant_message(response_text)
                
            except Exception as e:
                console.print(f"[red]生成回复失败: {e}[/red]")
                self.logger.error(f"LLM生成错误: {e}", exc_info=True)
                return
            
            # 4. TTS合成（直接使用原始文本）
            console.print("[yellow]🔊 正在合成语音...[/yellow]")
            try:
                audio_data = self.tts_manager.synthesize(response_text)
                
                if audio_data:
                    # 转换音频格式（Edge TTS返回MP3，需要转换为PCM）
                    pcm_data = self._convert_audio_to_pcm(audio_data, audio_output.sample_rate)
                    
                    if pcm_data:
                        # 5. 播放音频（同步播放，等待完成）
                        console.print("[yellow]🔊 正在播放...[/yellow]")
                        audio_output.play_sync(pcm_data)
                        console.print("[green]✓ 完成\n[/green]")
                    else:
                        console.print("[red]音频格式转换失败[/red]\n")
                else:
                    console.print("[red]TTS合成失败[/red]\n")
                    
            except Exception as e:
                console.print(f"[red]TTS合成失败: {e}[/red]")
                self.logger.error(f"TTS错误: {e}", exc_info=True)
                
        except Exception as e:
            console.print(f"[red]处理语音输入失败: {e}[/red]")
            self.logger.error(f"处理语音输入错误: {e}", exc_info=True)
      
    def _convert_audio_to_pcm(self, audio_data: bytes, target_sample_rate: int) -> Optional[bytes]:
        """
        将音频数据转换为PCM格式
        
        Args:
            audio_data: 原始音频数据（可能是MP3等格式）
            target_sample_rate: 目标采样率
            
        Returns:
            PCM格式的音频数据
        """
        try:
            # 尝试使用 pydub 转换
            try:
                from pydub import AudioSegment
                import io
                
                # 从字节流加载音频
                audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                
                # 转换为目标采样率
                audio_segment = audio_segment.set_frame_rate(target_sample_rate)
                
                # 转换为单声道
                audio_segment = audio_segment.set_channels(1)
                
                # 转换为16位PCM
                audio_segment = audio_segment.set_sample_width(2)  # 2 bytes = 16 bits
                
                # 导出为原始PCM数据
                pcm_data = audio_segment.raw_data
                
                return pcm_data
                
            except ImportError:
                self.logger.warning("pydub 未安装，无法转换音频格式")
                console.print("[yellow]警告: 需要安装 pydub 来播放音频[/yellow]")
                console.print("[yellow]安装: pip install pydub[/yellow]")
                return None
            except Exception as e:
                self.logger.error(f"音频转换失败: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"音频转换错误: {e}", exc_info=True)
            return None
                
        except Exception as e:
            console.print(f"[red]处理语音输入失败: {e}[/red]")
            self.logger.error(f"处理语音输入错误: {e}", exc_info=True)


@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--model', '-m', help='使用的模型名称')
@click.option('--voice', '-v', help='语音包名称')
@click.option('--text-mode', '-t', is_flag=True, help='文本模式（测试）')
def main(config, model, voice, text_mode):
    """RT-VoiceChat-CLI - 实时语音聊天命令行工具"""
    try:
        # 创建应用实例
        app = VoiceChatCLI(config_path=config)
        
        # 如果指定了模型，切换到该模型
        if model:
            try:
                app.llm_manager.switch_model(model)
                console.print(f"[green]已切换到模型: {model}[/green]")
            except Exception as e:
                console.print(f"[red]切换模型失败: {e}[/red]")
                sys.exit(1)
        
        # 运行模式
        if text_mode:
            app.run_text_mode()
        else:
            app.run_voice_mode()
            
    except Exception as e:
        console.print(f"[red]程序启动失败: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
