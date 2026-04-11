#!/usr/bin/env python3
"""
PDF to Cheat Sheet Generator
Processes PDF consulting guides and creates synthesized markdown cheat sheets using Gemini API.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

import fitz  # pymupdf
import tiktoken
from dotenv import load_dotenv
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm

# =============================================================================
# CONFIGURATION
# =============================================================================

CHUNK_SIZE_TOKENS = 10_000  # Target tokens per chunk
REQUEST_DELAY_SECONDS = 5   # Delay between API requests
MODEL_NAME = "gemini-2.5-flash"

INPUT_FOLDER = "Consulting Guides"
OUTPUT_FOLDER = "Consulting Guides TLDR"
PROGRESS_FOLDER = "progress"

SYNTHESIS_PROMPT = """You are an expert consultant creating a comprehensive cheat sheet from a business/strategy document.

Analyze the following content and extract the most valuable, actionable knowledge:

## Key Concepts & Frameworks
- List core frameworks, models, or methodologies mentioned
- Provide 1-2 sentence explanations for each

## Critical Statistics & Data Points
- Extract specific numbers, percentages, and research findings
- Include source attribution where mentioned

## Actionable Insights
- Practical recommendations that can be implemented
- Strategic advice for business leaders

## Notable Quotes
- Include 2-3 impactful direct quotes (with context if available)

## Terminology
- Define key terms and acronyms introduced

Guidelines:
- Be comprehensive but concise - this is a quick reference document
- Preserve specific numbers and data - don't generalize
- Use bullet points for scannability
- Bold **key terms** on first use
- If content is mostly filler (table of contents, acknowledgments, references), respond with: [MINIMAL_CONTENT: This section contains primarily <description>]

---
CONTENT TO ANALYZE:
{chunk_text}
"""

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(log_dir: Path) -> logging.Logger:
    """Configure logging to both file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# =============================================================================
# PDF PROCESSING
# =============================================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    text_parts = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text", sort=True)
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from {pdf_path}: {e}")

    return "\n\n".join(text_parts)


def count_tokens(text: str, tokenizer) -> int:
    """Count tokens using tiktoken."""
    return len(tokenizer.encode(text))


def chunk_text(text: str, tokenizer, max_tokens: int = CHUNK_SIZE_TOKENS) -> list[dict]:
    """
    Split text into chunks of approximately max_tokens each.
    Returns list of dicts with 'text' and 'token_count'.
    """
    tokens = tokenizer.encode(text)
    total_tokens = len(tokens)

    if total_tokens <= max_tokens:
        return [{"text": text, "token_count": total_tokens}]

    chunks = []
    for i in range(0, total_tokens, max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append({
            "text": chunk_text,
            "token_count": len(chunk_tokens)
        })

    return chunks

# =============================================================================
# PROGRESS TRACKING
# =============================================================================

class ProgressTracker:
    """Persistent progress tracking for resumability."""

    def __init__(self, progress_dir: Path):
        self.progress_file = progress_dir / "progress.json"
        self.chunks_dir = progress_dir / "chunks"
        self.progress_dir = progress_dir

        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load existing progress or initialize new state."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"Resumed from progress file: {len(state.get('completed_chunks', []))} chunks already done")
                return state
            except json.JSONDecodeError:
                logger.warning("Corrupted progress file, starting fresh")

        return {
            'started_at': datetime.now().isoformat(),
            'completed_chunks': [],
            'chunk_results': {},
            'failed_chunks': [],
            'pdf_status': {}
        }

    def _save_state(self):
        """Persist current state to disk."""
        self.state['last_updated'] = datetime.now().isoformat()
        temp_file = self.progress_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        temp_file.rename(self.progress_file)

    def is_chunk_completed(self, chunk_id: str) -> bool:
        """Check if a chunk was already processed."""
        return chunk_id in self.state['completed_chunks']

    def mark_chunk_completed(self, chunk_id: str, result: str):
        """Mark a chunk as completed and save result."""
        self.state['completed_chunks'].append(chunk_id)
        self.state['chunk_results'][chunk_id] = result

        # Save intermediate chunk file
        chunk_file = self.chunks_dir / f"{chunk_id}.md"
        chunk_file.write_text(result)

        self._save_state()

    def mark_chunk_failed(self, chunk_id: str, error: str):
        """Record a failed chunk."""
        self.state['failed_chunks'].append({
            'chunk_id': chunk_id,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()

    def get_results_for_pdf(self, pdf_name: str) -> list[tuple[int, str]]:
        """Get all completed chunk results for a PDF, sorted by chunk index."""
        results = []
        for chunk_id, result in self.state['chunk_results'].items():
            if chunk_id.startswith(pdf_name.replace('.pdf', '')):
                # Extract chunk index from chunk_id (e.g., "myfile_chunk_003" -> 3)
                try:
                    idx = int(chunk_id.split('_chunk_')[-1])
                    results.append((idx, result))
                except (ValueError, IndexError):
                    continue
        return sorted(results, key=lambda x: x[0])

    def clear_progress(self):
        """Clear all progress (for fresh start)."""
        self.state = {
            'started_at': datetime.now().isoformat(),
            'completed_chunks': [],
            'chunk_results': {},
            'failed_chunks': [],
            'pdf_status': {}
        }
        self._save_state()
        # Also clear chunk files
        for chunk_file in self.chunks_dir.glob("*.md"):
            chunk_file.unlink()

# =============================================================================
# GEMINI API CLIENT
# =============================================================================

class GeminiClient:
    """Gemini API client with retry logic."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = MODEL_NAME

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def synthesize_chunk(self, chunk_text: str) -> str:
        """Send a chunk to Gemini for synthesis."""
        prompt = SYNTHESIS_PROMPT.format(chunk_text=chunk_text)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text

# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def generate_final_markdown(pdf_name: str, chunk_results: list[tuple[int, str]]) -> str:
    """Combine all chunk results into a single coherent markdown document."""
    clean_name = pdf_name.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()

    header = f"""# {clean_name} - Cheat Sheet

> Auto-generated summary from PDF analysis
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> Source: {pdf_name}

---

"""

    body_parts = []
    for idx, result in chunk_results:
        # Skip chunks that are ONLY minimal content markers (less than 500 chars of real content)
        # But keep chunks that have the marker plus substantial content
        content_without_marker = result
        if '[MINIMAL_CONTENT:' in result:
            # Remove the minimal content line(s) and check remaining length
            lines = result.split('\n')
            filtered_lines = [l for l in lines if '[MINIMAL_CONTENT:' not in l]
            content_without_marker = '\n'.join(filtered_lines).strip()
            if len(content_without_marker) < 500:
                continue
            # Use the filtered content (without the minimal content marker)
            result = content_without_marker

        if len(chunk_results) > 1:
            body_parts.append(f"## Section {idx + 1}\n\n{result}\n")
        else:
            body_parts.append(result)

    footer = """
---

*This cheat sheet was automatically generated. Please verify critical information against the original document.*
"""

    return header + "\n".join(body_parts) + footer

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF consulting guides to markdown cheat sheets using Gemini AI'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Extract and chunk PDFs without calling API'
    )
    parser.add_argument(
        '--reset-progress',
        action='store_true',
        help='Clear progress and start fresh'
    )
    parser.add_argument(
        '--single-pdf',
        type=str,
        help='Process only this specific PDF file'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=CHUNK_SIZE_TOKENS,
        help=f'Target tokens per chunk (default: {CHUNK_SIZE_TOKENS})'
    )
    args = parser.parse_args()

    # Setup paths
    base_dir = Path(__file__).parent
    load_dotenv(base_dir / '.env')

    # Setup logging
    log_dir = base_dir / PROGRESS_FOLDER / 'logs'
    setup_logging(log_dir)

    logger.info("=" * 60)
    logger.info("PDF to Cheat Sheet Tool - Starting")
    logger.info("=" * 60)

    # Validate API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        if not args.dry_run:
            logger.error("GEMINI_API_KEY not found or not set in .env file")
            logger.error("Please add your API key to the .env file")
            sys.exit(1)
        else:
            logger.warning("No API key set, but running in dry-run mode")

    # Initialize components
    progress_tracker = ProgressTracker(base_dir / PROGRESS_FOLDER)
    if args.reset_progress:
        progress_tracker.clear_progress()
        logger.info("Progress cleared")

    tokenizer = tiktoken.get_encoding("cl100k_base")

    if not args.dry_run and api_key and api_key != 'your_api_key_here':
        gemini_client = GeminiClient(api_key)
    else:
        gemini_client = None

    # Create output directory
    output_dir = base_dir / OUTPUT_FOLDER
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDFs to process
    input_dir = base_dir / INPUT_FOLDER
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    if args.single_pdf:
        pdf_files = [input_dir / args.single_pdf]
        if not pdf_files[0].exists():
            logger.error(f"PDF file not found: {pdf_files[0]}")
            sys.exit(1)
    else:
        pdf_files = sorted(input_dir.glob('*.pdf'))

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Process each PDF
    total_chunks_processed = 0

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pdf_name}")
        logger.info(f"File size: {pdf_path.stat().st_size / 1_000_000:.1f} MB")

        try:
            # Extract text
            logger.info("  Extracting text...")
            text = extract_text_from_pdf(str(pdf_path))
            total_tokens = count_tokens(text, tokenizer)
            logger.info(f"  Extracted {total_tokens:,} tokens")

            # Chunk
            chunks = chunk_text(text, tokenizer, args.chunk_size)
            logger.info(f"  Split into {len(chunks)} chunk(s)")

            if args.dry_run:
                for i, chunk in enumerate(chunks):
                    logger.info(f"    Chunk {i+1}/{len(chunks)}: {chunk['token_count']:,} tokens")
                continue

            # Process each chunk
            pdf_base = pdf_name.replace('.pdf', '')
            for i, chunk in enumerate(tqdm(chunks, desc=f"Processing {pdf_name[:30]}")):
                chunk_id = f"{pdf_base}_chunk_{i:03d}"

                # Skip if already done
                if progress_tracker.is_chunk_completed(chunk_id):
                    logger.debug(f"Skipping completed chunk: {chunk_id}")
                    continue

                try:
                    logger.info(f"  Processing chunk {i+1}/{len(chunks)} ({chunk['token_count']:,} tokens)...")

                    result = gemini_client.synthesize_chunk(chunk['text'])
                    progress_tracker.mark_chunk_completed(chunk_id, result)
                    total_chunks_processed += 1

                    logger.info(f"  Completed {chunk_id}")

                    # Rate limiting delay
                    if i < len(chunks) - 1:
                        time.sleep(REQUEST_DELAY_SECONDS)

                except Exception as e:
                    logger.error(f"Failed chunk {chunk_id}: {e}")
                    progress_tracker.mark_chunk_failed(chunk_id, str(e))

            # Generate final markdown for this PDF
            chunk_results = progress_tracker.get_results_for_pdf(pdf_name)
            if chunk_results:
                markdown_content = generate_final_markdown(pdf_name, chunk_results)
                output_file = output_dir / f"{pdf_base}_TLDR.md"
                output_file.write_text(markdown_content)
                logger.info(f"  Created: {output_file.name}")

        except Exception as e:
            logger.error(f"Failed to process {pdf_name}: {e}")
            continue

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Chunks processed: {total_chunks_processed}")
    logger.info(f"Output directory: {output_dir}")

    failed = progress_tracker.state.get('failed_chunks', [])
    if failed:
        logger.warning(f"Failed chunks: {len(failed)} - see progress/progress.json")


if __name__ == '__main__':
    main()
