#!/usr/bin/env python3
"""Find GitHub repo for a paper.

Usage:
    python3 find_repo.py --title "Paper Title" [--authors "Author1, Author2"]
    python3 find_repo.py --text "raw paper text to search for github links"

Strategy:
    1. Search paper text for GitHub URLs
    2. Search GitHub by paper title
    3. Search GitHub by title + first author

Outputs JSON: { "repos": [{"url": ..., "stars": ..., "description": ..., "source": ...}] }
"""
import argparse
import json
import re
import sys
import urllib.request
import urllib.parse


def find_github_urls_in_text(text: str) -> list:
    """Extract GitHub repo URLs from paper text."""
    pattern = r"https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"
    matches = re.findall(pattern, text)
    # Deduplicate, preserve order
    seen = set()
    urls = []
    for m in matches:
        # Clean trailing periods, commas
        m = m.rstrip(".,;)")
        if m not in seen:
            seen.add(m)
            urls.append(f"https://github.com/{m}")
    return urls


def search_github(query: str, max_results: int = 5) -> list:
    """Search GitHub repos by query."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&per_page={max_results}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "paper-review-skill/1.0",
        "Accept": "application/vnd.github.v3+json",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return [
            {
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "description": item.get("description", ""),
                "source": "github_search",
            }
            for item in data.get("items", [])
        ]
    except Exception as e:
        print(f"GitHub search error: {e}", file=sys.stderr)
        return []


def find_repo(title: str = "", authors: str = "", text: str = "") -> dict:
    """Find GitHub repos for a paper."""
    repos = []
    
    # Strategy 1: Extract URLs from paper text
    if text:
        urls = find_github_urls_in_text(text)
        for url in urls:
            repos.append({"url": url, "stars": None, "description": "", "source": "paper_text"})
    
    # Strategy 2: Search GitHub by title
    if title:
        results = search_github(title)
        repos.extend(results)
    
    # Strategy 3: Search by title + first author
    if title and authors:
        first_author = authors.split(",")[0].strip().split()[-1]  # last name
        results = search_github(f"{title} {first_author}")
        # Add only new URLs
        existing = {r["url"] for r in repos}
        for r in results:
            if r["url"] not in existing:
                repos.append(r)
    
    return {"repos": repos}


def main():
    parser = argparse.ArgumentParser(description="Find GitHub repo for a paper")
    parser.add_argument("--title", default="", help="Paper title")
    parser.add_argument("--authors", default="", help="Comma-separated authors")
    parser.add_argument("--text", default="", help="Paper text to search for GitHub links")
    parser.add_argument("--text-file", help="File containing paper text")
    args = parser.parse_args()
    
    text = args.text
    if args.text_file:
        with open(args.text_file) as f:
            text = f.read()
    
    result = find_repo(title=args.title, authors=args.authors, text=text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
