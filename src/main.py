"""RT-VoiceChat-CLI 主程序"""
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from .core import ConfigManager, ConversationManager
from .llm import LLMManager
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
            console.print("[yellow]语音模式尚未实现，使用文本模式[/yellow]")
            app.run_text_mode()
            
    except Exception as e:
        console.print(f"[red]程序启动失败: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
