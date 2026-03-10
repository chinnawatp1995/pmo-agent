"""
Knowledge Module - API Interface
"""
from .routes import router, on_startup, on_shutdown

__all__ = ["router", "on_startup", "on_shutdown"]