"""
Knowledge Module - Interfaces Layer
"""
from .api import router, on_startup, on_shutdown

__all__ = ["router", "on_startup", "on_shutdown"]