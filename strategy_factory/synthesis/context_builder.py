"""
Context builder for assembling prompt context.

Combines research results, TLDR knowledge, and user context
into structured prompts for synthesis.
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..config import DELIVERABLES, TLDR_GUIDES_DIR
from ..models import ResearchOutput, CompanyInput
from ..temporal import get_temporal_context, TemporalContext
from ..knowledge_loader import KnowledgeLoader


class ContextBuilder:
    """
    Builds context for synthesis prompts.
    
    Assembles:
    - Company research results
    - Relevant TLDR guide knowledge
    - User-provided context
    - Temporal context
    - Previously generated deliverables (for dependencies)
    """
    
    def __init__(
        self,
        knowledge_loader: Optional[KnowledgeLoader] = None,
        temporal: Optional[TemporalContext] = None,
    ):
        """
        Initialize the context builder.
        
        Args:
            knowledge_loader: KnowledgeLoader for TLDR guides.
            temporal: TemporalContext for date injection.
        """
        self.knowledge_loader = knowledge_loader or KnowledgeLoader()
        self.temporal = temporal or get_temporal_context()
        self.generated_deliverables: Dict[str, str] = {}
    
    def build_context(
        self,
        deliverable_id: str,
        research: ResearchOutput,
        company_input: CompanyInput,
    ) -> Dict[str, Any]:
        """
        Build complete context for a deliverable.
        
        Args:
            deliverable_id: ID of the deliverable to generate.
            research: Research output from Perplexity.
            company_input: Original company input.
        
        Returns:
            Dict with all context needed for synthesis.
        """
        deliverable_config = DELIVERABLES.get(deliverable_id, {})
        
        context = {
            # Company info
            "company_name": company_input.name,
            "company_context": company_input.context,
            "industry": company_input.industry or research.industry.primary_industry,
            
            # Temporal context
            **self.temporal.get_context(),
            "temporal_prompt": self.temporal.format_for_prompt(),
            
            # Research sections
            "company_profile": self._format_company_profile(research),
            "digital_presence": self._format_digital_presence(research),
            "industry_context": self._format_industry_context(research),
            "tech_landscape": self._format_tech_landscape(research),
            
            # Knowledge base
            "tldr_knowledge": self._load_tldr_knowledge(deliverable_id, audience_id=company_input.audience),
            
            # Dependencies (previously generated content)
            "dependencies": self._get_dependencies(deliverable_id),
            
            # Metadata
            "deliverable_name": deliverable_config.get("name", deliverable_id),
            "information_tier": research.information_tier.value,
            "confidence_scores": research.confidence_scores,
        }
        
        return context
    
    def _format_company_profile(self, research: ResearchOutput) -> str:
        """Format company profile for prompt."""
        profile = research.profile
        
        sections = [
            f"## Company Overview\n{profile.description}",
        ]
        
        if profile.products_services:
            sections.append(
                f"## Products/Services\n" + 
                "\n".join(f"- {p}" for p in profile.products_services)
            )
        
        if profile.employee_estimate:
            sections.append(f"## Company Size\n~{profile.employee_estimate} employees")
        
        if profile.headquarters:
            sections.append(f"## Headquarters\n{profile.headquarters}")
        
        if profile.recent_news:
            news = "\n".join(
                f"- {n.get('title', 'News')}"
                for n in profile.recent_news[:3]
            )
            sections.append(f"## Recent News\n{news}")
        
        return "\n\n".join(sections)
    
    def _format_digital_presence(self, research: ResearchOutput) -> str:
        """Format digital presence data from raw query results for prompt."""
        sections = []
        raw = research.raw_queries

        # Google review rating (simple regex — the one thing worth extracting)
        google = raw.get("google_reviews")
        if google and google.results:
            rating_pattern = r'(\d+\.?\d*)\s*(?:stars?|/5|out of 5|-star)'
            for r in google.results:
                match = re.search(rating_pattern, r.snippet.lower())
                if match:
                    sections.append(f"## Customer Reviews\nGoogle rating: {match.group(1)}/5")
                    break

        # Raw review snippets — let Gemini interpret sentiment/themes
        review_snippets = []
        for key in ("social_reviews", "google_reviews"):
            qr = raw.get(key)
            if qr:
                for r in qr.results:
                    text = r.snippet.strip()
                    if len(text) > 20:
                        review_snippets.append(text[:300])
        if review_snippets:
            seen = set()
            unique = []
            for s in review_snippets:
                if s not in seen:
                    seen.add(s)
                    unique.append(s)
            formatted = "\n".join(f"- {s}" for s in unique[:8])
            sections.append(f"### What Customers Say\n{formatted}")

        # Social platforms (string matching — Python is good at this)
        company = raw.get("company_presence")
        if company and company.results:
            platform_map = {
                "facebook": "Facebook", "instagram": "Instagram",
                "tiktok": "TikTok", "youtube": "YouTube",
                "linkedin": "LinkedIn", "twitter": "Twitter/X",
                "x.com": "Twitter/X", "pinterest": "Pinterest",
                "nextdoor": "Nextdoor",
            }
            text = " ".join(r.snippet.lower() + " " + r.url.lower() for r in company.results)
            platforms = []
            for keyword, name in platform_map.items():
                if keyword in text and name not in platforms:
                    platforms.append(name)
            if platforms:
                sections.append(f"## Social Media\nPlatforms: {', '.join(platforms)}")

            # Activity snippet
            activity_keywords = ["posts", "followers", "engagement", "active", "updates"]
            for r in company.results:
                for sentence in r.snippet.split("."):
                    if any(kw in sentence.lower() for kw in activity_keywords):
                        sections.append(f"**Activity:** {sentence.strip()[:300]}")
                        break
                else:
                    continue
                break

        # Blog presence
        blog = raw.get("blog_content")
        if blog and blog.results:
            topics = [r.title[:150] for r in blog.results[:5] if r.title and len(r.title) > 10]
            if topics:
                formatted = "\n".join(f"- {t}" for t in topics)
                sections.append(f"## Blog & Content\n{formatted}")
        else:
            sections.append("## Blog & Content\nNo significant blog or content marketing presence found.")

        return "\n\n".join(sections) if sections else ""

    def _format_industry_context(self, research: ResearchOutput) -> str:
        """Format industry context for prompt."""
        industry = research.industry
        
        sections = [
            f"## Industry: {industry.primary_industry}",
        ]
        
        if industry.market_size:
            sections.append(f"**Market Size:** {industry.market_size}")
        
        if industry.growth_rate:
            sections.append(f"**Growth Rate:** {industry.growth_rate}")
        
        if industry.key_trends:
            trends = "\n".join(f"- {t}" for t in industry.key_trends[:5])
            sections.append(f"## Key Trends\n{trends}")
        
        if industry.challenges:
            challenges = "\n".join(f"- {c}" for c in industry.challenges[:5])
            sections.append(f"## Industry Challenges\n{challenges}")
        
        return "\n\n".join(sections)
    
    def _format_tech_landscape(self, research: ResearchOutput) -> str:
        """Format technology landscape for prompt."""
        tech = research.tech_landscape
        
        sections = []
        
        if tech.company_tech_stack:
            stack = ", ".join(tech.company_tech_stack[:10])
            sections.append(f"## Current Tech Stack\n{stack}")
        
        if tech.company_ai_initiatives:
            initiatives = "\n".join(f"- {i}" for i in tech.company_ai_initiatives[:5])
            sections.append(f"## Company AI Initiatives\n{initiatives}")
        
        if tech.industry_ai_adoption_rate:
            sections.append(f"## Industry AI Adoption\n{tech.industry_ai_adoption_rate}")
        
        if tech.industry_ai_use_cases:
            use_cases = "\n".join(
                f"- {uc.get('description', '')[:100]}"
                for uc in tech.industry_ai_use_cases[:5]
            )
            sections.append(f"## Industry AI Use Cases\n{use_cases}")
        
        if tech.recommended_ai_tools:
            tools = "\n".join(
                f"- {t.get('name', 'Tool')}"
                for t in tech.recommended_ai_tools[:5]
            )
            sections.append(f"## Recommended AI Tools\n{tools}")
        
        return "\n\n".join(sections) if sections else "No technology landscape information available."
    
    def _load_tldr_knowledge(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
        """Load relevant TLDR knowledge for a deliverable."""
        deliverable_config = DELIVERABLES.get(deliverable_id, {})
        tldr_guides = deliverable_config.get("tldr_guides", [])

        if not tldr_guides:
            return ""

        knowledge_sections = []

        for guide_name in tldr_guides:
            content = self.knowledge_loader.load_guide(guide_name)
            if content:
                # Truncate to reasonable length
                if len(content) > 5000:
                    content = content[:5000] + "\n\n[Content truncated...]"
                knowledge_sections.append(
                    f"### From: {guide_name}\n{content}"
                )

        if knowledge_sections:
            return "## Consulting Knowledge Base\n\n" + "\n\n---\n\n".join(knowledge_sections)

        return ""
    
    def _get_dependencies(self, deliverable_id: str) -> Dict[str, str]:
        """Get content from dependent deliverables."""
        deliverable_config = DELIVERABLES.get(deliverable_id, {})
        dependencies = deliverable_config.get("dependencies", [])
        
        if not dependencies:
            return {}
        
        dep_content = {}
        
        for dep_id in dependencies:
            if dep_id == "ALL_MARKDOWN":
                # Include all markdown deliverables
                for d_id, content in self.generated_deliverables.items():
                    if DELIVERABLES.get(d_id, {}).get("format") == "markdown":
                        dep_content[d_id] = content
            elif dep_id in self.generated_deliverables:
                dep_content[dep_id] = self.generated_deliverables[dep_id]
        
        return dep_content
    
    def register_deliverable(self, deliverable_id: str, content: str) -> None:
        """
        Register a generated deliverable for dependency tracking.
        
        Args:
            deliverable_id: ID of the deliverable.
            content: Generated content.
        """
        self.generated_deliverables[deliverable_id] = content
    
    def format_dependencies_for_prompt(self, dependencies: Dict[str, str]) -> str:
        """Format dependencies for inclusion in prompt, preferring SUMMARY lines."""
        if not dependencies:
            return ""

        sections = ["## Previously Generated Content\n"]

        for dep_id, content in dependencies.items():
            dep_name = DELIVERABLES.get(dep_id, {}).get("name", dep_id)

            # Look for SUMMARY: line
            summary_line = None
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith("SUMMARY:"):
                    summary_line = stripped
                    break

            if summary_line:
                sections.append(f"### {dep_name}\n{summary_line}")
            else:
                # Fallback: first two paragraphs
                paragraphs = content.split('\n\n')
                fallback = '\n\n'.join(paragraphs[:2])
                if len(fallback) > 800:
                    fallback = fallback[:800] + "..."
                sections.append(f"### {dep_name}\n{fallback}")

        return "\n\n".join(sections)
    
    def build_full_prompt(
        self,
        deliverable_id: str,
        prompt_template: str,
        research: ResearchOutput,
        company_input: CompanyInput,
    ) -> str:
        """
        Build complete prompt with all context.
        
        Args:
            deliverable_id: ID of the deliverable.
            prompt_template: The prompt template to use.
            research: Research output.
            company_input: Company input.
        
        Returns:
            Fully formatted prompt string.
        """
        context = self.build_context(deliverable_id, research, company_input)
        
        # Build the full prompt
        prompt_parts = [
            context["temporal_prompt"],
            f"\n# Company: {context['company_name']}",
            f"\n{context['company_profile']}",
            f"\n{context['digital_presence']}",
            f"\n{context['industry_context']}",
            f"\n{context['tech_landscape']}",
        ]

        # Add TLDR knowledge
        if context["tldr_knowledge"]:
            prompt_parts.append(f"\n{context['tldr_knowledge']}")

        # Add user context if provided
        if context["company_context"]:
            prompt_parts.append(
                f"\n## Additional Context from Client\n{context['company_context']}"
            )

        # Business context — regional/cultural context research can't surface
        if company_input.audience:
            from ..audience_loader import get_audience_loader
            loader = get_audience_loader()
            business_context = loader.get_business_context(company_input.audience)
            if business_context:
                prompt_parts.append(f"\n## Business Context\n{business_context}")

        # Add dependencies
        if context["dependencies"]:
            prompt_parts.append(
                f"\n{self.format_dependencies_for_prompt(context['dependencies'])}"
            )
        
        # Add the actual prompt template
        prompt_parts.append(f"\n---\n\n{prompt_template}")
        
        return "\n".join(prompt_parts)
