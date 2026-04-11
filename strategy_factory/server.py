"""
Simple web server to view AI Strategy Factory deliverables.

Usage:
    python -m strategy_factory.server "stripe"

Then open http://localhost:8000 in your browser.
"""

import argparse
import http.server
import json
import os
import socketserver
import webbrowser

from strategy_factory.config import DELIVERABLES
from pathlib import Path
from urllib.parse import unquote

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

from strategy_factory.config import OUTPUT_DIR
from strategy_factory.progress_tracker import slugify


def generate_html_page(company_name: str, company_slug: str) -> str:
    """Generate the main HTML page for viewing deliverables."""
    output_dir = OUTPUT_DIR / company_slug
    markdown_dir = output_dir / "markdown"

    # Read markdown files, ordered by DELIVERABLES config
    markdown_files = []
    if markdown_dir.exists():
        md_on_disk = {f.stem: f.name for f in markdown_dir.glob("*.md")}
        for d_id, d_cfg in DELIVERABLES.items():
            if d_cfg.get("format") == "markdown" and d_id in md_on_disk:
                markdown_files.append({
                    "name": d_cfg["name"],
                    "filename": md_on_disk[d_id],
                    "path": f"/markdown/{md_on_disk[d_id]}"
                })

    # Check for documents
    documents = []
    docs_dir = output_dir / "documents"
    if docs_dir.exists():
        for docx in sorted(docs_dir.glob("*.docx")):
            documents.append({
                "name": docx.stem.replace("_", " ").title(),
                "path": f"/documents/{docx.name}",
                "size": f"{docx.stat().st_size / 1024:.1f} KB"
            })

    # Read state.json for costs
    state_data = {}
    state_file = output_dir / "state.json"
    if state_file.exists():
        with open(state_file) as f:
            state_data = json.load(f)

    total_cost = state_data.get("total_cost", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Strategy Factory - {company_name}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --success: #22c55e;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}

        header .container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        header h1 {{
            font-size: 1.75rem;
            font-weight: 600;
        }}

        header .company {{
            font-size: 1rem;
            opacity: 0.9;
        }}

        .stats {{
            display: flex;
            gap: 2rem;
            font-size: 0.875rem;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: 600;
        }}

        .main-content {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
            min-height: calc(100vh - 200px);
        }}

        .sidebar {{
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 1rem;
        }}

        .sidebar h3 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }}

        .nav-list {{
            list-style: none;
            margin-bottom: 1.5rem;
        }}

        .nav-list li {{
            margin-bottom: 0.25rem;
        }}

        .nav-list a {{
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--text);
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.875rem;
            transition: all 0.15s;
        }}

        .nav-list a:hover {{
            background: var(--bg);
            color: var(--primary);
        }}

        .nav-list a.active {{
            background: var(--primary);
            color: white;
        }}

        .download-btn {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.75rem;
            background: var(--bg);
            border-radius: 6px;
            text-decoration: none;
            color: var(--text);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            transition: all 0.15s;
        }}

        .download-btn:hover {{
            background: var(--primary);
            color: white;
        }}

        .download-btn .size {{
            margin-left: auto;
            opacity: 0.6;
            font-size: 0.75rem;
        }}

        .content {{
            background: var(--card);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .content h1, .content h2, .content h3, .content h4 {{
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: var(--text);
        }}

        .content h1 {{ font-size: 1.75rem; margin-top: 0; }}
        .content h2 {{ font-size: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; }}
        .content h3 {{ font-size: 1.25rem; }}
        .content h4 {{ font-size: 1.1rem; }}

        .content p {{
            margin-bottom: 1rem;
        }}

        .content ul, .content ol {{
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}

        .content li {{
            margin-bottom: 0.5rem;
        }}

        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }}

        .content th, .content td {{
            padding: 0.75rem;
            text-align: left;
            border: 1px solid var(--border);
        }}

        .content th {{
            background: var(--bg);
            font-weight: 600;
        }}

        .content code {{
            background: var(--bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875em;
        }}

        .content pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin-bottom: 1rem;
        }}

        .content pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}

        .content blockquote {{
            border-left: 4px solid var(--primary);
            padding-left: 1rem;
            margin: 1rem 0;
            color: var(--text-secondary);
        }}

        .diagrams-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }}

        .diagram-card {{
            background: var(--bg);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}

        .diagram-card img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }}

        .diagram-card h4 {{
            margin: 0;
            font-size: 0.875rem;
        }}

        .welcome {{
            text-align: center;
            padding: 4rem 2rem;
        }}

        .welcome h2 {{
            font-size: 2rem;
            margin-bottom: 1rem;
            border: none;
        }}

        .welcome p {{
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto 2rem;
        }}

        .quick-links {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            max-width: 800px;
            margin: 0 auto;
        }}

        .quick-link {{
            background: var(--bg);
            padding: 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            color: var(--text);
            transition: all 0.15s;
        }}

        .quick-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .quick-link h4 {{
            margin: 0 0 0.5rem;
            color: var(--primary);
        }}

        .quick-link p {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin: 0;
        }}

        @media (max-width: 900px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}

            .sidebar {{
                position: relative;
                top: 0;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div>
                <h1>AI Strategy Factory</h1>
                <p class="company">{company_name}</p>
            </div>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(markdown_files)}</div>
                    <div>Deliverables</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${total_cost:.2f}</div>
                    <div>Total Cost</div>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="main-content">
            <aside class="sidebar">
                <h3>Strategy Documents</h3>
                <ul class="nav-list">
"""

    for md in markdown_files:
        html += f'                    <li><a href="#" data-file="{md["filename"]}" class="md-link">{md["name"]}</a></li>\n'

    html += """                </ul>
"""

    if documents:
        html += """
                <h3>Documents</h3>
"""
        for doc in documents:
            html += f'                <a href="{doc["path"]}" class="download-btn" download>📄 {doc["name"]}<span class="size">{doc["size"]}</span></a>\n'

    html += """
            </aside>

            <main class="content" id="content">
                <div class="welcome">
                    <h2>Welcome to Your AI Strategy</h2>
                    <p>Select a document from the sidebar to view your comprehensive AI strategy deliverables, or download the reports.</p>
                    <div class="quick-links">
                        <a href="#" class="quick-link" data-file="05_roadmap.md">
                            <h4>Implementation Roadmap</h4>
                            <p>30/60/90/180/360 day plan</p>
                        </a>
                        <a href="#" class="quick-link" data-file="06_quick_wins.md">
                            <h4>Quick Wins</h4>
                            <p>Immediate opportunities</p>
                        </a>
                        <a href="#" class="quick-link" data-file="09_roi_calculator.md">
                            <h4>ROI Analysis</h4>
                            <p>Cost-benefit breakdown</p>
                        </a>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script>
        function loadMarkdown(filename, clickedElement) {
            console.log('Loading:', filename);
            fetch('/api/markdown/' + filename)
                .then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.text();
                })
                .then(html => {
                    console.log('Got HTML, length:', html.length);
                    document.getElementById('content').innerHTML = html;
                    document.querySelectorAll('.nav-list a').forEach(a => a.classList.remove('active'));
                    if (clickedElement) clickedElement.classList.add('active');
                })
                .catch(err => {
                    console.error('Error:', err);
                    document.getElementById('content').innerHTML = '<p>Error loading content: ' + err.message + '</p>';
                });
        }

        // Add event listeners after DOM loads
        document.addEventListener('DOMContentLoaded', function() {
            // Sidebar markdown links
            document.querySelectorAll('.md-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const filename = this.getAttribute('data-file');
                    loadMarkdown(filename, this);
                });
            });

            // Quick link cards with data-file attribute
            document.querySelectorAll('.quick-link[data-file]').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const filename = this.getAttribute('data-file');
                    loadMarkdown(filename, null);
                });
            });
        });
    </script>
</body>
</html>"""

    return html


class StrategyFactoryHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the strategy factory viewer."""

    def __init__(self, *args, company_slug=None, company_name=None, output_dir=None, **kwargs):
        self.company_slug = company_slug
        self.company_name = company_name
        self.base_output_dir = output_dir
        super().__init__(*args, directory=str(output_dir), **kwargs)

    def do_GET(self):
        path = unquote(self.path)

        if path == "/" or path == "":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = generate_html_page(self.company_name, self.company_slug)
            self.wfile.write(html.encode())
            return

        if path.startswith("/api/markdown/"):
            filename = path.replace("/api/markdown/", "")
            md_path = Path(self.base_output_dir) / "markdown" / filename

            if md_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                with open(md_path, "r") as f:
                    content = f.read()

                if HAS_MARKDOWN:
                    html_content = markdown.markdown(
                        content,
                        extensions=['tables', 'fenced_code', 'toc']
                    )
                else:
                    html_content = f"<pre>{content}</pre>"

                self.wfile.write(html_content.encode())
            else:
                self.send_error(404, "File not found")
            return

        super().do_GET()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(company_name: str, port: int = 8000, open_browser: bool = True):
    """Run the web server for viewing deliverables."""
    company_slug = slugify(company_name)
    output_dir = OUTPUT_DIR / company_slug

    if not output_dir.exists():
        print(f"Error: No output found for '{company_name}'")
        print(f"Expected directory: {output_dir}")
        return 1

    def handler(*args, **kwargs):
        return StrategyFactoryHandler(
            *args,
            company_slug=company_slug,
            company_name=company_name,
            output_dir=output_dir,
            **kwargs
        )

    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\nAI Strategy Factory Viewer")
        print(f"=" * 40)
        print(f"Company: {company_name}")
        print(f"Server running at: {url}")
        print(f"Press Ctrl+C to stop\n")

        if open_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="View AI Strategy Factory deliverables in your browser"
    )
    parser.add_argument(
        "company",
        type=str,
        help="Company name to view deliverables for"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to run server on (default: 8000)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )

    args = parser.parse_args()
    return run_server(args.company, args.port, not args.no_browser)


if __name__ == "__main__":
    exit(main())
