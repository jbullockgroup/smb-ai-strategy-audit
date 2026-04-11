"""
Gemini API client wrapper with retry logic.

Provides a robust interface for making Gemini API calls
with automatic retries, exponential backoff, and cost tracking.
"""

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import google.generativeai as genai

from ..config import GEMINI_MODEL, GEMINI_REQUEST_DELAY, RETRY_CONFIG


@dataclass
class SynthesisResult:
    """Result of a synthesis request."""
    content: str
    model_used: str
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    cost_estimate: float
    error: Optional[str] = None


class GeminiClient:
    """
    Wrapper for Gemini API with retry logic.
    
    Features:
    - Automatic retry with exponential backoff
    - Cost estimation and tracking
    - Rate limiting
    - Token counting
    """
    
    # Gemini 2.5 Flash pricing (per 1M tokens)
    COST_PER_1M_INPUT = 0.30  # $0.30 per 1M input tokens
    COST_PER_1M_OUTPUT = 2.50  # $2.50 per 1M output tokens
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = GEMINI_MODEL,
    ):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, uses GEMINI_API_KEY env var.
            model_name: Model to use for synthesis.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Cost tracking
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_thinking_tokens = 0
        self.request_count = 0
        
        # Rate limiting
        self.last_request_time = 0.0
        self.min_request_interval = GEMINI_REQUEST_DELAY
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of a request."""
        input_cost = (input_tokens / 1_000_000) * self.COST_PER_1M_INPUT
        output_cost = (output_tokens / 1_000_000) * self.COST_PER_1M_OUTPUT
        return input_cost + output_cost
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimate: ~4 characters per token
        return len(text) // 4
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
    ) -> SynthesisResult:
        """
        Generate content using Gemini.
        
        Args:
            prompt: The prompt to send.
            system_instruction: Optional system instruction.
            temperature: Sampling temperature (0-1).
            max_output_tokens: Maximum tokens in response.
        
        Returns:
            SynthesisResult with generated content.
        """
        max_retries = RETRY_CONFIG["max_retries"]
        delay = RETRY_CONFIG["initial_delay"]
        max_delay = RETRY_CONFIG["max_delay"]
        backoff = RETRY_CONFIG["backoff_multiplier"]
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                # Configure generation
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
                
                # Create model with system instruction if provided
                if system_instruction:
                    model = genai.GenerativeModel(
                        self.model_name,
                        system_instruction=system_instruction,
                    )
                else:
                    model = self.model
                
                # Generate response
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                
                # Detect truncation via finish_reason before reading text
                candidate = response.candidates[0] if response.candidates else None
                finish_reason = getattr(candidate, "finish_reason", None)
                finish_name = getattr(finish_reason, "name", str(finish_reason))
                if finish_name == "MAX_TOKENS":
                    raise RuntimeError(
                        f"Gemini stopped early: finish_reason={finish_name} "
                        f"(output hit max_output_tokens={max_output_tokens})"
                    )

                # Extract content
                content = response.text
                # Use actual token counts from API response
                um = response.usage_metadata
                input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
                output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)
                # Derive thinking tokens from gap (library v0.8.5 doesn't expose them directly)
                total_tokens = getattr(um, 'total_token_count', 0) or 0
                thinking_tokens = max(0, total_tokens - input_tokens - output_tokens)

                # Calculate cost (thinking tokens billed at output rate)
                cost = self._estimate_cost(input_tokens, output_tokens + thinking_tokens)

                # Update tracking
                self.total_cost += cost
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_thinking_tokens += thinking_tokens
                self.request_count += 1
                
                return SynthesisResult(
                    content=content,
                    model_used=self.model_name,
                    timestamp=datetime.now(),
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    cost_estimate=cost,
                )
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                    time.sleep(delay)
                    delay = min(delay * backoff, max_delay)
        
        # All retries failed
        return SynthesisResult(
            content="",
            model_used=self.model_name,
            timestamp=datetime.now(),
            prompt_tokens=0,
            completion_tokens=0,
            cost_estimate=0.0,
            error=str(last_error),
        )
    
    def generate_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> SynthesisResult:
        """
        Generate content with structured context.
        
        Args:
            prompt: The prompt template.
            context: Context dict to format into prompt.
            system_instruction: Optional system instruction.
            temperature: Sampling temperature.
        
        Returns:
            SynthesisResult with generated content.
        """
        # Format prompt with context
        formatted_prompt = prompt
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in formatted_prompt:
                formatted_prompt = formatted_prompt.replace(placeholder, str(value))
        
        return self.generate(
            prompt=formatted_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )
    
    @staticmethod
    def _is_separator_row(line: str) -> bool:
        """Check if a line is a (possibly malformed) table separator row.

        A separator row is comprised almost entirely of |, -, :, and spaces.
        Data rows contain letters, digits, and punctuation that aren't separator chars.
        """
        stripped = line.strip()
        if not stripped:
            return False
        allowed = set('|-: ')
        non_allowed = sum(1 for c in stripped if c not in allowed)
        return non_allowed / len(stripped) < 0.05 and '-' in stripped and '|' in stripped

    def _fix_malformed_tables(self, content: str) -> str:
        """Fix malformed markdown tables with overly long separator rows."""
        import re
        lines = content.split('\n')
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this looks like a table header row (has multiple | chars)
            if line.count('|') >= 2 and not re.match(r'^\s*\|[\s\-:]+\|', line):
                # This might be a header row, count columns
                cols = [c.strip() for c in line.split('|')]
                cols = [c for c in cols if c]
                num_cols = len(cols)

                if num_cols >= 2:
                    # Check if next line is a malformed separator
                    if i + 1 < len(lines) and self._is_separator_row(lines[i + 1]):
                        # Create a proper separator
                        separator = '|' + '|'.join([' --- ' for _ in range(num_cols)]) + '|'
                        fixed_lines.append(line)
                        fixed_lines.append(separator)
                        i += 2
                        continue

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines)

    def generate_markdown(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> SynthesisResult:
        """
        Generate markdown content.

        Args:
            prompt: The prompt.
            system_instruction: Optional system instruction.

        Returns:
            SynthesisResult with markdown content.
        """
        # Add markdown formatting instruction
        markdown_instruction = """
You are generating professional consulting documentation in Markdown format.
Follow these formatting guidelines:
- Use proper heading hierarchy (# for title, ## for sections, ### for subsections)
- CRITICAL: Every section heading in your output MUST start with # markers. Never write a section title as plain text.
  Wrong: Your Current Tool Stack
  Right: ## Your Current Tool Stack
- Use bullet points and numbered lists for clarity
- Include tables where appropriate using markdown syntax
- CRITICAL: For markdown tables, each row must be on a single line. Table separator row must only have dashes like |---|---|---|
- Use **bold** for emphasis and `code` for technical terms
- Keep paragraphs concise and actionable
- Do not include ```markdown``` code fences around the output
"""

        full_instruction = markdown_instruction
        if system_instruction:
            full_instruction = f"{markdown_instruction}\n\n{system_instruction}"

        result = self.generate(
            prompt=prompt,
            system_instruction=full_instruction,
            temperature=0.5,  # Lower temperature for more consistent formatting
        )

        # Post-process to fix any malformed tables
        if result.content:
            result.content = self._fix_malformed_tables(result.content)

        return result
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get a summary of API usage and costs."""
        return {
            "total_cost": round(self.total_cost, 4),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_thinking_tokens": self.total_thinking_tokens,
            "request_count": self.request_count,
            "avg_cost_per_request": round(
                self.total_cost / max(1, self.request_count), 4
            ),
        }
