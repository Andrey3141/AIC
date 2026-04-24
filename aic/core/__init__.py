# файл: aic/core/__init__.py
from aic.core.browser_manager import BrowserManager
from aic.core.message_handler import MessageHandler, MessageSnapshot
from aic.core.timer import Timer

__all__ = ['BrowserManager', 'MessageHandler', 'MessageSnapshot', 'Timer']
