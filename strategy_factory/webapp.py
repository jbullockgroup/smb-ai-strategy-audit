"""
Full-featured web application for AI Strategy Factory.

Features:
- Home page to enter company name and start analysis
- Real-time progress tracking during pipeline execution
- Results viewer with proper markdown rendering
- Download links for generated files

Usage:
    python -m strategy_factory.webapp

Then open http://localhost:5000 in your browser.
"""

import json
import os
import queue
import shutil
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify, Response, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension

from strategy_factory.config import OUTPUT_DIR, DELIVERABLES
from strategy_factory.models import CompanyInput
from strategy_factory.progress_tracker import ProgressTracker, slugify

load_dotenv()

app = Flask(__name__)

# Store for active jobs and their progress
active_jobs = {}


# =============================================================================
# HTML Templates
# =============================================================================

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - AI Strategy Factory</title>
    <style>
        :root {
            --primary: #3b82f6;
            --primary-dark: #2563eb;
            --primary-light: #1e3a5f;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #e2e8f0;
            --text-secondary: #94a3b8;
            --border: #334155;
            --success: #22c55e;
            --success-light: #14532d;
            --warning: #f59e0b;
            --error: #ef4444;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        header {
            background: linear-gradient(135deg, #1e3a5f, #1e293b);
            color: white;
            padding: 0.25rem 0;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }

        header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        header a:not(.btn) {
            color: white;
            text-decoration: none;
            opacity: 0.9;
            transition: opacity 0.15s;
        }

        header a:not(.btn):hover {
            opacity: 1;
        }

        .btn.btn-nav {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 400;
            line-height: normal;
            text-decoration: none;
            box-sizing: border-box;
            font-family: inherit;
        }

        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }

        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--text);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text);
        }

        .form-group small {
            display: block;
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }

        input[type="text"], input[type="url"], textarea, select {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 1rem;
            background: #0f172a;
            color: var(--text);
            transition: border-color 0.15s, box-shadow 0.15s;
        }

        input[type="text"]:focus, input[type="url"]:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        ::placeholder {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            opacity: 1;
        }

        #audience {
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            background: var(--card) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E") no-repeat right 0.625rem center / 12px;
        }

        .drop-zone {
            border: 2px dashed var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.15s, background-color 0.15s;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .drop-zone:hover, .drop-zone.drag-over {
            border-color: var(--primary);
            background-color: var(--primary-light);
        }

        .drop-zone {
            background: #0f172a;
        }

        .logo-preview {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-top: 0.75rem;
            padding: 0.5rem 0.75rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        .logo-preview img {
            max-height: 60px;
            max-width: 120px;
            object-fit: contain;
        }

        .logo-preview .logo-filename {
            flex: 1;
            font-size: 0.875rem;
            color: var(--text-secondary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .logo-remove-btn {
            background: none;
            border: 1px solid var(--border);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 1.1rem;
            padding: 0.15rem 0.5rem;
            line-height: 1;
            transition: color 0.15s, border-color 0.15s;
        }

        .logo-remove-btn:hover {
            color: #e74c3c;
            border-color: #e74c3c;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s, transform 0.1s;
        }

        .btn:hover {
            background: var(--primary-dark);
        }

        .btn:active {
            transform: scale(0.98);
        }

        .btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
        }

        .btn-secondary {
            background: var(--bg);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .radio-group {
            display: flex;
            gap: 1rem;
        }

        .radio-option {
            flex: 1;
            padding: 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .radio-option:hover {
            border-color: var(--primary-light);
        }

        .radio-option.selected {
            border-color: var(--primary);
            background: var(--primary-light);
        }

        .radio-option input {
            display: none;
        }

        .radio-option h4 {
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }

        .radio-option p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin: 0;
        }

        /* Progress page styles */
        .progress-container {
            max-width: 800px;
            margin: 3rem auto;
        }

        .progress-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .progress-header h2 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }

        .progress-header p {
            color: var(--text-secondary);
        }

        .phase-list {
            list-style: none;
        }

        .phase-item {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            padding: 1.25rem;
            background: var(--card);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }

        .phase-item.active {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .phase-item.completed {
            border-color: var(--success);
            background: var(--success-light);
        }

        .phase-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
        }

        .phase-item.pending .phase-icon {
            background: var(--border);
            color: var(--text-secondary);
        }

        .phase-item.active .phase-icon {
            background: var(--primary);
            color: white;
            animation: pulse 1.5s infinite;
        }

        .phase-item.completed .phase-icon {
            background: var(--success);
            color: white;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .phase-content {
            flex: 1;
        }

        .phase-content h4 {
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }

        .phase-content p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin: 0;
        }

        .phase-progress {
            margin-top: 0.75rem;
        }

        .progress-bar {
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary);
            border-radius: 3px;
            transition: width 0.3s;
        }

        .progress-text {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Results page - sidebar layout */
        .results-layout {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 2rem;
            min-height: calc(100vh - 200px);
        }

        .sidebar {
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 1rem;
        }

        .sidebar h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }

        .nav-list {
            list-style: none;
            margin-bottom: 1.5rem;
        }

        .nav-list li {
            margin-bottom: 0.25rem;
        }

        .nav-list a {
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--text);
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.875rem;
            transition: all 0.15s;
        }

        .nav-list a:hover {
            background: var(--bg);
            color: var(--primary);
        }

        .nav-list a.active {
            background: var(--primary);
            color: white;
        }

        .download-btn {
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
        }

        .download-btn:hover {
            background: var(--primary);
            color: white;
        }

        .download-btn .size {
            margin-left: auto;
            opacity: 0.6;
            font-size: 0.75rem;
        }

        .content {
            background: var(--card);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        /* Markdown content styling */
        .markdown-content h1 { font-size: 1.75rem; margin-top: 0; margin-bottom: 1rem; }
        .markdown-content h2 { font-size: 1.5rem; margin-top: 2rem; margin-bottom: 0.75rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; }
        .markdown-content h3 { font-size: 1.25rem; margin-top: 1.5rem; margin-bottom: 0.5rem; }
        .markdown-content h4 { font-size: 1.1rem; margin-top: 1.25rem; margin-bottom: 0.5rem; }

        .markdown-content p { margin-bottom: 1rem; }

        .markdown-content ul, .markdown-content ol {
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }

        .markdown-content li { margin-bottom: 0.5rem; }

        .markdown-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-size: 0.9rem;
        }

        .markdown-content th, .markdown-content td {
            padding: 0.75rem 1rem;
            text-align: left;
            border: 1px solid var(--border);
        }

        .markdown-content th {
            background: var(--bg);
            font-weight: 600;
        }

        .markdown-content code {
            background: var(--bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875em;
        }

        .markdown-content pre {
            background: #0f172a;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }

        .markdown-content pre code {
            background: none;
            padding: 0;
            color: inherit;
        }

        .markdown-content blockquote {
            border-left: 4px solid var(--primary);
            padding-left: 1rem;
            margin: 1rem 0;
            color: var(--text-secondary);
        }

        .markdown-content hr {
            border: none;
            border-top: 1px solid var(--border);
            margin: 2rem 0;
        }

        /* Diagrams grid */
        .diagrams-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
        }

        .diagram-card {
            background: var(--bg);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }

        .diagram-card img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .diagram-card img:hover {
            transform: scale(1.02);
        }

        .diagram-card h4 {
            margin: 0;
            font-size: 0.875rem;
        }

        /* Stats header */
        .stats-bar {
            display: flex;
            gap: 2rem;
            padding: 1rem 1.5rem;
            background: var(--card);
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }

        .stat-item {
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--primary);
        }

        .stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        /* Home page sidebar layout — matches results-layout */
        .home-layout {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 2rem;
            min-height: calc(100vh - 200px);
        }

        .analyses-sidebar {
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 1rem;
        }

        .analyses-sidebar h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }

        .sidebar-search {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.875rem;
            margin-bottom: 0.75rem;
            background: #0f172a;
            color: var(--text);
            transition: border-color 0.15s, box-shadow 0.15s;
        }

        .sidebar-search:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .sidebar-list {
            max-height: calc(100vh - 350px);
            overflow-y: auto;
        }

        .sidebar-company-card {
            display: block;
            padding: 0.75rem;
            border-radius: 6px;
            text-decoration: none;
            color: var(--text);
            transition: background 0.15s;
            border-bottom: 1px solid var(--border);
            position: relative;
        }

        .sidebar-company-card:last-child {
            border-bottom: none;
        }

        .sidebar-company-card:hover {
            background: var(--bg);
        }

        .delete-btn {
            position: absolute;
            top: calc(0.5rem + 3px);
            right: 0.5rem;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: none;
            background: transparent;
            color: #ef4444;
            font-size: 16px;
            line-height: 1;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.15s, background 0.15s;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
        }

        .delete-btn:hover {
            background: rgba(239, 68, 68, 0.15);
        }

        .sidebar-company-card:hover .delete-btn {
            opacity: 1;
        }

        .sidebar-company-name {
            font-weight: 500;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .sidebar-company-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .sidebar-phase {
            text-transform: capitalize;
        }

        .sidebar-progress {
            font-weight: 600;
            color: var(--success);
        }

        .sidebar-empty {
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-align: center;
            padding: 1rem;
        }

        .home-main {
            min-width: 0;
            max-width: 700px;
        }

        @media (max-width: 900px) {
            .results-layout {
                grid-template-columns: 1fr;
            }

            .sidebar {
                position: relative;
                top: 0;
            }

            .home-layout {
                grid-template-columns: 1fr;
            }

            .analyses-sidebar {
                width: 100%;
                position: relative;
                top: 0;
                order: 2;
            }

            .home-main {
                order: 1;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <a href="/" style="display: flex; align-items: center; gap: 0.4rem; text-decoration: none;"><img src="/assets/SMB-AI-logo.png" alt="SMB AI Logo" style="height: 72px; width: auto;"><h1>SMB AI Strategy <span style="font-style: italic; color: #3b82f6; font-size: 1.5625rem;">Audit</span></h1></a>
            <nav>
                <a href="/" class="btn btn-nav">New Analysis</a>
            </nav>
        </div>
    </header>

    <div class="container">
        {{ content|safe }}
    </div>

    {{ scripts|safe }}
</body>
</html>
"""

HOME_CONTENT = """
<div class="home-layout">
    <aside class="analyses-sidebar">
        <h3>Previous Analyses</h3>
        <div style="position: relative;">
            <svg style="position: absolute; left: 0.6rem; top: calc(50% - 7px); transform: translateY(-50%); pointer-events: none; opacity: 0.5;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" class="sidebar-search" placeholder="Search analyses..." id="sidebar-search" style="padding-left: calc(2.2rem - 4px);">
        </div>
        <div class="sidebar-list" id="sidebar-list">
            {% for company in companies %}
            <a href="/results/{{ company.slug }}" class="sidebar-company-card" data-name="{{ company.name|lower }}">
                <div class="sidebar-company-name">{{ company.name }}</div>
                <div class="sidebar-company-meta">
                    <span class="sidebar-phase">{{ company.phase }}</span>
                    <span class="sidebar-progress">{{ "%.0f"|format(company.progress) }}%</span>
                </div>
                <span class="delete-btn" data-slug="{{ company.slug }}" title="Delete analysis">&times;</span>
            </a>
            {% endfor %}
            {% if not companies %}
            <p class="sidebar-empty">No analyses yet</p>
            {% endif %}
        </div>
    </aside>

    <div class="home-main">
            <div class="card">
                <h2>Generate AI Strategy Deliverables</h2>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                    Enter a company name to generate comprehensive AI strategy documents including
                    roadmaps, maturity assessments, ROI analysis, and implementation guides.
                </p>

                <form id="analysis-form" action="/start" method="POST" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="company">Company Name *</label>
                        <input type="text" id="company" name="company" placeholder="e.g., Stripe, Airbnb, Shopify" required>
                    </div>

                    <div class="form-group">
                        <label for="website">Company Website</label>
                        <input type="url" id="website" name="website"
                               placeholder="e.g., https://stripe.com">
                    </div>

                    <div class="form-group">
                        <label for="industry">Industry</label>
                        <input type="text" id="industry" name="industry"
                               placeholder="e.g., landscaping, plumbing, restaurant">
                        <small>Leave blank to auto-detect from company name and context.</small>
                    </div>

                    <div class="form-group">
                        <label for="logo">Company Logo</label>
                        <div class="drop-zone" id="logo-drop-zone">
                            Drag & drop a logo here, or click to browse
                            <input type="file" id="logo" name="logo" accept="image/png,image/jpeg,image/webp,image/svg+xml" style="display: none;">
                        </div>
                        <div id="logo-preview" class="logo-preview" style="display: none;">
                            <img id="logo-thumb" src="" alt="Logo preview">
                            <span class="logo-filename" id="logo-filename"></span>
                            <button type="button" class="logo-remove-btn" id="logo-remove">&times;</button>
                        </div>
                        <small>PNG, JPG, or SVG — max 5 MB. Auto-extracted if you provide a website above.</small>
                    </div>

                    <div class="form-group">
                        <label for="context">Additional Context</label>
                        <textarea id="context" name="context" placeholder="Optional: Industry, company size, specific goals, current tech stack, etc."></textarea>
                        <small style="margin-top: -4px;">Make the analysis specific to your situation.</small>
                    </div>

                    <div class="form-group">
                        <label for="audience" style="display: flex; align-items: center; justify-content: space-between;">Business Context <a href="/audience-builder" style="font-weight: 500; font-size: 0.875rem; padding: 0.35rem 0.85rem; background: #f97316; color: white; border-radius: 6px; text-decoration: none;">Create New Profile</a></label>
                        <select id="audience" name="audience" style="width: 100%; padding: 0.75rem; border: 2px solid var(--border); border-radius: 8px; font-size: 1rem; color: var(--text);">
                            <option value="">General</option>
                            {% for aud in audiences %}
                            <option value="{{ aud.id }}">{{ aud.name }}</option>
                            {% endfor %}
                        </select>
                        <small>Select a profile to inject regional/cultural context into deliverables.</small>
                    </div>

                    <button type="submit" class="btn" style="width: 100%;">
                        Start Analysis
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
"""

HOME_SCRIPTS = """
<script>
    // Sidebar search filtering
    const searchInput = document.getElementById('sidebar-search');
    const sidebarList = document.getElementById('sidebar-list');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            sidebarList.querySelectorAll('.sidebar-company-card').forEach(card => {
                const name = card.dataset.name;
                card.style.display = name.includes(query) ? '' : 'none';
            });
        });
    }

    // Delete analysis handler
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const slug = this.dataset.slug;
            const card = this.closest('.sidebar-company-card');
            const name = card.querySelector('.sidebar-company-name').textContent;
            if (confirm('Delete analysis for ' + name + '?')) {
                fetch('/api/delete/' + slug, { method: 'DELETE' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            card.style.transition = 'opacity 0.3s, transform 0.3s';
                            card.style.opacity = '0';
                            card.style.transform = 'translateX(-20px)';
                            setTimeout(() => card.remove(), 300);
                            // Show "No analyses yet" if list is empty
                            const list = document.getElementById('sidebar-list');
                            if (!list.querySelector('.sidebar-company-card')) {
                                list.innerHTML = '<p class="sidebar-empty">No analyses yet</p>';
                            }
                        }
                    });
            }
        });
    });

    document.querySelectorAll('.radio-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.radio-option').forEach(o => o.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input').checked = true;
        });
    });

    // Logo drag-and-drop
    const dropZone = document.getElementById('logo-drop-zone');
    const logoInput = document.getElementById('logo');
    const logoPreview = document.getElementById('logo-preview');
    const logoThumb = document.getElementById('logo-thumb');
    const logoFilename = document.getElementById('logo-filename');
    const logoRemove = document.getElementById('logo-remove');

    const MAX_LOGO_SIZE = 5 * 1024 * 1024; // 5 MB
    const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'];

    dropZone.addEventListener('click', () => logoInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleLogoFile(e.dataTransfer.files[0]);
        }
    });

    logoInput.addEventListener('change', () => {
        if (logoInput.files.length) {
            handleLogoFile(logoInput.files[0]);
        }
    });

    logoRemove.addEventListener('click', () => {
        logoInput.value = '';
        logoPreview.style.display = 'none';
        dropZone.style.display = '';
    });

    function handleLogoFile(file) {
        if (!ALLOWED_TYPES.includes(file.type)) {
            alert('Please upload a PNG, JPG, or SVG image.');
            return;
        }
        if (file.size > MAX_LOGO_SIZE) {
            alert('Logo must be under 5 MB.');
            return;
        }
        // Set the file on the input (needed for form submission when dropped)
        const dt = new DataTransfer();
        dt.items.add(file);
        logoInput.files = dt.files;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            logoThumb.src = e.target.result;
            logoFilename.textContent = file.name;
            logoPreview.style.display = 'flex';
            dropZone.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
</script>
"""

PROGRESS_CONTENT = """
<div class="progress-container">
    <div class="progress-header">
        <h2>Analyzing {{ company_name }}</h2>
        <p id="status-text">Initializing...</p>
    </div>

    <div class="card">
        <ul class="phase-list" id="phase-list">
            <li class="phase-item active" id="phase-research">
                <div class="phase-icon"><div class="spinner"></div></div>
                <div class="phase-content">
                    <h4>Research Phase</h4>
                    <p id="research-status">Gathering company intelligence...</p>
                    <div class="phase-progress">
                        <div class="progress-bar"><div class="progress-fill" id="research-progress" style="width: 0%"></div></div>
                        <div class="progress-text" id="research-text">Starting...</div>
                    </div>
                </div>
            </li>
            <li class="phase-item pending" id="phase-synthesis">
                <div class="phase-icon">2</div>
                <div class="phase-content">
                    <h4>Synthesis Phase</h4>
                    <p id="synthesis-status">Waiting...</p>
                    <div class="phase-progress" style="display: none;">
                        <div class="progress-bar"><div class="progress-fill" id="synthesis-progress" style="width: 0%"></div></div>
                        <div class="progress-text" id="synthesis-text"></div>
                    </div>
                </div>
            </li>
            <li class="phase-item pending" id="phase-generation">
                <div class="phase-icon">3</div>
                <div class="phase-content">
                    <h4>Document Generation</h4>
                    <p id="generation-status">Waiting...</p>
                    <div class="phase-progress" style="display: none;">
                        <div class="progress-bar"><div class="progress-fill" id="generation-progress" style="width: 0%"></div></div>
                        <div class="progress-text" id="generation-text"></div>
                    </div>
                </div>
            </li>
        </ul>
    </div>

    <div id="error-container" style="display: none;">
        <div class="card" style="border-color: var(--error); background: #450a0a;">
            <h3 style="color: var(--error);">Error</h3>
            <p id="error-message"></p>
            <a href="/" class="btn btn-secondary" style="margin-top: 1rem;">Try Again</a>
        </div>
    </div>
</div>
"""

PROGRESS_SCRIPTS = """
<script>
    const jobId = '{{ job_id }}';
    let eventSource;

    function updatePhase(phaseId, status, isActive, isCompleted) {
        const phase = document.getElementById('phase-' + phaseId);
        phase.classList.remove('pending', 'active', 'completed');

        if (isCompleted) {
            phase.classList.add('completed');
            phase.querySelector('.phase-icon').innerHTML = '&#10003;';
        } else if (isActive) {
            phase.classList.add('active');
            phase.querySelector('.phase-icon').innerHTML = '<div class="spinner"></div>';
            phase.querySelector('.phase-progress').style.display = 'block';
        } else {
            phase.classList.add('pending');
        }

        document.getElementById(phaseId + '-status').textContent = status;
    }

    function updateProgress(phaseId, progress, text) {
        document.getElementById(phaseId + '-progress').style.width = progress + '%';
        document.getElementById(phaseId + '-text').textContent = text;
    }

    function startEventStream() {
        eventSource = new EventSource('/progress/' + jobId);

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Progress update:', data);

            document.getElementById('status-text').textContent = data.message || 'Processing...';

            if (data.phase === 'research') {
                updatePhase('research', data.status || 'Researching...', true, data.completed);
                if (data.progress !== undefined) {
                    updateProgress('research', data.progress, data.detail || '');
                }
            } else if (data.phase === 'synthesis') {
                updatePhase('research', 'Complete', false, true);
                updatePhase('synthesis', data.status || 'Synthesizing...', true, data.completed);
                if (data.progress !== undefined) {
                    updateProgress('synthesis', data.progress, data.detail || '');
                }
            } else if (data.phase === 'generation') {
                updatePhase('synthesis', 'Complete', false, true);
                updatePhase('generation', data.status || 'Generating...', true, data.completed);
                if (data.progress !== undefined) {
                    updateProgress('generation', data.progress, data.detail || '');
                }
            }

            if (data.complete) {
                eventSource.close();
                updatePhase('generation', 'Complete', false, true);
                document.getElementById('status-text').textContent = 'Analysis complete!';
                setTimeout(() => {
                    window.location.href = '/results/' + data.company_slug;
                }, 1000);
            }

            if (data.error) {
                eventSource.close();
                document.getElementById('error-container').style.display = 'block';
                document.getElementById('error-message').textContent = data.error;
                document.getElementById('status-text').textContent = 'Error occurred';
            }
        };

        eventSource.onerror = function(err) {
            console.error('EventSource error:', err);
        };
    }

    startEventStream();
</script>
"""


# =============================================================================
# Routes
# =============================================================================

@app.route('/')
def home():
    """Home page with form to start new analysis."""
    # Get list of previous analyses
    companies = []
    if OUTPUT_DIR.exists():
        for item in OUTPUT_DIR.iterdir():
            if item.is_dir() and (item / "state.json").exists():
                try:
                    tracker = ProgressTracker(item.name)
                    summary = tracker.get_progress_summary()
                    companies.append({
                        "name": summary["company_name"],
                        "slug": item.name,
                        "phase": summary["current_phase"],
                        "progress": summary["deliverables"]["progress_percent"],
                        "cost": summary["costs"]["total"],
                    })
                except:
                    pass

    from jinja2 import Template
    from strategy_factory.audience_loader import get_audience_loader
    audiences = get_audience_loader().available_audiences
    content = Template(HOME_CONTENT).render(
        companies=sorted(companies, key=lambda x: x["name"]),
        audiences=audiences,
    )

    return render_template_string(
        BASE_TEMPLATE,
        title="Home",
        content=content,
        scripts=HOME_SCRIPTS
    )


@app.route('/api/delete/<company_slug>', methods=['DELETE'])
def delete_analysis(company_slug):
    """Delete a company analysis and all its files."""
    company_dir = OUTPUT_DIR / company_slug
    if not company_dir.exists() or not company_dir.is_dir():
        return jsonify({"success": False, "error": "Analysis not found"}), 404
    # Safety: only delete directories that contain state.json
    if not (company_dir / "state.json").exists():
        return jsonify({"success": False, "error": "Invalid analysis directory"}), 400
    shutil.rmtree(company_dir)
    return jsonify({"success": True})


@app.route('/start', methods=['POST'])
def start_analysis():
    """Start a new analysis job."""
    company_name = request.form.get('company', '').strip()
    industry = request.form.get('industry', '').strip()
    context = request.form.get('context', '').strip()
    audience = request.form.get('audience', '').strip() or None
    website = request.form.get('website', '').strip()

    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    # Generate a job ID
    job_id = str(uuid.uuid4())[:8]
    company_slug = slugify(company_name)

    # Handle logo upload
    logo_path_str = None
    logo_file = request.files.get('logo')
    if logo_file and logo_file.filename:
        filename = secure_filename(logo_file.filename)
        ext = Path(filename).suffix.lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
            logo_dir = OUTPUT_DIR / company_slug / "logo"
            logo_dir.mkdir(parents=True, exist_ok=True)
            if ext == '.webp':
                # Convert WebP to PNG so all generators can handle it
                from PIL import Image as PILImage
                import io
                webp_bytes = logo_file.read()
                img = PILImage.open(io.BytesIO(webp_bytes)).convert("RGBA")
                png_filename = Path(filename).stem + ".png"
                logo_save_path = logo_dir / png_filename
                img.save(str(logo_save_path), "PNG")
            elif ext == '.svg':
                try:
                    import cairosvg
                except ImportError:
                    return jsonify({"error": "SVG support requires cairosvg. Install with: pip install cairosvg (also needs system cairo: brew install cairo)"}), 400
                svg_bytes = logo_file.read()
                png_filename = Path(filename).stem + ".png"
                logo_save_path = logo_dir / png_filename
                cairosvg.svg2png(bytestring=svg_bytes, write_to=str(logo_save_path))
            else:
                logo_save_path = logo_dir / filename
                logo_file.save(str(logo_save_path))
            logo_path_str = str(logo_save_path)

    # Auto-extract logo from website if no manual upload
    if not logo_path_str and website:
        from strategy_factory.logo_extractor import extract_logo_from_url
        logo_dir = OUTPUT_DIR / company_slug / "logo"
        logo_path_str = extract_logo_from_url(website, logo_dir)

    # Create job entry
    active_jobs[job_id] = {
        "company_name": company_name,
        "company_slug": company_slug,
        "context": context,
        "audience": audience,
        "status": "starting",
        "progress_queue": queue.Queue(),
        "started_at": datetime.now(),
    }

    # Start the pipeline in a background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, company_name, context, logo_path_str, audience, website, industry),
        daemon=True
    )
    thread.start()

    # Redirect to progress page
    from jinja2 import Template
    content = Template(PROGRESS_CONTENT).render(company_name=company_name)
    scripts = Template(PROGRESS_SCRIPTS).render(job_id=job_id)

    return render_template_string(
        BASE_TEMPLATE,
        title=f"Analyzing {company_name}",
        content=content,
        scripts=scripts
    )


@app.route('/progress/<job_id>')
def progress_stream(job_id):
    """Server-Sent Events stream for progress updates."""
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        job = active_jobs[job_id]
        q = job["progress_queue"]

        while True:
            try:
                # Wait for progress update
                update = q.get(timeout=30)
                yield f"data: {json.dumps(update)}\n\n"

                if update.get("complete") or update.get("error"):
                    break
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'keepalive': True})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/results/<company_slug>')
def results(company_slug):
    """View results for a company."""
    output_dir = OUTPUT_DIR / company_slug

    if not output_dir.exists():
        return "Company not found", 404

    tracker = ProgressTracker(company_slug)
    summary = tracker.get_progress_summary()

    # Get markdown files, ordered by DELIVERABLES config
    markdown_files = []
    markdown_dir = output_dir / "markdown"
    if markdown_dir.exists():
        md_on_disk = {f.stem: f.name for f in markdown_dir.glob("*.md")}
        for d_id, d_cfg in DELIVERABLES.items():
            if d_cfg.get("format") == "markdown" and d_id in md_on_disk:
                markdown_files.append({
                    "name": d_cfg["name"],
                    "filename": md_on_disk[d_id],
                })

    documents = []
    docs_dir = output_dir / "documents"
    if docs_dir.exists():
        for doc_file in sorted(docs_dir.glob("*.docx")):
            documents.append({
                "name": doc_file.stem.replace("_", " ").title(),
                "filename": doc_file.name,
                "size": f"{doc_file.stat().st_size / 1024:.1f} KB",
                "icon": "📄",
            })
        for doc_file in sorted(docs_dir.glob("*.pdf")):
            documents.append({
                "name": doc_file.stem.replace("_", " ").title(),
                "filename": doc_file.name,
                "size": f"{doc_file.stat().st_size / 1024:.1f} KB",
                "icon": "📕",
            })

    content = render_results_page(
        company_name=summary["company_name"],
        company_slug=company_slug,
        total_cost=summary["costs"]["total"],
        markdown_files=markdown_files,
        documents=documents,
    )

    return render_template_string(
        BASE_TEMPLATE,
        title=summary["company_name"],
        content=content,
        scripts=RESULTS_SCRIPTS
    )


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


def fix_malformed_tables(content: str) -> str:
    """Fix malformed markdown tables with overly long separator rows."""
    import re
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this looks like a table header row (has multiple | but not a separator)
        if line.count('|') >= 2 and not re.match(r'^\s*\|[\s\-:]+\|', line):
            cols = [c.strip() for c in line.split('|')]
            cols = [c for c in cols if c]
            num_cols = len(cols)

            if num_cols >= 2:
                # Check if next line is a malformed separator
                if i + 1 < len(lines) and _is_separator_row(lines[i + 1]):
                    # Create proper separator
                    separator = '|' + '|'.join([' --- ' for _ in range(num_cols)]) + '|'
                    fixed_lines.append(line)
                    fixed_lines.append(separator)
                    i += 2
                    continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)


@app.route('/api/markdown/<company_slug>/<filename>')
def get_markdown(company_slug, filename):
    """Get rendered markdown content."""
    md_path = OUTPUT_DIR / company_slug / "markdown" / filename

    if not md_path.exists():
        return "File not found", 404

    with open(md_path, "r") as f:
        content = f.read()

    # Remove YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    # Fix malformed tables
    content = fix_malformed_tables(content)

    # Convert markdown to HTML
    html = markdown.markdown(
        content,
        extensions=[
            TableExtension(),
            FencedCodeExtension(),
            TocExtension(),
            'nl2br'
        ]
    )

    return f'<div class="markdown-content">{html}</div>'


@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve project asset files (logos, images)."""
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    return send_from_directory(assets_dir, filename)


@app.route('/files/<company_slug>/<path:filepath>')
def serve_file(company_slug, filepath):
    """Serve static files (images, presentations, documents)."""
    directory = OUTPUT_DIR / company_slug
    return send_from_directory(directory, filepath)


def render_results_page(company_name, company_slug, total_cost, markdown_files, documents):
    """Render the results page HTML."""
    html = f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-value">{len(markdown_files)}</div>
            <div class="stat-label">Deliverables</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${total_cost:.2f}</div>
            <div class="stat-label">Total Cost</div>
        </div>
        <div class="stat-item" style="margin-left: auto;">
            <div class="stat-value" style="font-size: 1.25rem;">{company_name}</div>
            <div class="stat-label">Company</div>
        </div>
    </div>

    <div class="results-layout">
        <aside class="sidebar">
            <h3>Strategy Documents</h3>
            <ul class="nav-list" id="doc-list">
    """

    for md in markdown_files:
        html += f'<li><a href="#" data-file="{md["filename"]}" class="doc-link">{md["name"]}</a></li>\n'

    html += """
            </ul>
    """

    if documents:
        html += '<h3>Final Documents</h3>\n'
        for doc in documents:
            icon = doc.get("icon", "📄")
            html += f'<a href="/files/{company_slug}/documents/{doc["filename"]}" class="download-btn" download>{icon} {doc["name"]}<span class="size">{doc["size"]}</span></a>\n'

    html += f"""
        </aside>

        <main class="content" id="content">
            <div style="text-align: center; padding: 3rem;">
                <h2>Welcome to {company_name}'s AI Strategy</h2>
                <p style="color: var(--text-secondary); max-width: 500px; margin: 1rem auto 2rem;">
                    Select a document from the sidebar to view the analysis, or download the final documents.
                </p>
            </div>
        </main>
    </div>

    <script>
        const companySlug = '{company_slug}';
    </script>
    """

    return html


AUDIENCE_BUILDER_CONTENT = """
<div style="max-width: 700px; margin: 2rem auto;">
    <div class="card">
        <h2>Business Context Profile Builder</h2>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            Describe a business vertical and region. AI will research and generate a context profile you can edit before saving.
        </p>

        <div id="chat-container" style="border: 1px solid var(--border); border-radius: 8px; margin-bottom: 1rem;">
            <div id="chat-messages" style="padding: 1rem; min-height: 200px; max-height: 400px; overflow-y: auto;">
            </div>
            <div style="border-top: 1px solid var(--border); padding: 0.75rem; display: flex; gap: 0.5rem;">
                <input type="text" id="chat-input" placeholder="e.g., plumbers in Western North Carolina" style="flex: 1;">
                <button type="button" class="btn" id="send-btn" onclick="sendMessage()">Submit</button>
            </div>
        </div>

        <div id="draft-section" style="display: none; margin-top: 1rem;">
            <div class="form-group">
                <label for="draft-editor">Generated Business Context <small>(edit before saving)</small></label>
                <textarea id="draft-editor" rows="8" style="width: 100%; font-family: monospace; font-size: 0.9rem; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; resize: vertical;"></textarea>
            </div>
        </div>

        <div id="save-section" style="display: none; margin-top: 1rem;">
            <div class="form-group">
                <label for="audience-name">Profile Name</label>
                <input type="text" id="audience-name" placeholder="e.g. Plumbers WNC">
                <small>This becomes the display name in the Business Context dropdown.</small>
            </div>
            <button type="button" class="btn" id="save-btn" onclick="saveAudience()">Save Profile</button>
        </div>

        <div id="save-success" style="display: none; padding: 1rem; background: var(--success-light); border-radius: 8px; margin-top: 1rem;">
            <strong>Saved!</strong> <span id="save-message"></span>
            <br><a href="/" style="color: var(--primary);">Return to main page to use this profile.</a>
        </div>

        <div id="save-error" style="display: none; padding: 1rem; background: #450a0a; border-radius: 8px; margin-top: 1rem; color: var(--error);">
            <strong>Error:</strong> <span id="error-text"></span>
        </div>
    </div>

    <div style="text-align: center; margin-top: 1rem;">
        <a href="/" style="color: var(--text-secondary);">&larr; Back to main page</a>
    </div>
</div>
"""

AUDIENCE_BUILDER_SCRIPTS = """
<script>
    let chatHistory = [];

    function appendMessage(role, content) {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.style.marginBottom = '0.75rem';
        div.style.padding = '0.5rem 0.75rem';
        div.style.borderRadius = '6px';
        div.style.background = role === 'user' ? 'var(--primary-light)' : '#334155';
        div.innerHTML = '<strong>' + (role === 'user' ? 'You' : 'AI') + ':</strong> ' + content.replace(/\\n/g, '<br>');
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const msg = input.value.trim();
        if (!msg) return;

        input.value = '';
        document.getElementById('send-btn').disabled = true;
        appendMessage('user', msg);
        chatHistory.push({role: 'user', content: msg});

        try {
            const resp = await fetch('/audience-builder/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({history: chatHistory})
            });
            const data = await resp.json();

            if (data.error) {
                document.getElementById('save-error').style.display = 'block';
                document.getElementById('error-text').textContent = data.error;
            } else {
                appendMessage('assistant', data.reply);
                chatHistory.push({role: 'assistant', content: data.reply});

                if (data.draft_text) {
                    document.getElementById('draft-section').style.display = 'block';
                    document.getElementById('draft-editor').value = data.draft_text;
                }

                if (data.ready_to_save) {
                    document.getElementById('save-section').style.display = 'block';
                    if (data.suggested_name && !document.getElementById('audience-name').value) {
                        document.getElementById('audience-name').value = data.suggested_name;
                    }
                }
            }
        } catch(e) {
            document.getElementById('save-error').style.display = 'block';
            document.getElementById('error-text').textContent = 'Network error: ' + e.message;
        }

        document.getElementById('send-btn').disabled = false;
        document.getElementById('chat-input').focus();
    }

    async function saveAudience() {
        const name = document.getElementById('audience-name').value.trim();
        if (!name) {
            alert('Please enter a profile name.');
            return;
        }

        const draftText = document.getElementById('draft-editor').value.trim();
        if (!draftText) {
            alert('No draft to save. Generate one first.');
            return;
        }

        const saveBtn = document.getElementById('save-btn');
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const resp = await fetch('/audience-builder/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, draft_text: draftText, history: chatHistory})
            });
            const data = await resp.json();

            if (data.error) {
                document.getElementById('save-error').style.display = 'block';
                document.getElementById('error-text').textContent = data.error;
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Profile';
            } else {
                document.getElementById('save-section').style.display = 'none';
                document.getElementById('draft-section').style.display = 'none';
                document.getElementById('save-success').style.display = 'block';
                document.getElementById('save-message').textContent = 'Profile "' + data.name + '" saved successfully.';
            }
        } catch(e) {
            document.getElementById('save-error').style.display = 'block';
            document.getElementById('error-text').textContent = 'Network error: ' + e.message;
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Profile';
        }
    }

    document.getElementById('chat-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
</script>
"""

RESULTS_SCRIPTS = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Document links
        document.querySelectorAll('.doc-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const filename = this.getAttribute('data-file');

                // Update active state
                document.querySelectorAll('.doc-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');

                // Load content
                fetch('/api/markdown/' + companySlug + '/' + filename)
                    .then(response => response.text())
                    .then(html => {
                        document.getElementById('content').innerHTML = html;
                    })
                    .catch(err => {
                        document.getElementById('content').innerHTML = '<p>Error loading content.</p>';
                    });
            });
        });

        // Load first document by default
        const firstDoc = document.querySelector('.doc-link');
        if (firstDoc) firstDoc.click();
    });
</script>
"""


@app.route('/audience-builder')
def audience_builder():
    """Business context profile builder page."""
    return render_template_string(
        BASE_TEMPLATE,
        title="Business Context Profile Builder",
        content=AUDIENCE_BUILDER_CONTENT,
        scripts=AUDIENCE_BUILDER_SCRIPTS
    )


@app.route('/audience-builder/chat', methods=['POST'])
def audience_builder_chat():
    """Chat endpoint for business context profile generation via Gemini, enriched with Perplexity research."""
    import re as _re
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    history = data.get('history', [])
    if not history or history[-1].get('role') != 'user':
        return jsonify({"error": "No user message provided"}), 400

    try:
        from strategy_factory.synthesis.gemini_client import GeminiClient
        client = GeminiClient()

        system_instruction = (
            "You are generating a business context profile for an AI strategy tool used by small business consultants. "
            "You will receive a short description of a business vertical and region (e.g., 'plumbers in Western North Carolina' "
            "or 'lawyers in St. Louis'). Your job is to enrich it with specific, actionable regional and vertical context "
            "that web research cannot easily surface for individual companies. Cover: regional economy drivers, typical "
            "business structure (owner-only vs staff, revenue range), local regulatory or licensing specifics, cultural "
            "or community factors, industry-specific challenges in that geography, and growth patterns common to that "
            "vertical in that region. Be specific — name real conditions, not generic advice. Write in a single flowing "
            "paragraph, under 100 words. If the user sends a follow-up message, revise the paragraph to incorporate their feedback. "
            "On the first response, also suggest a short profile name (5 words or less) on its own line prefixed with "
            "'Suggested name: '. Keep the paragraph itself separate from the name suggestion with a line break between them."
        )

        # Build full conversation as a single prompt
        conversation = ""
        for turn in history:
            role_label = "User" if turn['role'] == 'user' else "Assistant"
            conversation += f"{role_label}: {turn['content']}\n\n"
        conversation += "Assistant:"

        # Count user turns
        user_turns = sum(1 for h in history if h['role'] == 'user')

        # On first user message, enrich with Perplexity research
        if user_turns == 1:
            try:
                from strategy_factory.research.perplexity_client import PerplexityClient
                from strategy_factory.config import PerplexityModel
                pplx = PerplexityClient()
                user_desc = history[-1]['content']

                research_queries = [
                    f"{user_desc} typical business structure revenue range challenges",
                    f"{user_desc} regional market conditions regulatory requirements",
                    f"AI adoption trends {user_desc} small business",
                ]

                research_context = ""
                for q in research_queries:
                    try:
                        result = pplx.search(query=q, max_results=5, model=PerplexityModel.SONAR)
                        snippets = "; ".join(r.snippet for r in result.results[:3] if r.snippet)
                        research_context += f"- {q}: {snippets}\n"
                    except Exception:
                        pass  # Graceful degradation — generate without this query if it fails

                if research_context:
                    conversation = f"Research findings about '{user_desc}':\n{research_context}\n\n{conversation}"
            except Exception:
                pass  # Graceful degradation — generate without research if Perplexity unavailable

        result = client.generate(
            prompt=conversation,
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=2048,
        )

        reply = result.content.strip()
        ready_to_save = user_turns >= 1

        suggested_name = None
        name_match = _re.search(r'[Ss]uggested name:\s*["\']?([^"\'\n]+)["\']?', reply)
        if name_match:
            suggested_name = name_match.group(1).strip().rstrip('.')

        # Extract paragraph (everything before "Suggested name:" line)
        draft_text = reply
        name_line_match = _re.search(r'\n[Ss]uggested name:.*', draft_text)
        if name_line_match:
            draft_text = draft_text[:name_line_match.start()].strip()

        return jsonify({
            "reply": reply,
            "draft_text": draft_text,
            "turn_count": user_turns,
            "ready_to_save": ready_to_save,
            "suggested_name": suggested_name,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/audience-builder/save', methods=['POST'])
def audience_builder_save():
    """Save a business context profile from edited draft or chat history."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Audience name is required"}), 400

    try:
        from strategy_factory.progress_tracker import slugify
        from strategy_factory.audience_loader import AUDIENCE_DIR
        import strategy_factory.audience_loader as _al_module

        draft_text = data.get('draft_text', '').strip()

        if draft_text:
            # User edited the draft in textarea — use it directly
            file_content = f"# {name}\n\n## Business Context\n\n{draft_text}\n"
        else:
            # Fallback: generate from chat history
            history = data.get('history', [])
            conversation = "\n".join(
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in history
            )

            from strategy_factory.synthesis.gemini_client import GeminiClient
            client = GeminiClient()

            prompt = f"""Based on this conversation and research, generate a concise business context profile.

Conversation:
{conversation}

Profile name: {name}

Generate the file in exactly this Markdown format (output only the file content, nothing else):

# {name}

## Business Context
[5-10 lines covering: regional economy context, revenue range if known, team structure
(owner-only vs staff), values/culture notes, and industry-specific context that web
research cannot easily surface. Write as a single flowing paragraph. Be specific, not generic.]
"""
            result = client.generate(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=1024,
            )
            if result.error:
                return jsonify({"error": result.error}), 500
            file_content = result.content.strip()

        slug = slugify(name)
        AUDIENCE_DIR.mkdir(parents=True, exist_ok=True)
        save_path = AUDIENCE_DIR / f"{slug}.md"
        save_path.write_text(file_content, encoding="utf-8")

        # Invalidate singleton cache so new profile appears in dropdown
        _al_module._loader_instance = None

        return jsonify({"slug": slug, "name": name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Pipeline Execution
# =============================================================================

def run_pipeline(job_id: str, company_name: str, context: str, logo_path: str = None, audience: str = None, website: str = None, industry: str = None):
    """Run the full pipeline in a background thread."""
    job = active_jobs[job_id]
    q = job["progress_queue"]

    try:
        # Import here to avoid circular imports
        from strategy_factory.models import CompanyInput
        from strategy_factory.progress_tracker import ProgressTracker
        from strategy_factory.research.orchestrator import ResearchOrchestrator
        from strategy_factory.synthesis.orchestrator import SynthesisOrchestrator
        from strategy_factory.generation.orchestrator import GenerationOrchestrator

        company_input = CompanyInput(
            name=company_name,
            industry=industry or None,
            context=context,
            logo_path=logo_path,
            audience=audience,
            website=website,
        )

        tracker = ProgressTracker(company_name, company_input)

        # Phase 1: Research
        tracker.start_phase("research")
        q.put({
            "phase": "research",
            "message": "Starting research...",
            "status": "Gathering company intelligence",
            "progress": 0,
            "detail": "Initializing"
        })

        def research_callback(message: str, progress: float):
            q.put({
                "phase": "research",
                "message": f"Research: {message}",
                "status": "Researching",
                "progress": int(progress * 100),
                "detail": message
            })

        research_orchestrator = ResearchOrchestrator(
            cache_dir=Path(tracker.output_dir),
            progress_callback=research_callback,
        )

        research_output = research_orchestrator.research(company_input)
        tracker.save_research_output(research_output)
        research_orchestrator.save_research_cache(Path(tracker.output_dir))
        tracker.complete_phase("research", f"Completed research for {company_name}")

        q.put({
            "phase": "research",
            "completed": True,
            "message": "Research complete"
        })

        # Phase 2: Synthesis
        tracker.start_phase("synthesis")
        q.put({
            "phase": "synthesis",
            "message": "Starting synthesis...",
            "status": "Generating deliverables",
            "progress": 0,
            "detail": "Initializing"
        })

        def synthesis_callback(message: str, progress: float):
            q.put({
                "phase": "synthesis",
                "message": f"Synthesis: {message}",
                "status": "Synthesizing",
                "progress": int(progress * 100),
                "detail": message
            })

        synthesis_orchestrator = SynthesisOrchestrator(
            output_dir=OUTPUT_DIR,
            progress_callback=synthesis_callback,
        )

        synthesis_output = synthesis_orchestrator.synthesize(company_input, research_output)

        # Track synthesis costs (CLI path does this in main.py; webapp was missing it)
        synthesis_cost = synthesis_orchestrator.get_cost_summary()["total_cost"]
        if synthesis_cost > 0:
            tracker.add_cost(synthesis_cost, "synthesis")

        file_paths = synthesis_orchestrator.save_deliverables(tracker.company_slug)

        for d_id, path in file_paths.items():
            tracker.complete_deliverable(d_id, path)
        tracker.complete_phase("synthesis", f"Generated {len(file_paths)} markdown deliverables")

        q.put({
            "phase": "synthesis",
            "completed": True,
            "message": "Synthesis complete"
        })

        # Phase 3: Generation
        tracker.start_phase("generation")
        q.put({
            "phase": "generation",
            "message": "Starting document generation...",
            "status": "Creating final documents",
            "progress": 0,
            "detail": "Initializing"
        })

        def generation_callback(message: str, progress: float):
            q.put({
                "phase": "generation",
                "message": f"Generation: {message}",
                "status": "Generating",
                "progress": int(progress * 100),
                "detail": message
            })

        generation_orchestrator = GenerationOrchestrator(
            output_dir=OUTPUT_DIR,
            progress_callback=generation_callback,
        )

        result = generation_orchestrator.generate_all(
            company_slug=tracker.company_slug,
            company_input=company_input,
            research=research_output,
            synthesis=synthesis_output,
        )

        # Mark generation deliverables complete in tracker
        for deliverable in result.deliverables:
            d_name = deliverable["name"]
            d_path = deliverable["path"]
            for d_id, config in DELIVERABLES.items():
                if config.get("name") == d_name:
                    tracker.complete_deliverable(d_id, d_path)
                    break
        tracker.complete_phase("generation", f"Generated {len(result.deliverables)} files")

        q.put({
            "phase": "generation",
            "completed": True,
            "message": "Generation complete"
        })

        # Complete
        q.put({
            "complete": True,
            "company_slug": tracker.company_slug,
            "message": "Analysis complete!"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        q.put({
            "error": str(e),
            "message": "Error occurred"
        })


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the web application."""
    import argparse
    import socket

    parser = argparse.ArgumentParser(description="AI Strategy Factory Web App")
    parser.add_argument("--port", "-p", type=int, default=8888, help="Port to run on (default: 8888)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    # Check for API keys
    missing_keys = []
    if not os.getenv("PERPLEXITY_API_KEY"):
        missing_keys.append("PERPLEXITY_API_KEY")
    if not os.getenv("GEMINI_API_KEY"):
        missing_keys.append("GEMINI_API_KEY")

    if missing_keys:
        print("Warning: Missing API keys:", ", ".join(missing_keys))
        print("Set these in your .env file for full functionality.\n")

    import webbrowser

    # Find an available port if default is in use
    port = args.port
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    if is_port_in_use(port):
        print(f"Port {port} is in use, trying alternatives...")
        for alt_port in [8889, 8890, 9000, 9001]:
            if not is_port_in_use(alt_port):
                port = alt_port
                break
        else:
            print("Error: Could not find an available port. Try specifying one with --port")
            return 1

    url = f"http://localhost:{port}"

    print("\n" + "=" * 50)
    print("AI Strategy Factory Web App")
    print("=" * 50)
    print(f"Server running at: {url}")
    print("Press Ctrl+C to stop\n")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        app.run(host=args.host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0


if __name__ == "__main__":
    main()
