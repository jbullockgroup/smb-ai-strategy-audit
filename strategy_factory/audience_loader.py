"""
Audience loader for audience-specific strategy tailoring.

Loads audience definition files from knowledge_base/audience/
and provides access to the business context paragraph for prompt injection.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

AUDIENCE_DIR = PROJECT_ROOT / "knowledge_base" / "audience"


class AudienceLoader:
    """
    Loads and manages audience definition files.

    Usage:
        loader = AudienceLoader()
        audiences = loader.available_audiences
        content = loader.load_audience("mountain_bizworks_scaleup")
        context = loader.get_business_context("mountain_bizworks_scaleup")
    """

    def __init__(self, audience_dir: Path = None):
        self.audience_dir = Path(audience_dir) if audience_dir else AUDIENCE_DIR
        self._cache: Dict[str, str] = {}

    @property
    def available_audiences(self) -> List[Dict[str, str]]:
        """Scan *.md files, return [{"id": stem, "name": H1 heading}]."""
        if not self.audience_dir.exists():
            return []

        audiences = []
        for f in sorted(self.audience_dir.glob("*.md")):
            name = f.stem
            # Extract H1 heading as display name
            try:
                text = f.read_text(encoding="utf-8")
                h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
                display_name = h1_match.group(1).strip() if h1_match else name
            except Exception:
                display_name = name
            audiences.append({"id": name, "name": display_name})
        return audiences

    def load_audience(self, audience_id: str) -> Optional[str]:
        """Load full markdown content for an audience, with caching."""
        if audience_id in self._cache:
            return self._cache[audience_id]

        file_path = self.audience_dir / f"{audience_id}.md"
        if not file_path.exists():
            logger.warning(f"Audience file not found: {audience_id}")
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            self._cache[audience_id] = content
            logger.debug(f"Loaded audience: {audience_id} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error loading audience {audience_id}: {e}")
            return None

    def get_business_context(self, audience_id: str) -> str:
        """Extract the ## Business Context paragraph from an audience file."""
        content = self.load_audience(audience_id)
        if not content:
            return ""
        pattern = r"^##\s+Business Context\s*\n(.*?)(?=^##\s|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""


# Module-level singleton
_loader_instance: Optional[AudienceLoader] = None


def get_audience_loader() -> AudienceLoader:
    """Get singleton audience loader instance."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = AudienceLoader()
    return _loader_instance
