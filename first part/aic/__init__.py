# файл: aic/__init__.py
"""
AIC - Artificial Intelligence Company
Четырёхэтапная система для работы с DeepSeek
"""

__version__ = "10.1.0"
__author__ = "AIC Team"

from aic.models.config import Config
from aic.core.browser_manager import BrowserManager
from aic.core.message_handler import MessageHandler
from aic.core.timer import Timer
from aic.ui.main_window import AICApp

__all__ = [
    'Config',
    'BrowserManager', 
    'MessageHandler',
    'Timer',
    'AICApp'
]
