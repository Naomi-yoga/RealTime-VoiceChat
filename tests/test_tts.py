"""TTS语音合成测试"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def test_tts_manager():
    """测试TTS管理器"""
    console.print("\n[bold cyan]测试 1: TTS管理器初始化[/bold cyan]\n")
    
    try:
        from src.tts import TTSManager
        from src.core import ConfigManager
        
        # 加载配置
        config_manager = ConfigManager()
        tts_config = config_manager.get('tts', default={})
        
        # 创建TTS管理器
        tts_manager = TTSManager(tts_config)
        
        console.print(f"[green]✓ TTS管理器初始化成功[/green]")
        console.print(f"  当前引擎: {tts_manager.get_current_engine_name()}")
        console.print(f"  当前语音: {tts_manager.get_current_voice()}")
        
        # 列出可用引擎
        engines = tts_manager.list_available_engines()
        console.print(f"  可用引擎: {', '.join(engines)}")
        
        return tts_manager
        
    except Exception as e:
        console.print(f"[red]✗ TTS管理器初始化失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def test_edge_tts_basic(tts_manager):
    """测试Edge TTS基本合成"""
    console.print("\n[bold cyan]测试 2: Edge TTS 基本合成[/bold cyan]\n")
    
    if not tts_manager:
        console.print("[yellow]跳过测试（TTS管理器未初始化）[/yellow]")
        return False
    
    try:
        test_text = "你好，我是语音合成测试。"
        
        console.print(f"合成文本: {test_text}")
        console.print("正在合成...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("合成中...", total=None)
            
            start_time = time.time()
            audio_data = tts_manager.synthesize(test_text)
            elapsed = time.time() - start_time
            
            progress.remove_task(task)
        
        if audio_data:
            console.print(f"[green]✓ 合成成功[/green]")
            console.print(f"  音频大小: {len(audio_data)} 字节")
            console.print(f"  耗时: {elapsed:.2f} 秒")
            return True
        else:
            console.print("[red]✗ 合成失败（返回None）[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ 合成失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_edge_tts_stream(tts_manager):
    """测试Edge TTS流式合成"""
    console.print("\n[bold cyan]测试 3: Edge TTS 流式合成[/bold cyan]\n")
    
    if not tts_manager:
        console.print("[yellow]跳过测试（TTS管理器未初始化）[/yellow]")
        return False
    
    try:
        test_text = "这是一个流式语音合成测试，我会逐块返回音频数据。"
        
        console.print(f"合成文本: {test_text}")
        console.print("正在流式合成...")
        
        start_time = time.time()
        chunk_count = 0
        total_size = 0
        
        for chunk in tts_manager.synthesize_stream(test_text):
            chunk_count += 1
            total_size += len(chunk)
            console.print(f"  收到音频块 {chunk_count}: {len(chunk)} 字节")
        
        elapsed = time.time() - start_time
        
        if chunk_count > 0:
            console.print(f"\n[green]✓ 流式合成成功[/green]")
            console.print(f"  总音频块数: {chunk_count}")
            console.print(f"  总大小: {total_size} 字节")
            console.print(f"  耗时: {elapsed:.2f} 秒")
            return True
        else:
            console.print("[red]✗ 流式合成失败（无数据）[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ 流式合成失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_edge_tts_save_file(tts_manager):
    """测试Edge TTS保存到文件"""
    console.print("\n[bold cyan]测试 4: Edge TTS 保存到文件[/bold cyan]\n")
    
    if not tts_manager:
        console.print("[yellow]跳过测试（TTS管理器未初始化）[/yellow]")
        return False
    
    try:
        test_text = "测试保存到文件功能。"
        output_file = "test_output.mp3"
        
        console.print(f"合成文本: {test_text}")
        console.print(f"输出文件: {output_file}")
        console.print("正在合成...")
        
        start_time = time.time()
        success = tts_manager.synthesize_to_file(test_text, output_file)
        elapsed = time.time() - start_time
        
        if success:
            import os
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                console.print(f"[green]✓ 保存成功[/green]")
                console.print(f"  文件大小: {file_size} 字节")
                console.print(f"  耗时: {elapsed:.2f} 秒")
                
                # 清理测试文件
                try:
                    os.remove(output_file)
                    console.print(f"  已清理测试文件: {output_file}")
                except:
                    pass
                
                return True
            else:
                console.print("[red]✗ 文件未创建[/red]")
                return False
        else:
            console.print("[red]✗ 保存失败[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ 保存失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_tts_with_playback(tts_manager):
    """测试TTS合成并播放"""
    console.print("\n[bold cyan]测试 5: TTS 合成并播放[/bold cyan]\n")
    
    if not tts_manager:
        console.print("[yellow]跳过测试（TTS管理器未初始化）[/yellow]")
        return False
    
    try:
        from src.audio import AudioOutputHandler
        import io
        
        # 尝试导入音频处理库
        try:
            from pydub import AudioSegment
            from pydub.playback import play
            HAS_PYDUB = True
        except ImportError:
            HAS_PYDUB = False
            console.print("[yellow]未安装 pydub，跳过播放测试[/yellow]")
            console.print("[yellow]安装: pip install pydub[/yellow]")
            return False
        
        test_text = "你好，这是语音合成播放测试。"
        
        console.print(f"合成文本: {test_text}")
        console.print("正在合成...")
        
        audio_data = tts_manager.synthesize(test_text)
        
        if audio_data:
            console.print(f"[green]✓ 合成成功[/green] ({len(audio_data)} 字节)")
            console.print("正在播放...")
            
            # 播放音频
            try:
                audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                play(audio_segment)
                console.print("[green]✓ 播放完成[/green]")
                return True
            except Exception as e:
                console.print(f"[yellow]播放失败: {e}[/yellow]")
                console.print("[yellow]可能需要安装 ffmpeg[/yellow]")
                return False
        else:
            console.print("[red]✗ 合成失败[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold]TTS语音合成功能测试[/bold]\n"
        "测试Edge TTS引擎的各项功能",
        border_style="cyan"
    ))
    
    # 测试列表
    tests = []
    
    # 1. 初始化TTS管理器
    tts_manager = test_tts_manager()
    tests.append(("TTS管理器初始化", tts_manager is not None))
    
    if tts_manager:
        # 2. 基本合成测试
        result = test_edge_tts_basic(tts_manager)
        tests.append(("基本合成", result))
        
        # 3. 流式合成测试
        result = test_edge_tts_stream(tts_manager)
        tests.append(("流式合成", result))
        
        # 4. 保存文件测试
        result = test_edge_tts_save_file(tts_manager)
        tests.append(("保存文件", result))
        
        # 5. 合成并播放测试
        result = test_tts_with_playback(tts_manager)
        tests.append(("合成播放", result))
    
    # 显示总结
    console.print("\n" + "=" * 50)
    console.print("[bold]测试总结[/bold]")
    console.print("=" * 50)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "[green]✓ 通过[/green]" if result else "[red]✗ 失败[/red]"
        console.print(f"{name}: {status}")
    
    console.print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        console.print("[bold green]所有测试通过！[/bold green]")
    else:
        console.print("[bold yellow]部分测试失败[/bold yellow]")


if __name__ == "__main__":
    main()
