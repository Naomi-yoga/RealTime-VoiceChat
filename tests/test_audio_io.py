"""音频输入输出测试"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def test_audio_devices():
    """测试音频设备枚举"""
    console.print("\n[bold cyan]测试 1: 音频设备枚举[/bold cyan]\n")
    
    try:
        from src.audio import AudioInputHandler, AudioOutputHandler
        
        # 测试输入设备
        console.print("[bold]输入设备:[/bold]")
        audio_input = AudioInputHandler()
        input_devices = audio_input.list_devices()
        
        if input_devices:
            for device in input_devices:
                console.print(
                    f"  [{device['index']}] {device['name']} "
                    f"({device['channels']} ch, {device['sample_rate']} Hz)"
                )
        else:
            console.print("  [yellow]未找到输入设备[/yellow]")
        
        # 测试输出设备
        console.print("\n[bold]输出设备:[/bold]")
        audio_output = AudioOutputHandler()
        output_devices = audio_output.list_devices()
        
        if output_devices:
            for device in output_devices:
                console.print(
                    f"  [{device['index']}] {device['name']} "
                    f"({device['channels']} ch, {device['sample_rate']} Hz)"
                )
        else:
            console.print("  [yellow]未找到输出设备[/yellow]")
        
        console.print("\n[green]✓ 设备枚举测试通过[/green]")
        return True
        
    except ImportError as e:
        console.print(f"[red]✗ 导入失败: {e}[/red]")
        console.print("[yellow]请安装 PyAudio: pip install pyaudio[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        return False


def test_audio_recording():
    """测试音频录制"""
    console.print("\n[bold cyan]测试 2: 音频录制[/bold cyan]\n")
    
    try:
        from src.audio import AudioInputHandler
        import numpy as np
        
        console.print("准备录制 3 秒音频...")
        audio_input = AudioInputHandler(sample_rate=16000, chunk_size=1600)
        
        # 启动录音
        audio_input.start()
        console.print("[green]● 录音中...[/green] (请说话)")
        
        chunks = []
        max_level = 0.0
        
        # 录制 3 秒
        for i in range(30):  # 3秒，每次100ms
            chunk = audio_input.read(timeout=0.2)
            if chunk:
                chunks.append(chunk)
                level = audio_input.get_audio_level(chunk)
                max_level = max(max_level, level)
                
                # 显示音频电平
                bars = int(level * 50)
                console.print(f"\r音频电平: {'█' * bars}", end="")
            time.sleep(0.1)
        
        console.print()  # 换行
        
        # 停止录音
        audio_input.stop()
        
        console.print(f"\n[green]✓ 录制完成[/green]")
        console.print(f"  总块数: {len(chunks)}")
        console.print(f"  最大电平: {max_level:.3f}")
        console.print(f"  总时长: ~{len(chunks) * 0.1:.1f}秒")
        
        return True
        
    except ImportError as e:
        console.print(f"[red]✗ 导入失败: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_audio_playback():
    """测试音频播放"""
    console.print("\n[bold cyan]测试 3: 音频播放[/bold cyan]\n")
    
    try:
        from src.audio import AudioOutputHandler
        import numpy as np
        
        console.print("生成测试音频...")
        
        # 生成一个简单的正弦波音频（440Hz，A音）
        sample_rate = 16000
        duration = 2.0  # 秒
        frequency = 440  # Hz
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # 转换为 int16 格式
        audio_data = (audio_data * 32767).astype(np.int16)
        audio_bytes = audio_data.tobytes()
        
        console.print(f"播放 {duration} 秒 {frequency}Hz 正弦波...")
        
        # 播放音频
        audio_output = AudioOutputHandler(sample_rate=sample_rate)
        audio_output.play_sync(audio_bytes)
        
        console.print("[green]✓ 播放完成[/green]")
        return True
        
    except ImportError as e:
        console.print(f"[red]✗ 导入失败: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_record_and_playback():
    """测试录音并回放"""
    console.print("\n[bold cyan]测试 4: 录音并回放[/bold cyan]\n")
    
    try:
        from src.audio import AudioInputHandler, AudioOutputHandler
        
        console.print("录制 3 秒音频...")
        audio_input = AudioInputHandler(sample_rate=16000, chunk_size=1600)
        
        # 录音
        audio_input.start()
        console.print("[green]● 录音中...[/green] (请说话)")
        
        chunks = []
        for i in range(30):
            chunk = audio_input.read(timeout=0.2)
            if chunk:
                chunks.append(chunk)
            time.sleep(0.1)
        
        audio_input.stop()
        console.print("[green]✓ 录制完成[/green]")
        
        # 合并所有音频块
        audio_data = b''.join(chunks)
        
        console.print("\n播放录制的音频...")
        audio_output = AudioOutputHandler(sample_rate=16000)
        audio_output.play_sync(audio_data)
        
        console.print("[green]✓ 回放完成[/green]")
        return True
        
    except ImportError as e:
        console.print(f"[red]✗ 导入失败: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold]音频输入输出功能测试[/bold]\n"
        "测试 PyAudio 音频处理器的功能",
        border_style="cyan"
    ))
    
    tests = [
        ("设备枚举", test_audio_devices),
        ("音频录制", test_audio_recording),
        ("音频播放", test_audio_playback),
        ("录音回放", test_record_and_playback),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            console.print("\n\n[yellow]测试被中断[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]测试出错: {e}[/red]")
            results.append((name, False))
    
    # 显示总结
    console.print("\n" + "=" * 50)
    console.print("[bold]测试总结[/bold]")
    console.print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[green]✓ 通过[/green]" if result else "[red]✗ 失败[/red]"
        console.print(f"{name}: {status}")
    
    console.print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        console.print("[bold green]所有测试通过！[/bold green]")
    else:
        console.print("[bold yellow]部分测试失败[/bold yellow]")


if __name__ == "__main__":
    main()
