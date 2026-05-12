# файл: aic/ui/__init__.py
from aic.ui.main_window import AICApp
from aic.ui.panels import ControlPanel, ChatPanel, LogPanel
from aic.ui.timer_display import TimerDisplay

__all__ = ['AICApp', 'ControlPanel', 'ChatPanel', 'LogPanel', 'TimerDisplay']
