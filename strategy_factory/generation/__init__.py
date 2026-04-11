"""
Generation module - Document creation (Markdown, DOCX, PDF).

This module handles the final generation phase, converting synthesized content
into polished deliverables in various formats.
"""

from .markdown_generator import MarkdownGenerator, save_markdown_deliverables
from .docx_generator import DocxGenerator, generate_strategy_report
from .pdf_generator import PDFGenerator
from .orchestrator import GenerationOrchestrator, run_generation

__all__ = [
    # Markdown
    "MarkdownGenerator",
    "save_markdown_deliverables",
    # Word
    "DocxGenerator",
    "generate_strategy_report",
    # PDF
    "PDFGenerator",
    # Orchestrator
    "GenerationOrchestrator",
    "run_generation",
]
