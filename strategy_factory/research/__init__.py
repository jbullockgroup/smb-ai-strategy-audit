"""
Research module for the AI Strategy Factory.

This module handles all Perplexity API interactions for company research,
including:
- Company profile research
- Industry analysis
- Technology landscape mapping
"""

from .perplexity_client import PerplexityClient
from .query_templates import QueryTemplates
from .orchestrator import ResearchOrchestrator
from .result_processor import ResultProcessor

__all__ = [
    "PerplexityClient",
    "QueryTemplates",
    "ResearchOrchestrator",
    "ResultProcessor",
]
