"""
Progress tracking and state management for the AI Strategy Factory.

Handles:
- Creating and loading pipeline state from state.json
- Tracking deliverable progress
- Enabling session resumability
- Generating phase summaries
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .models import (
    PipelineState,
    CompanyInput,
    DeliverableProgress,
    PhaseProgress,
    DeliverableStatus,
    ResearchOutput,
)
from .config import OUTPUT_DIR, DELIVERABLES

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: Text to convert

    Returns:
        Lowercase, hyphenated slug
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


class ProgressTracker:
    """
    Manages pipeline state and progress tracking.

    Usage:
        tracker = ProgressTracker("Acme Corp", company_input)
        tracker.start_phase("research")
        tracker.update_deliverable("01_tech_inventory", DeliverableStatus.IN_PROGRESS)
        tracker.complete_deliverable("01_tech_inventory", "/path/to/file.md")
        tracker.complete_phase("research", "Completed research with 15 queries...")
    """

    def __init__(
        self,
        company_name: str,
        company_input: Optional[CompanyInput] = None,
        output_base: Path = OUTPUT_DIR
    ):
        """
        Initialize progress tracker.

        Args:
            company_name: Name of the company
            company_input: Optional CompanyInput model with full input data
            output_base: Base directory for outputs (default: output/)
        """
        self.company_name = company_name
        self.company_slug = slugify(company_name)
        self.output_base = Path(output_base)
        self.output_dir = self.output_base / self.company_slug
        self.state_file = self.output_dir / "state.json"
        self.research_cache_file = self.output_dir / "research_cache.json"

        # Load existing state or create new
        if self.state_file.exists():
            self.state = self._load_state()
            # Use the proper company name from state, not the slug
            if self.state.company_name:
                self.company_name = self.state.company_name
            logger.info(f"Loaded existing state for {self.company_name}")
        else:
            self.state = self._create_state(company_input)
            logger.info(f"Created new state for {company_name}")

    def _create_state(self, company_input: Optional[CompanyInput]) -> PipelineState:
        """Create a new pipeline state."""
        # Create output directory structure
        self._ensure_directories()

        # Initialize deliverable progress
        deliverables = {}
        for deliverable_id in DELIVERABLES.keys():
            deliverables[deliverable_id] = DeliverableProgress()

        # Initialize phase progress
        phases = {
            "research": PhaseProgress(name="Research"),
            "synthesis": PhaseProgress(name="Synthesis"),
            "generation": PhaseProgress(name="Document Generation"),
        }

        # Create default input if none provided
        if company_input is None:
            company_input = CompanyInput(name=self.company_name)

        state = PipelineState(
            company_name=self.company_name,
            company_slug=self.company_slug,
            output_dir=str(self.output_dir),
            input_data=company_input,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            phases=phases,
            deliverables=deliverables,
        )

        self._save_state(state)
        return state

    def _load_state(self) -> PipelineState:
        """Load existing state from file."""
        with open(self.state_file, 'r') as f:
            data = json.load(f)
        return PipelineState(**data)

    def _save_state(self, state: Optional[PipelineState] = None):
        """Save state to file."""
        if state is None:
            state = self.state
        state.updated_at = datetime.now()

        with open(self.state_file, 'w') as f:
            f.write(state.model_dump_json(indent=2))

    def _ensure_directories(self):
        """Create output directory structure."""
        dirs = [
            self.output_dir,
            self.output_dir / "markdown",
            self.output_dir / "documents",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # Phase Management
    # ========================================================================

    def start_phase(self, phase_name: str):
        """Mark a phase as started."""
        if phase_name in self.state.phases:
            self.state.phases[phase_name].status = DeliverableStatus.IN_PROGRESS
            self.state.phases[phase_name].started_at = datetime.now()
            self.state.current_phase = phase_name
            self._save_state()
            logger.info(f"Started phase: {phase_name}")

    def complete_phase(self, phase_name: str, summary: str = ""):
        """Mark a phase as completed with summary."""
        if phase_name in self.state.phases:
            self.state.phases[phase_name].status = DeliverableStatus.COMPLETED
            self.state.phases[phase_name].completed_at = datetime.now()
            self.state.phases[phase_name].summary = summary
            self._save_state()

            # Write phase summary to file
            summary_file = self.output_dir / f"phase_{phase_name}_summary.md"
            self._write_phase_summary(phase_name, summary, summary_file)
            logger.info(f"Completed phase: {phase_name}")

    def fail_phase(self, phase_name: str, error: str):
        """Mark a phase as failed."""
        if phase_name in self.state.phases:
            self.state.phases[phase_name].status = DeliverableStatus.FAILED
            self.state.errors.append({
                "phase": phase_name,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
            self._save_state()
            logger.error(f"Phase {phase_name} failed: {error}")

    def _write_phase_summary(self, phase_name: str, summary: str, file_path: Path):
        """Write phase summary to markdown file."""
        phase = self.state.phases[phase_name]
        content = f"""# Phase Summary: {phase.name}

**Company:** {self.company_name}
**Status:** {phase.status.value}
**Started:** {phase.started_at.strftime('%Y-%m-%d %H:%M:%S') if phase.started_at else 'N/A'}
**Completed:** {phase.completed_at.strftime('%Y-%m-%d %H:%M:%S') if phase.completed_at else 'N/A'}

## Summary

{summary}

## Deliverables Completed This Phase

"""
        # Add completed deliverables
        for d_id, d_progress in self.state.deliverables.items():
            if d_progress.status == DeliverableStatus.COMPLETED:
                deliverable_info = DELIVERABLES.get(d_id, {})
                content += f"- [x] {deliverable_info.get('name', d_id)}\n"

        # Add pending deliverables
        content += "\n## Remaining Deliverables\n\n"
        for d_id, d_progress in self.state.deliverables.items():
            if d_progress.status != DeliverableStatus.COMPLETED:
                deliverable_info = DELIVERABLES.get(d_id, {})
                content += f"- [ ] {deliverable_info.get('name', d_id)}\n"

        with open(file_path, 'w') as f:
            f.write(content)

    # ========================================================================
    # Deliverable Management
    # ========================================================================

    def update_deliverable(
        self,
        deliverable_id: str,
        status: DeliverableStatus,
        file_path: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update deliverable status."""
        if deliverable_id in self.state.deliverables:
            d = self.state.deliverables[deliverable_id]
            d.status = status

            if status == DeliverableStatus.IN_PROGRESS and d.started_at is None:
                d.started_at = datetime.now()

            if file_path:
                d.file_path = file_path

            if error:
                d.error = error
                d.retry_count += 1

            self._save_state()

    def complete_deliverable(self, deliverable_id: str, file_path: str):
        """Mark deliverable as completed."""
        if deliverable_id in self.state.deliverables:
            d = self.state.deliverables[deliverable_id]
            d.status = DeliverableStatus.COMPLETED
            d.file_path = file_path
            d.completed_at = datetime.now()
            self._save_state()
            logger.info(f"Completed deliverable: {deliverable_id}")

    def fail_deliverable(self, deliverable_id: str, error: str):
        """Mark deliverable as failed."""
        if deliverable_id in self.state.deliverables:
            d = self.state.deliverables[deliverable_id]
            d.status = DeliverableStatus.FAILED
            d.error = error
            d.retry_count += 1
            self.state.errors.append({
                "deliverable": deliverable_id,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
            self._save_state()
            logger.error(f"Deliverable {deliverable_id} failed: {error}")

    def get_pending_deliverables(self) -> List[str]:
        """Get list of pending deliverable IDs."""
        return [
            d_id for d_id, d in self.state.deliverables.items()
            if d.status in [DeliverableStatus.PENDING, DeliverableStatus.FAILED]
        ]

    def get_completed_deliverables(self) -> List[str]:
        """Get list of completed deliverable IDs."""
        return [
            d_id for d_id, d in self.state.deliverables.items()
            if d.status == DeliverableStatus.COMPLETED
        ]

    def are_dependencies_met(self, deliverable_id: str) -> bool:
        """Check if all dependencies for a deliverable are completed."""
        deliverable_info = DELIVERABLES.get(deliverable_id, {})
        dependencies = deliverable_info.get("dependencies", [])

        if "ALL_MARKDOWN" in dependencies:
            # Check all markdown deliverables
            markdown_ids = [
                d_id for d_id, d_info in DELIVERABLES.items()
                if d_info.get("format") == "markdown"
            ]
            return all(
                self.state.deliverables[d_id].status == DeliverableStatus.COMPLETED
                for d_id in markdown_ids
            )

        return all(
            self.state.deliverables[dep].status == DeliverableStatus.COMPLETED
            for dep in dependencies
            if dep in self.state.deliverables
        )

    def get_ready_deliverables(self) -> List[str]:
        """Get deliverables that are ready to be generated (deps met, not started)."""
        ready = []
        for d_id in self.get_pending_deliverables():
            if self.are_dependencies_met(d_id):
                ready.append(d_id)
        return ready

    # ========================================================================
    # Research Cache Management
    # ========================================================================

    def save_research_output(self, research_output: ResearchOutput):
        """Save research output to cache."""
        self.state.research_output = research_output
        self.state.research_cache_path = str(self.research_cache_file)
        self.state.total_research_cost = research_output.total_cost
        self.state.total_cost = self.state.total_research_cost + self.state.total_synthesis_cost

        # Also save to separate file for easier access
        with open(self.research_cache_file, 'w') as f:
            f.write(research_output.model_dump_json(indent=2))

        self._save_state()
        logger.info(f"Saved research output ({research_output.total_cost:.4f} cost)")

    def load_research_output(self) -> Optional[ResearchOutput]:
        """Load research output from cache."""
        if self.research_cache_file.exists():
            with open(self.research_cache_file, 'r') as f:
                data = json.load(f)
            return ResearchOutput(**data)
        return self.state.research_output

    # ========================================================================
    # Cost Tracking
    # ========================================================================

    def add_cost(self, amount: float, cost_type: str = "synthesis"):
        """Add cost to tracking."""
        if cost_type == "research":
            self.state.total_research_cost += amount
        else:
            self.state.total_synthesis_cost += amount

        self.state.total_cost = (
            self.state.total_research_cost + self.state.total_synthesis_cost
        )
        self._save_state()

    # ========================================================================
    # Progress Reporting
    # ========================================================================

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        total_deliverables = len(self.state.deliverables)
        completed = len(self.get_completed_deliverables())
        pending = len(self.get_pending_deliverables())

        return {
            "company_name": self.company_name,
            "current_phase": self.state.current_phase,
            "phases": {
                name: {
                    "status": phase.status.value,
                    "summary": phase.summary
                }
                for name, phase in self.state.phases.items()
            },
            "deliverables": {
                "total": total_deliverables,
                "completed": completed,
                "pending": pending,
                "progress_percent": (completed / total_deliverables * 100) if total_deliverables > 0 else 0
            },
            "costs": {
                "research": self.state.total_research_cost,
                "synthesis": self.state.total_synthesis_cost,
                "total": self.state.total_cost
            },
            "errors": self.state.errors
        }

    def print_status(self):
        """Print current status to console."""
        summary = self.get_progress_summary()

        print(f"\n{'='*60}")
        print(f"AI Strategy Factory - {summary['company_name']}")
        print(f"{'='*60}")
        print(f"Current Phase: {summary['current_phase']}")
        print(f"\nPhase Status:")
        for name, phase in summary['phases'].items():
            status_icon = "✓" if phase['status'] == 'completed' else "○" if phase['status'] == 'pending' else "◑"
            print(f"  {status_icon} {name}: {phase['status']}")

        print(f"\nDeliverables: {summary['deliverables']['completed']}/{summary['deliverables']['total']} ({summary['deliverables']['progress_percent']:.1f}%)")
        print(f"Total Cost: ${summary['costs']['total']:.4f}")

        if summary['errors']:
            print(f"\nErrors: {len(summary['errors'])}")
            for err in summary['errors'][-3:]:  # Show last 3 errors
                print(f"  - {err.get('deliverable') or err.get('phase')}: {err['error'][:50]}...")

        print(f"{'='*60}\n")

    # ========================================================================
    # Reset and Cleanup
    # ========================================================================

    def reset(self, keep_research: bool = False):
        """Reset progress, optionally keeping research cache."""
        research_output = None
        if keep_research and self.state.research_output:
            research_output = self.state.research_output

        # Recreate state
        self.state = self._create_state(self.state.input_data)

        if research_output:
            self.save_research_output(research_output)
            self.state.phases["research"].status = DeliverableStatus.COMPLETED

        logger.info(f"Reset progress for {self.company_name}")


def get_or_create_tracker(
    company_name: str,
    company_input: Optional[CompanyInput] = None
) -> ProgressTracker:
    """
    Factory function to get or create a progress tracker.

    Args:
        company_name: Name of the company
        company_input: Optional input data

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(company_name, company_input)
