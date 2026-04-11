"""
Synthesis module for the AI Strategy Factory.

This module handles Gemini API interactions for content synthesis,
transforming research results into actionable deliverables using
consulting knowledge from TLDR guides.
"""

from .gemini_client import GeminiClient
from .context_builder import ContextBuilder
from .orchestrator import SynthesisOrchestrator

__all__ = [
    "GeminiClient",
    "ContextBuilder",
    "SynthesisOrchestrator",
]
