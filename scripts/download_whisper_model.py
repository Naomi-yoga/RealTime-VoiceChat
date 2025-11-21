"""手动下载 Whisper 模型到项目目录"""
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Whisper 模型信息
MODELS = {
    'tiny': {
        'repo_id': 'guillaumekln/faster-whisper-tiny',
        'size': '~75 MB',
        'description': '最小模型，速度最快，准确度较低'
    },
    'base': {
        'repo_id': 'guillaumekln/faster-whisper-base',
        'size': '~150 MB',
        'description': '基础模型，速度快，准确度适中（推荐）'
    },
    'small': {
        'repo_id': 'guillaumekln/faster-whisper-small',
        'size': '~500 MB',
        'description': '小型模型，速度和准确度平衡'
    },
    'medium': {
        'repo_id': 'guillaumekln/faster-whisper-medium',
        'size': '~1.5 GB',
        'description': '中型模型，准确度高，速度较慢'
    },
    'large-v2': {
        'repo_id': 'guillaumekln/faster-whisper-large-v2',
        'size': '~3 GB',
        'description': '大型模型，准确度最高，速度最慢'
    }
}


def download_model(model_name: str, use_mirror: bool = False):
    """
    下载模型到项目目录
    
    Args:
        model_name: 模型名称
        use_mirror: 是否使用镜像
    """
    if model_name not in MODELS:
        console.print(f"[red]错误: 未知模型 '{model_name}'[/red]")
        console.print(f"[yellow]可用模型: {', '.join(MODELS.keys())}[/yellow]")
        return False
    
    model_info = MODELS[model_name]
    
    # 创建 models 目录（项目根目录下）
    project_root = Path(__file__).parent.parent  # 从 scripts/ 回到项目根目录
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)
    
    target_dir = models_dir / f"whisper-{model_name}"
    
    # 检查是否已存在
    if target_dir.exists():
        console.print(f"[yellow]模型已存在: {target_dir}[/yellow]")
        choice = console.input("是否重新下载? (y/N): ").strip().lower()
        if choice != 'y':
            console.print("[green]取消下载[/green]")
            return True
    
    console.print(f"\n[bold cyan]准备下载模型: {model_name}[/bold cyan]")
    console.print(f"描述: {model_info['description']}")
    console.print(f"大小: {model_info['size']}")
    console.print(f"目标目录: {target_dir}\n")
    
    # 设置镜像
    if use_mirror:
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        console.print("[cyan]使用镜像: https://hf-mirror.com[/cyan]\n")
    
    try:
        console.print("[yellow]开始下载...[/yellow]")
        
        # 下载模型
        snapshot_download(
            repo_id=model_info['repo_id'],
            local_dir=str(target_dir),
            local_dir_use_symlinks=False
        )
        
        console.print(f"\n[bold green]✓ 模型下载成功！[/bold green]")
        console.print(f"保存位置: {target_dir}")
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]✗ 下载失败: {e}[/bold red]")
        
        if not use_mirror:
            console.print("\n[yellow]提示: 可以尝试使用镜像下载[/yellow]")
            console.print("运行: python download_whisper_model.py --mirror")
        
        return False


def main():
    """主函数"""
    console.print("\n[bold]Whisper 模型下载工具[/bold]")
    console.print("=" * 50)
    
    # 检查依赖
    try:
        import huggingface_hub
    except ImportError:
        console.print("[red]错误: huggingface_hub 未安装[/red]")
        console.print("请运行: pip install huggingface_hub")
        return
    
    # 显示可用模型
    console.print("\n[bold]可用模型:[/bold]")
    for name, info in MODELS.items():
        console.print(f"  [{name:10}] {info['size']:8} - {info['description']}")
    
    # 获取用户选择
    console.print()
    model_name = console.input("请选择要下载的模型 [默认: base]: ").strip().lower()
    if not model_name:
        model_name = 'base'
    
    # 询问是否使用镜像
    use_mirror = False
    if '--mirror' in sys.argv or '-m' in sys.argv:
        use_mirror = True
    else:
        mirror_choice = console.input("是否使用国内镜像加速? (y/N): ").strip().lower()
        use_mirror = mirror_choice == 'y'
    
    # 下载模型
    success = download_model(model_name, use_mirror)
    
    if success:
        console.print("\n" + "=" * 50)
        console.print("[bold green]下载完成！[/bold green]")
        console.print("\n现在可以运行:")
        console.print("  python test_realtime_asr.py")
        console.print("\n程序会自动使用本地模型，无需网络连接。")
    else:
        console.print("\n[red]下载失败，请检查网络连接或使用镜像[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
