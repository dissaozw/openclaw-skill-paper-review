# 📄 paper-review

OpenClaw skill for autonomous ML/AI paper review with code-to-paper mapping.

## What it does

Give it a paper URL → it fetches the PDF, summarizes key points, finds the GitHub repo, clones it, reads the code, maps components to paper sections/equations, and exports structured notes to Notion.

## Output Template

1. **TL;DR**
2. **Main Loop** — code block from entry point
3. **Data Flow** — ASCII diagram
4. **Core Components** — each with: what / code location / snippet / paper reference / equations (LaTeX)
5. **Code Structure** — tree view
6. **Results** — benchmarks
7. **Notes & Relevance**

If no repo is found, outputs a paper-only summary (TL;DR → Problem → Method → Equations → Results → Limitations).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/fetch_paper.py` | Fetch paper from arXiv/PDF URL, extract text via pdfplumber |
| `scripts/find_repo.py` | Find GitHub repo from paper text or search API |
| `scripts/notion_export.py` | Create/update Notion pages with structured blocks |

## Requirements

- Python 3.9+
- `pdfplumber` (`pip install pdfplumber`)
- Notion API key at `~/.config/notion/api_key` or `NOTION_API_KEY` env var

## Usage

Install as an OpenClaw skill by cloning into your workspace skills directory:

```bash
cd ~/.openclaw/workspace/skills
git clone https://github.com/dissaozw/openclaw-skill-paper-review.git paper-review
```

Then ask your agent to review a paper:

> "Review this paper: https://arxiv.org/abs/2504.15777"

## License

MIT
