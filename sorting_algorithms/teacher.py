"""The step builder moved to the top level in Phase 5, so searching could
share it rather than keep a second copy. This re-export keeps the six sorting
modules importing `from .teacher import step` exactly as they did.
"""
from teacher import step

__all__ = ['step']
