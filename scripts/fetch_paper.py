#!/usr/bin/env python3
"""Fetch paper text from arXiv or PDF URL.

Usage:
    python3 fetch_paper.py <url_or_arxiv_id> [--output <path>]

Supports:
    - arXiv IDs (e.g., 2501.01243)
    - arXiv URLs (e.g., https://arxiv.org/abs/2501.01243)
    - Direct PDF URLs

Outputs JSON with: title, authors, abstract, url, pdf_url, text (full extracted text)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET


def extract_arxiv_id(url_or_id: str) -> str:
    """Extract arXiv ID from URL or raw ID."""
    # Direct ID like 2501.01243 or 2501.01243v2
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", url_or_id):
        return url_or_id
    # URL patterns
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url_or_id)
    if m:
        return m.group(1)
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> dict:
    """Fetch title, authors, abstract from arXiv API."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-review-skill/1.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    xml = resp.read().decode()
    
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {}
    
    title = entry.find("atom:title", ns)
    abstract = entry.find("atom:summary", ns)
    authors = entry.findall("atom:author/atom:name", ns)
    published = entry.find("atom:published", ns)
    
    # Find PDF link
    pdf_url = None
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf":
            pdf_url = link.get("href")
    
    return {
        "title": title.text.strip().replace("\n", " ") if title is not None else "",
        "authors": [a.text.strip() for a in authors],
        "abstract": abstract.text.strip() if abstract is not None else "",
        "year": published.text[:4] if published is not None else "",
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
    }


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using available tools."""
    # Try pdftotext first (poppler)
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback: try python pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n\n".join(text_parts)
    except ImportError:
        pass
    
    # Fallback: try PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass
    
    return "[Could not extract PDF text. Install pdftotext (poppler) or pdfplumber.]"


def fetch_paper(url_or_id: str) -> dict:
    """Main: fetch paper metadata + full text."""
    arxiv_id = extract_arxiv_id(url_or_id)
    
    if arxiv_id:
        meta = fetch_arxiv_metadata(arxiv_id)
        pdf_url = meta.get("pdf_url", f"https://arxiv.org/pdf/{arxiv_id}.pdf")
    else:
        # Assume direct PDF URL
        meta = {
            "title": "",
            "authors": [],
            "abstract": "",
            "year": "",
            "url": url_or_id,
            "pdf_url": url_or_id,
        }
        pdf_url = url_or_id
    
    # Download PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "paper-review-skill/1.0"})
        resp = urllib.request.urlopen(req, timeout=120)
        f.write(resp.read())
    
    try:
        text = extract_text_from_pdf(pdf_path)
        # Truncate to ~100K chars to avoid overwhelming context
        if len(text) > 100000:
            text = text[:100000] + "\n\n[... truncated at 100K chars ...]"
        meta["text"] = text
    finally:
        os.unlink(pdf_path)
    
    return meta


def main():
    parser = argparse.ArgumentParser(description="Fetch paper from arXiv or PDF URL")
    parser.add_argument("url", help="arXiv URL/ID or PDF URL")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    args = parser.parse_args()
    
    result = fetch_paper(args.url)
    
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
