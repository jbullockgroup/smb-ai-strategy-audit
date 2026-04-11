"""
Generation orchestrator for coordinating all document creation.

Manages the generation of all output formats (markdown, DOCX, PDF).
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from ..config import OUTPUT_DIR, DELIVERABLES
from ..models import (
    CompanyInput,
    ResearchOutput,
    SynthesisOutput,
    DeliverableContent,
    GenerationResult,
)

from .markdown_generator import MarkdownGenerator
from .docx_generator import DocxGenerator
from .pdf_generator import PDFGenerator


class GenerationOrchestrator:
    """
    Orchestrates the generation of all output deliverables.

    Responsibilities:
    - Save markdown files
    - Generate Word documents
    - Generate PDF strategy report
    - Track progress and handle errors
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        """
        Initialize the generation orchestrator.

        Args:
            output_dir: Base output directory.
            progress_callback: Callback for progress updates.
        """
        self.output_dir = output_dir or OUTPUT_DIR
        self.progress_callback = progress_callback

        # Initialize generators
        self.markdown_gen = MarkdownGenerator(output_dir=self.output_dir)
        self.docx_gen = DocxGenerator(output_dir=self.output_dir)
        self.pdf_gen = PDFGenerator(output_dir=self.output_dir)

        # Track results
        self.generated_files: Dict[str, str] = {}
        self.errors: List[Dict[str, Any]] = []

    def generate_all(
        self,
        company_slug: str,
        company_input: CompanyInput,
        research: ResearchOutput,
        synthesis: SynthesisOutput,
    ) -> GenerationResult:
        """
        Generate all output deliverables.

        Args:
            company_slug: URL-safe company name.
            company_input: Original company input.
            research: Research output.
            synthesis: Synthesis output.

        Returns:
            GenerationResult with all generated files.
        """
        start_time = datetime.now()
        total_steps = 3  # markdown, docx, pdf
        current_step = 0

        self._report_progress("Starting generation", 0)

        # Step 1: Save markdown files
        current_step += 1
        self._report_progress("Saving markdown files", current_step / total_steps)
        markdown_paths = self._save_markdown(company_slug, synthesis)
        self.generated_files.update(markdown_paths)

        # Step 2: Generate DOCX strategy report
        current_step += 1
        self._report_progress("Generating Word document", current_step / total_steps)
        docx_paths = self._generate_documents(
            company_slug, company_input, research, synthesis
        )
        self.generated_files.update(docx_paths)

        # Step 3: Generate PDF strategy report
        current_step += 1
        self._report_progress("Generating PDF report", current_step / total_steps)
        pdf_paths = self._generate_pdf(
            company_slug, company_input, research, synthesis
        )
        self.generated_files.update(pdf_paths)

        # Complete
        self._report_progress("Generation complete", 1.0)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Build result
        deliverables_list = [
            {
                "name": self._get_deliverable_name(key),
                "path": path,
                "format": self._get_format_from_path(path),
            }
            for key, path in self.generated_files.items()
        ]

        return GenerationResult(
            company_name=company_input.name,
            success=len(self.errors) == 0,
            output_dir=str(self.output_dir / company_slug),
            deliverables=deliverables_list,
            total_cost=synthesis.total_cost if synthesis else 0.0,
            generation_time=duration,
            errors=[e["error"] for e in self.errors],
        )

    def _save_markdown(
        self,
        company_slug: str,
        synthesis: SynthesisOutput,
    ) -> Dict[str, str]:
        """Save all markdown deliverables."""
        try:
            return self.markdown_gen.save_all(company_slug, synthesis)
        except Exception as e:
            self._record_error("markdown_generation", str(e))
            return {}

    def _generate_documents(
        self,
        company_slug: str,
        company_input: CompanyInput,
        research: ResearchOutput,
        synthesis: SynthesisOutput,
    ) -> Dict[str, str]:
        """Generate DOCX strategy report."""
        paths = {}

        try:
            report_path = self.docx_gen.generate_strategy_report(
                company_slug=company_slug,
                company_input=company_input,
                research=research,
                synthesis=synthesis,
            )
            paths["final_strategy_report"] = report_path
        except Exception as e:
            self._record_error("strategy_report_docx", str(e))

        return paths

    def _generate_pdf(
        self,
        company_slug: str,
        company_input: CompanyInput,
        research: ResearchOutput,
        synthesis: SynthesisOutput,
    ) -> Dict[str, str]:
        """Generate PDF strategy report."""
        paths = {}

        try:
            pdf_path = self.pdf_gen.generate_strategy_report(
                company_slug=company_slug,
                company_input=company_input,
                research=research,
                synthesis=synthesis,
            )
            paths["final_strategy_report_pdf"] = pdf_path
        except Exception as e:
            self._record_error("strategy_report_pdf", str(e))

        return paths

    def _get_deliverable_name(self, key: str) -> str:
        """Get human-readable name for a deliverable."""
        if key in DELIVERABLES:
            return DELIVERABLES[key]["name"]
        return key.replace("_", " ").title()

    def _get_format_from_path(self, path: str) -> str:
        """Get file format from path."""
        path = Path(path)
        suffix = path.suffix.lower()

        format_map = {
            ".md": "markdown",
            ".docx": "docx",
            ".pdf": "pdf",
        }

        return format_map.get(suffix, "unknown")

    def _record_error(self, component: str, error: str) -> None:
        """Record an error during generation."""
        self.errors.append({
            "component": component,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })

    def _report_progress(self, message: str, progress: float) -> None:
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def get_generated_files(self) -> Dict[str, str]:
        """Get all generated file paths."""
        return self.generated_files.copy()

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all errors that occurred during generation."""
        return self.errors.copy()


def run_generation(
    company_slug: str,
    company_input: CompanyInput,
    research: ResearchOutput,
    synthesis: SynthesisOutput,
    output_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> GenerationResult:
    """
    Convenience function to run all generation.

    Args:
        company_slug: URL-safe company name.
        company_input: Original company input.
        research: Research output.
        synthesis: Synthesis output.
        output_dir: Optional output directory.
        progress_callback: Optional progress callback.

    Returns:
        GenerationResult with all generated files.
    """
    orchestrator = GenerationOrchestrator(
        output_dir=output_dir,
        progress_callback=progress_callback,
    )

    return orchestrator.generate_all(
        company_slug=company_slug,
        company_input=company_input,
        research=research,
        synthesis=synthesis,
    )


def generate_outputs_from_synthesis(
    company_slug: str,
    company_input: CompanyInput,
    research: ResearchOutput,
    synthesis: SynthesisOutput,
    output_dir: Optional[Path] = None,
    skip_docx: bool = False,
) -> Dict[str, str]:
    """
    Generate specific outputs with fine-grained control.

    Args:
        company_slug: URL-safe company name.
        company_input: Original company input.
        research: Research output.
        synthesis: Synthesis output.
        output_dir: Optional output directory.
        skip_docx: Skip Word/PDF document generation.

    Returns:
        Dict mapping deliverable names to file paths.
    """
    base_dir = output_dir or OUTPUT_DIR
    generated = {}

    # Always save markdown
    md_gen = MarkdownGenerator(output_dir=base_dir)
    markdown_paths = md_gen.save_all(company_slug, synthesis)
    generated.update(markdown_paths)

    # Word and PDF documents
    if not skip_docx:
        docx_gen = DocxGenerator(output_dir=base_dir)
        try:
            report_path = docx_gen.generate_strategy_report(
                company_slug, company_input, research, synthesis
            )
            generated["final_strategy_report"] = report_path
        except Exception:
            pass

        pdf_gen = PDFGenerator(output_dir=base_dir)
        try:
            pdf_path = pdf_gen.generate_strategy_report(
                company_slug, company_input, research, synthesis
            )
            generated["final_strategy_report_pdf"] = pdf_path
        except Exception:
            pass

    return generated
