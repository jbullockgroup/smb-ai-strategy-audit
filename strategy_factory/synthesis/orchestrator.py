"""
Synthesis orchestrator for managing deliverable generation.

Coordinates the generation of all deliverables in dependency order,
manages context building, and tracks progress.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from ..config import DELIVERABLES, OUTPUT_DIR
from ..models import (
    CompanyInput,
    ResearchOutput,
    DeliverableContent,
    SynthesisOutput,
    DeliverableStatus,
)
from ..knowledge_loader import KnowledgeLoader
from ..temporal import get_temporal_context
from .gemini_client import GeminiClient
from .context_builder import ContextBuilder
from .prompts import get_prompt, PROMPTS


class SynthesisOrchestrator:
    """
    Orchestrates the synthesis of all deliverables.
    
    Responsibilities:
    - Determine generation order based on dependencies
    - Build context for each deliverable
    - Generate content using Gemini
    - Track progress and handle failures
    """
    
    # Dependency levels for ordering
    GENERATION_ORDER = [
        ["01_tools_audit", "02_daily_pain_points"],
        ["05_readiness_assessment", "03_action_plan"],
        ["04_simple_roadmap", "06_roi_snapshot"],
        ["07_closing"],
        ["08_executive_summary"],
    ]
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        """
        Initialize the synthesis orchestrator.
        
        Args:
            output_dir: Directory for output files.
            progress_callback: Callback for progress updates.
        """
        self.output_dir = output_dir or OUTPUT_DIR
        self.progress_callback = progress_callback
        
        # Initialize components
        self.gemini_client = GeminiClient()
        self.knowledge_loader = KnowledgeLoader()
        self.context_builder = ContextBuilder(
            knowledge_loader=self.knowledge_loader,
            temporal=get_temporal_context(),
        )
        
        # Track state
        self.generated_content: Dict[str, DeliverableContent] = {}
        self.errors: List[Dict[str, Any]] = []
    
    def synthesize(
        self,
        company_input: CompanyInput,
        research: ResearchOutput,
        deliverables: Optional[List[str]] = None,
    ) -> SynthesisOutput:
        """
        Synthesize all deliverables for a company.
        
        Args:
            company_input: Company input data.
            research: Research output from Perplexity.
            deliverables: Optional list of specific deliverables to generate.
                         If None, generates all markdown deliverables.
        
        Returns:
            SynthesisOutput with all generated content.
        """
        # Determine which deliverables to generate
        if deliverables:
            target_deliverables = deliverables
        else:
            # Default to all markdown deliverables
            target_deliverables = [
                d_id for d_id, config in DELIVERABLES.items()
                if config.get("format") == "markdown"
            ]
        
        # Calculate total steps for progress
        total_steps = len(target_deliverables)
        completed_steps = 0
        
        self._report_progress("Starting synthesis", 0)
        
        # Generate in dependency order
        for level_index, level in enumerate(self.GENERATION_ORDER):
            level_deliverables = [d for d in level if d in target_deliverables]
            
            for deliverable_id in level_deliverables:
                self._report_progress(
                    f"Generating {deliverable_id}",
                    completed_steps / total_steps
                )
                
                # Check if dependencies are met
                if not self._check_dependencies(deliverable_id):
                    self._record_error(
                        deliverable_id,
                        "Dependencies not met"
                    )
                    continue
                
                # Generate deliverable (one retry on truncation/validation failure)
                content = self._generate_deliverable(
                    deliverable_id,
                    company_input,
                    research,
                )
                if content and content.error:
                    print(f"  Retrying {deliverable_id}: {content.error}")
                    content = self._generate_deliverable(
                        deliverable_id,
                        company_input,
                        research,
                    )

                if content and not content.error:
                    self.generated_content[deliverable_id] = content
                    # Register for dependency tracking
                    self.context_builder.register_deliverable(
                        deliverable_id,
                        content.content
                    )
                else:
                    self._record_error(
                        deliverable_id,
                        content.error if content else "Unknown error"
                    )
                
                completed_steps += 1
        
        self._report_progress("Synthesis complete", 1.0)
        
        # Build output
        return SynthesisOutput(
            company_name=company_input.name,
            synthesis_timestamp=datetime.now(),
            deliverables=self.generated_content,
            total_cost=self.gemini_client.total_cost,
        )
    
    def _generate_deliverable(
        self,
        deliverable_id: str,
        company_input: CompanyInput,
        research: ResearchOutput,
    ) -> Optional[DeliverableContent]:
        """
        Generate a single deliverable.
        
        Args:
            deliverable_id: ID of the deliverable.
            company_input: Company input.
            research: Research output.
        
        Returns:
            DeliverableContent or None if failed.
        """
        deliverable_config = DELIVERABLES.get(deliverable_id, {})
        
        # Get prompt template
        prompt_template = get_prompt(deliverable_id)
        if not prompt_template:
            return DeliverableContent(
                deliverable_id=deliverable_id,
                name=deliverable_config.get("name", deliverable_id),
                format="markdown",
                error=f"No prompt template found for {deliverable_id}",
            )
        
        # Build full prompt with context
        full_prompt = self.context_builder.build_full_prompt(
            deliverable_id=deliverable_id,
            prompt_template=prompt_template,
            research=research,
            company_input=company_input,
        )
        
        # Generate content
        result = self.gemini_client.generate_markdown(
            prompt=full_prompt,
            system_instruction=self._get_system_instruction(deliverable_id),
        )
        
        if result.error:
            return DeliverableContent(
                deliverable_id=deliverable_id,
                name=deliverable_config.get("name", deliverable_id),
                format="markdown",
                error=result.error,
            )

        if result.content and "SUMMARY:" not in result.content:
            return DeliverableContent(
                deliverable_id=deliverable_id,
                name=deliverable_config.get("name", deliverable_id),
                format="markdown",
                error="Missing SUMMARY line — output likely truncated",
            )

        return DeliverableContent(
            deliverable_id=deliverable_id,
            name=deliverable_config.get("name", deliverable_id),
            format="markdown",
            content=result.content,
            generated_at=result.timestamp,
            synthesis_cost=result.cost_estimate,
        )
    
    def _get_system_instruction(self, deliverable_id: str) -> str:
        """Get system instruction for a deliverable."""
        return """
You are an AI adoption coach creating practical, plain-English strategy reports for small business owners.

Guidelines:
- Write like you're explaining to a smart friend who isn't technical
- Be specific with tool names and prices (ChatGPT Plus $20/mo, Claude Pro $20/mo, Perplexity Pro $20/mo, Gemini free/$20/mo)
- If the business could only do ONE thing: recommend Claude Cowork (Max plan, $100-200/mo) — it's an agentic AI that handles multi-step work autonomously, perfect for non-technical owners
- Focus on what to DO, not frameworks or models
- Never recommend: Make.com, Zapier, complex automation platforms, anything requiring API knowledge
- Prefer: n8n for automation (if technical help available), native integrations in existing tools
- Use concrete examples: "Instead of spending 3 hours on proposals, spend 30 minutes"
- Total budget awareness: most clients are $150K-$2.5M revenue, owner-operated
- NO enterprise jargon, NO maturity models, NO governance frameworks
- Professional but accessible - this should read like expert advice, not a blog post
"""
    
    def _check_dependencies(self, deliverable_id: str) -> bool:
        """Check if all dependencies for a deliverable are met."""
        deliverable_config = DELIVERABLES.get(deliverable_id, {})
        dependencies = deliverable_config.get("dependencies", [])
        
        for dep in dependencies:
            if dep == "ALL_MARKDOWN":
                # Skip this check for final deliverables
                continue
            if dep not in self.generated_content:
                return False
        
        return True
    
    def _record_error(self, deliverable_id: str, error: str) -> None:
        """Record an error during generation."""
        self.errors.append({
            "deliverable_id": deliverable_id,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })
    
    def _report_progress(self, message: str, progress: float) -> None:
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def save_deliverables(
        self,
        company_slug: str,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, str]:
        """
        Save all generated deliverables to disk.
        
        Args:
            company_slug: URL-safe company name.
            output_dir: Optional output directory override.
        
        Returns:
            Dict mapping deliverable_id to file path.
        """
        base_dir = output_dir or self.output_dir
        company_dir = base_dir / company_slug / "markdown"
        company_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        
        for deliverable_id, content in self.generated_content.items():
            if content.content:
                file_name = f"{deliverable_id}.md"
                file_path = company_dir / file_name
                
                with open(file_path, "w") as f:
                    f.write(content.content)
                
                file_paths[deliverable_id] = str(file_path)
                content.file_path = str(file_path)
        
        return file_paths
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for synthesis."""
        return self.gemini_client.get_cost_summary()
    
    def get_generation_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all deliverables."""
        status = {}
        
        for d_id in DELIVERABLES:
            if d_id in self.generated_content:
                content = self.generated_content[d_id]
                status[d_id] = {
                    "status": "completed" if not content.error else "failed",
                    "error": content.error,
                    "cost": content.synthesis_cost,
                    "file_path": content.file_path,
                }
            else:
                # Check if it has an error
                error = next(
                    (e for e in self.errors if e["deliverable_id"] == d_id),
                    None
                )
                status[d_id] = {
                    "status": "failed" if error else "pending",
                    "error": error["error"] if error else None,
                }
        
        return status


def run_synthesis(
    company_input: CompanyInput,
    research: ResearchOutput,
    output_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> SynthesisOutput:
    """
    Convenience function to run synthesis.
    
    Args:
        company_input: Company input.
        research: Research output.
        output_dir: Output directory.
        progress_callback: Progress callback.
    
    Returns:
        SynthesisOutput with generated deliverables.
    """
    orchestrator = SynthesisOrchestrator(
        output_dir=output_dir,
        progress_callback=progress_callback,
    )
    
    return orchestrator.synthesize(company_input, research)
