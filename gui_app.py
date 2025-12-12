import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
from pathlib import Path
import ollama
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.core.engine import AgentEngine
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.utils.config import load_config

class TextHandler:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

class DigitalHumainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Humain - Desktop Automation")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.load_models()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Model Selection
        model_frame = ttk.LabelFrame(main_frame, text="LLM Configuration", padding="5")
        model_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model_frame, text="Select Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly")
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(model_frame, text="Refresh Models", command=self.load_models).pack(side=tk.LEFT, padx=5)
        
        # Task Input
        task_frame = ttk.LabelFrame(main_frame, text="Task", padding="5")
        task_frame.pack(fill=tk.X, pady=5)
        
        self.task_text = tk.Text(task_frame, height=4, width=50)
        self.task_text.pack(fill=tk.X, padx=5, pady=5)
        self.task_text.insert("1.0", "Go to notepad and write a letter to Steve Jobs in 10 words")
        
        # Controls
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = ttk.Button(control_frame, text="Run Task", command=self.start_task)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Logs
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=20)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Redirect logger
        logger.remove()
        logger.add(TextHandler(self.log_area), format="{time:HH:mm:ss} | {level} | {message}")

    def load_models(self):
        try:
            response = ollama.list()
            # Handle both object and dict response types just in case
            if hasattr(response, 'models'):
                model_names = [m.model for m in response.models]
            else:
                model_names = [m['model'] for m in response['models']]
                
            self.model_combo['values'] = model_names
            if model_names:
                # Default to deepseek-r1:1.5b if available, else first one
                default_model = "deepseek-r1:1.5b"
                if default_model in model_names:
                    self.model_combo.set(default_model)
                else:
                    self.model_combo.set(model_names[0])
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.model_combo['values'] = ["Error loading models"]

    def clear_logs(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')

    def start_task(self):
        task = self.task_text.get("1.0", tk.END).strip()
        model = self.model_var.get()
        
        if not task:
            logger.warning("Please enter a task")
            return
            
        if not model:
            logger.warning("Please select a model")
            return
            
        self.run_btn.configure(state='disabled')
        threading.Thread(target=self.run_agent, args=(task, model), daemon=True).start()

    def run_agent(self, task, model):
        try:
            logger.info(f"Starting task with model: {model}")
            
            # Initialize components
            config = load_config()
            
            llm = OllamaProvider(
                model=model,
                base_url=config.get("llm", {}).get("base_url", "http://localhost:11434"),
                timeout=config.get("llm", {}).get("timeout", 300)
            )
            
            screen_analyzer = ScreenAnalyzer(
                save_screenshots=True,
                screenshot_dir="./screenshots"
            )
            
            gui_actions = GUIActions(pause=1.0)  # Slower for safety
            
            tool_registry = ToolRegistry()
            tool_registry.register(FileReadTool())
            tool_registry.register(FileWriteTool())
            
            agent_config = AgentConfig(
                name="gui_agent",
                role=AgentRole.EXECUTOR,
                model=model,
                max_iterations=15
            )
            
            agent = DesktopAutomationAgent(
                config=agent_config,
                llm_provider=llm,
                screen_analyzer=screen_analyzer,
                gui_actions=gui_actions,
                tool_registry=tool_registry
            )
            
            engine = AgentEngine(agent)
            engine.build_graph()
            
            result = engine.run(task)
            
            if result['error']:
                logger.error(f"Task failed: {result['error']}")
            else:
                logger.success("Task completed successfully!")
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state='normal'))

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalHumainGUI(root)
    root.mainloop()
