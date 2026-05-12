import logging
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.traceback import install
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
from rich.table import Table
from rich import box
import sys

# Install rich traceback for better error display
install(show_locals=True, width=120, word_wrap=True)

# Custom theme for beautiful colors
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "debug": "dim blue",
    "download": "bright_blue",
    "process": "magenta",
    "file": "green",
    "url": "bright_cyan underline",
    "time": "dim white",
})

console = Console(theme=CUSTOM_THEME)

class BeautifulLogger:
    """Main logger class for the application"""
    
    def __init__(self, name, log_file=None, level=logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rich console handler
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
            log_time_format="[%Y-%m-%d %H:%M:%S]"
        )
        rich_handler.setLevel(level)
        
        # Format without extra timestamp (Rich adds its own)
        formatter = logging.Formatter('%(message)s')
        rich_handler.setFormatter(formatter)
        self.logger.addHandler(rich_handler)
        
        # Optional file handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(exist_ok=True, parents=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def _log(self, level, message, emoji="", color="", *args, **kwargs):
        """Internal log method with formatting"""
        if emoji:
            message = f"{emoji} {message}"
        if color:
            message = f"[{color}]{message}[/{color}]"
        
        getattr(self.logger, level)(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        self._log("info", message, *args, **kwargs)
    
    def debug(self, message, *args, **kwargs):
        self._log("debug", message, "🔍", "dim blue", *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._log("warning", message, "⚠️", "yellow", *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._log("error", message, "❌", "bold red", *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._log("critical", message, "💀", "bold white on red", *args, **kwargs)
    
    def success(self, message, *args, **kwargs):
        self._log("info", message, "✅", "bold green", *args, **kwargs)
    
    def download(self, message, *args, **kwargs):
        self._log("info", message, "📥", "bright_blue", *args, **kwargs)
    
    def process(self, message, *args, **kwargs):
        self._log("info", message, "⚙️", "magenta", *args, **kwargs)
    
    def file(self, message, *args, **kwargs):
        self._log("info", message, "📄", "green", *args, **kwargs)
    
    def url(self, message, *args, **kwargs):
        self._log("info", message, "🔗", "bright_cyan underline", *args, **kwargs)
    
    def section(self, title, emoji="📦"):
        """Print a beautiful section header"""
        panel = Panel(
            f"[bold cyan]{emoji} {title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
    
    def rule(self, title=None):
        """Print a horizontal rule"""
        console.rule(title, style="cyan")
    
    def create_progress(self, description="Downloading"):
        """Create a progress bar for downloads"""
        return Progress(
            TextColumn(f"[bold blue]{description}[/bold blue]"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False
        )
    
    def print_table(self, title, columns, rows):
        """Print a formatted table"""
        table = Table(title=title, box=box.ROUNDED, header_style="bold cyan")
        for col in columns:
            table.add_column(col)
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        console.print(table)
    
    def print_dict(self, data, title=None):
        """Print a dictionary as a formatted table"""
        if title:
            console.print(f"\n[bold cyan]{title}[/bold cyan]")
        
        table = Table(box=box.MINIMAL, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        console.print(table)
    
    def status(self, message, status="info"):
        """Print a status message with colored prefix"""
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        color = colors.get(status, "white")
        console.print(f"[{color}]●[/{color}] {message}")

# Factory functions for different components
def get_downloader_logger():
    return BeautifulLogger(
        "Downloader",
        log_file="logs/downloader.log",
        level=logging.DEBUG
    )

def get_ffmpeg_logger():
    return BeautifulLogger(
        "FFmpeg",
        log_file="logs/ffmpeg.log",
        level=logging.DEBUG
    )

def get_main_logger():
    return BeautifulLogger(
        "Main",
        log_file="logs/main.log",
        level=logging.INFO
    )