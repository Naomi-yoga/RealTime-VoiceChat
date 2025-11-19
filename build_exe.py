"""
打包脚本 - 使用 PyInstaller 将程序打包为独立exe

使用方法:
    python build_exe.py
"""
import os
import sys
import shutil
from pathlib import Path

# PyInstaller配置
APP_NAME = "RT-VoiceChat-CLI"
MAIN_SCRIPT = "src/main.py"
ICON_FILE = None  # 如果有图标文件，设置路径

# 依赖的数据文件
DATA_FILES = [
    ('config/default_config.yaml', 'config'),
    ('.env.example', '.'),
]


def build_exe():
    """构建exe文件"""
    print(f"开始打包 {APP_NAME}...")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("错误: 未找到 PyInstaller")
        print("请运行: pip install pyinstaller")
        sys.exit(1)
    
    # 构建命令
    cmd_parts = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",  # 单文件模式
        "--console",  # 控制台应用
        "--clean",    # 清理临时文件
    ]
    
    # 添加图标
    if ICON_FILE and Path(ICON_FILE).exists():
        cmd_parts.extend(["--icon", ICON_FILE])
    
    # 添加数据文件
    for src, dest in DATA_FILES:
        if Path(src).exists():
            cmd_parts.extend(["--add-data", f"{src};{dest}"])
    
    # 添加隐藏导入（解决一些动态导入问题）
    hidden_imports = [
        "yaml",
        "dotenv",
        "openai",
        "edge_tts",
        "faster_whisper",
        "rich",
        "click",
    ]
    for module in hidden_imports:
        cmd_parts.extend(["--hidden-import", module])
    
    # 主脚本
    cmd_parts.append(MAIN_SCRIPT)
    
    # 执行打包命令
    cmd = " ".join(cmd_parts)
    print(f"执行命令: {cmd}")
    
    result = os.system(cmd)
    
    if result == 0:
        print(f"\n✅ 打包成功!")
        print(f"可执行文件位置: dist/{APP_NAME}.exe")
        print(f"\n使用方法:")
        print(f"  1. 将 dist/{APP_NAME}.exe 复制到任意目录")
        print(f"  2. 在同一目录创建 .env 文件并配置API密钥")
        print(f"  3. 双击运行 {APP_NAME}.exe")
    else:
        print(f"\n❌ 打包失败，错误码: {result}")
        sys.exit(1)


def clean_build():
    """清理构建文件"""
    print("清理构建文件...")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = [f'{APP_NAME}.spec']
    
    for dir_name in dirs_to_remove:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  已删除: {dir_name}/")
    
    for file_name in files_to_remove:
        if Path(file_name).exists():
            os.remove(file_name)
            print(f"  已删除: {file_name}")
    
    print("清理完成")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="打包RT-VoiceChat-CLI为exe")
    parser.add_argument('--clean', action='store_true', help='清理构建文件')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    else:
        build_exe()
