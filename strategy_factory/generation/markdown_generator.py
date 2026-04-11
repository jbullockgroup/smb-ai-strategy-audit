"""
Markdown generator for saving synthesized deliverables.

Handles saving markdown content to disk with proper formatting
and directory structure.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config import OUTPUT_DIR, DELIVERABLES
from ..models import DeliverableContent, SynthesisOutput


class MarkdownGenerator:
    """
    Generates and saves markdown deliverables.

    Responsibilities:
    - Save markdown content to appropriate directories
    - Add metadata headers to files
    - Handle file naming conventions
    - Extract and validate content structure
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the markdown generator.

        Args:
            output_dir: Base output directory.
        """
        self.output_dir = output_dir or OUTPUT_DIR

    def save_deliverable(
        self,
        company_slug: str,
        deliverable_id: str,
        content: str,
        add_metadata: bool = True,
    ) -> str:
        """
        Save a single markdown deliverable.

        Args:
            company_slug: URL-safe company name.
            deliverable_id: ID of the deliverable.
            content: Markdown content to save.
            add_metadata: Whether to add metadata header.

        Returns:
            Path to saved file.
        """
        # Create directory structure
        company_dir = self.output_dir / company_slug / "markdown"
        company_dir.mkdir(parents=True, exist_ok=True)

        # Build filename
        file_name = f"{deliverable_id}.md"
        file_path = company_dir / file_name

        # Prepare content with optional metadata
        final_content = content
        if add_metadata:
            metadata = self._build_metadata(deliverable_id)
            # Only add metadata if content doesn't already have it
            if not content.strip().startswith("---"):
                final_content = metadata + "\n\n" + content

        # Clean up content
        final_content = self._clean_markdown(final_content)

        # Save file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        return str(file_path)

    def save_all(
        self,
        company_slug: str,
        synthesis_output: SynthesisOutput,
        add_metadata: bool = True,
    ) -> Dict[str, str]:
        """
        Save all markdown deliverables from synthesis output.

        Args:
            company_slug: URL-safe company name.
            synthesis_output: Complete synthesis output.
            add_metadata: Whether to add metadata headers.

        Returns:
            Dict mapping deliverable_id to file path.
        """
        file_paths = {}

        for deliverable_id, content in synthesis_output.deliverables.items():
            if content.format == "markdown" and content.content:
                path = self.save_deliverable(
                    company_slug=company_slug,
                    deliverable_id=deliverable_id,
                    content=content.content,
                    add_metadata=add_metadata,
                )
                file_paths[deliverable_id] = path

        return file_paths

    def _build_metadata(self, deliverable_id: str) -> str:
        """Build YAML front matter metadata."""
        config = DELIVERABLES.get(deliverable_id, {})
        name = config.get("name", deliverable_id)

        return f"""---
title: "{name}"
deliverable_id: "{deliverable_id}"
generated_at: "{datetime.now().isoformat()}"
generator: "AI Strategy Factory"
---"""

    def _clean_markdown(self, content: str) -> str:
        """Clean and normalize markdown content."""
        # Remove multiple consecutive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Ensure file ends with single newline
        content = content.strip() + "\n"

        return content

    def extract_sections(self, content: str) -> Dict[str, str]:
        """
        Extract sections from markdown content.

        Useful for building reports.

        Args:
            content: Markdown content.

        Returns:
            Dict mapping section heading to section content.
        """
        sections = {}
        current_heading = "introduction"
        current_content = []

        for line in content.split("\n"):
            # Check for heading
            heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if heading_match:
                # Save previous section
                if current_content:
                    sections[current_heading] = "\n".join(current_content).strip()

                # Start new section
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_heading] = "\n".join(current_content).strip()

        return sections

    def extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract tables from markdown content.

        Args:
            content: Markdown content.

        Returns:
            List of tables as dicts with headers and rows.
        """
        tables = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check for table header (starts with |)
            if line.startswith("|") and line.endswith("|"):
                table_lines = [line]
                i += 1

                # Collect all table lines
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                # Parse table if we have at least header + separator + 1 row
                if len(table_lines) >= 3:
                    table = self._parse_table(table_lines)
                    if table:
                        tables.append(table)
            else:
                i += 1

        return tables

    def _parse_table(self, table_lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parse markdown table lines into structured data."""
        if len(table_lines) < 3:
            return None

        # Parse header
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.strip("|").split("|")]

        # Skip separator line (line 1)
        # Parse data rows
        rows = []
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))

        return {
            "headers": headers,
            "rows": rows,
        }

    def extract_bullet_points(self, content: str) -> List[str]:
        """
        Extract bullet points from markdown content.

        Args:
            content: Markdown content.

        Returns:
            List of bullet point texts.
        """
        bullet_pattern = re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE)
        matches = bullet_pattern.findall(content)
        return [m.strip() for m in matches]



def save_markdown_deliverables(
    company_slug: str,
    synthesis_output: SynthesisOutput,
    output_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Convenience function to save all markdown deliverables.

    Args:
        company_slug: URL-safe company name.
        synthesis_output: Complete synthesis output.
        output_dir: Optional output directory.

    Returns:
        Dict mapping deliverable_id to file path.
    """
    generator = MarkdownGenerator(output_dir=output_dir)
    return generator.save_all(company_slug, synthesis_output)
