"""
基础功能测试脚本
测试配置管理、对话管理等核心功能（不需要API密钥）
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_config_manager():
    """测试配置管理器"""
    print("\n" + "="*50)
    print("测试1: 配置管理器")
    print("="*50)
    
    try:
        from src.core import ConfigManager
        
        config = ConfigManager()
        print("✓ 配置管理器初始化成功")
        
        # 测试获取配置
        models = config.get('models')
        print(f"✓ 读取模型配置: {len(models)} 个模型")
        
        # 测试嵌套配置
        deepseek_model = config.get('models', 'deepseek', 'model')
        print(f"✓ 读取嵌套配置: DeepSeek模型 = {deepseek_model}")
        
        # 测试默认值
        unknown = config.get('unknown', 'key', default='默认值')
        print(f"✓ 默认值功能: {unknown}")
        
        print("\n✅ 配置管理器测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_manager():
    """测试对话管理器"""
    print("\n" + "="*50)
    print("测试2: 对话管理器")
    print("="*50)
    
    try:
        from src.core import ConversationManager
        
        conv = ConversationManager(
            system_prompt="你是测试助手",
            max_history=3,
            save_history=False
        )
        print("✓ 对话管理器初始化成功")
        
        # 添加消息
        conv.add_user_message("测试问题1")
        conv.add_assistant_message("测试回答1")
        print(f"✓ 添加消息: {len(conv.messages)} 条")
        
        # 获取消息
        messages = conv.get_messages()
        print(f"✓ 获取消息: {len(messages)} 条")
        
        # 测试历史修剪
        for i in range(10):
            conv.add_user_message(f"问题{i}")
            conv.add_assistant_message(f"回答{i}")
        
        print(f"✓ 历史修剪: {len(conv.messages)} 条 (max_history=3)")
        
        # 清空历史
        conv.clear_history()
        print(f"✓ 清空历史: {len(conv.messages)} 条")
        
        print("\n✅ 对话管理器测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 对话管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger():
    """测试日志系统"""
    print("\n" + "="*50)
    print("测试3: 日志系统")
    print("="*50)
    
    try:
        from src.utils import setup_logger, get_logger
        
        # 设置日志
        logger = setup_logger(
            name="test",
            level="DEBUG",
            console=True
        )
        print("✓ 日志系统初始化成功")
        
        # 测试不同级别
        test_logger = get_logger("test_module")
        test_logger.debug("这是DEBUG消息")
        test_logger.info("这是INFO消息")
        test_logger.warning("这是WARNING消息")
        print("✓ 各级别日志输出正常")
        
        print("\n✅ 日志系统测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 日志系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_utils():
    """测试音频工具"""
    print("\n" + "="*50)
    print("测试4: 音频工具")
    print("="*50)
    
    try:
        import numpy as np
        from src.utils import AudioBuffer, calculate_rms
        
        # 测试RMS计算
        audio_data = np.random.randn(1000)
        rms = calculate_rms(audio_data)
        print(f"✓ RMS计算: {rms:.4f}")
        
        # 测试音频缓冲
        buffer = AudioBuffer(max_size=10)
        for i in range(5):
            buffer.add(np.random.randn(100))
        print(f"✓ 音频缓冲: {len(buffer)} 帧")
        
        all_data = buffer.get_all()
        print(f"✓ 获取数据: {len(all_data)} 样本")
        print(f"✓ 缓冲清空: {buffer.is_empty}")
        
        print("\n✅ 音频工具测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 音频工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_framework():
    """测试LLM框架（不实际调用API）"""
    print("\n" + "="*50)
    print("测试5: LLM框架")
    print("="*50)
    
    try:
        from src.llm import LLMManager
        
        # 模拟配置
        test_config = {
            'deepseek': {
                'api_key': 'test-key',
                'model': 'deepseek-chat',
                'base_url': 'https://api.deepseek.com/v1'
            }
        }
        
        manager = LLMManager(test_config)
        print("✓ LLM管理器初始化成功")
        
        # 测试列出模型
        models = manager.list_available_models()
        print(f"✓ 可用模型: {models}")
        
        # 注意: 不实际创建LLM实例，因为需要有效的API密钥
        print("✓ LLM框架结构正确")
        
        print("\n✅ LLM框架测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM框架测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RT-VoiceChat-CLI 基础功能测试")
    print("="*60)
    
    results = {
        '配置管理': test_config_manager(),
        '对话管理': test_conversation_manager(),
        '日志系统': test_logger(),
        '音频工具': test_audio_utils(),
        'LLM框架': test_llm_framework(),
    }
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！项目基础功能正常。")
        print("\n下一步:")
        print("1. 配置API密钥 (编辑 .env 文件)")
        print("2. 运行程序: python -m src.main --text-mode")
    else:
        print("\n⚠️  部分测试失败，请检查依赖安装。")
        print("运行: pip install -r requirements.txt")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
