---
name: paper-review
description: Read an ML/AI paper, summarize it, find and clone the GitHub repo, map code to paper concepts, and save structured notes to Notion. Use when asked to review, read, or summarize a paper — especially with a URL, arXiv link, or paper title.
---

# Paper Review Skill

Autonomous paper review: fetch → summarize → find repo → read code → map to paper → export to Notion.

## Config

- **Notion Papers DB**: Auto-discovered by searching for a database named "Papers"
- **Repos directory**: `repos/` (workspace-relative)
- **Notion API key**: `~/.config/notion/api_key` or `NOTION_API_KEY` env

## Workflow

### Phase 1: Fetch Paper

```bash
python3 scripts/fetch_paper.py "<url_or_arxiv_id>" -o /tmp/paper.json
```

Output: JSON with `title`, `authors`, `abstract`, `year`, `url`, `pdf_url`, `text`.

If text extraction fails or is poor quality, use `web_fetch` on the arXiv HTML version: `https://arxiv.org/html/<id>`.

### Phase 2: Summarize Paper

Read the extracted text. Identify:
- **TL;DR**: 1-2 sentences
- **Problem**: What gap does this address?
- **Method**: Core approach + key innovations
- **Key equations**: The essential math (will become LaTeX blocks)
- **Architecture**: System components and how they interact
- **Results**: Main benchmarks and numbers
- **Limitations**: Acknowledged or observed

### Phase 3: Find & Clone Repo

```bash
python3 scripts/find_repo.py --title "<title>" --authors "<authors>" --text-file /tmp/paper_text.txt
```

Pick the best repo: prefer repos linked in the paper text (`source: paper_text`), then highest-star GitHub search result whose description matches.

If a repo is found:
```bash
cd repos/ && git clone <repo_url>
```

If no repo found, skip to Phase 5.

### Phase 4: Read Code & Map to Paper

This is the high-value phase. Follow this approach:

1. **Read README** — find the recommended example / quickstart
2. **Pick ONE example** — typically from `examples/` or mentioned in README
3. **Trace the entry point** — find the main training/inference loop
4. **Identify core components** by following the data flow:
   - What goes in? (data loading)
   - What generates? (inference/rollout)
   - What computes loss? (training objective)
   - What optimizes? (optimizer, scheduler)
   - What coordinates? (controller, orchestrator)
5. **For each component**, note:
   - File path + class/function name
   - What it does (1-2 sentences)
   - Key code snippet or pseudocode
   - Which paper section/equation it implements

**Code reading strategy**: Start from the example, trace into the main loop, then go one level deeper into each function called by the loop. Don't read every file — follow the data flow.

### Phase 5: Build Notion Page

Structure the page body as Notion blocks following this template:

```
1. TL;DR                          — paragraph
2. Main Loop                      — code block (from example entry point)
3. Data Flow                      — code block (ASCII diagram)
4. Core Components                — for each:
   4.x Component Name             — heading_2
     What:                         — paragraph
     Code:                         — paragraph (file:line, class/fn names in code annotations)
     [code block]                  — code block (key snippet or pseudocode)
     Paper:                        — paragraph (section ref)
     [equation]                    — equation block (LaTeX, if applicable)
5. Code Structure                 — code block (tree view)
6. Results                        — bullets
7. Notes & Relevance              — paragraphs + bullets
```

If no repo was found, skip sections 2-5 and use:

```
1. TL;DR
2. Problem & Motivation
3. Method
4. Key Equations                  — equation blocks (LaTeX)
5. Results
6. Limitations
7. Notes & Relevance
```

#### Notion Block Types Reference

```python
# Heading
{"type": "heading_1", "heading_1": {"rich_text": [{"text": {"content": "..."}}]}}

# Paragraph with mixed formatting
{"type": "paragraph", "paragraph": {"rich_text": [
    {"text": {"content": "bold "}, "annotations": {"bold": True}},
    {"text": {"content": "code_ref"}, "annotations": {"code": True}},
    {"text": {"content": " normal text"}}
]}}

# Code block
{"type": "code", "code": {"rich_text": [{"text": {"content": "..."}}], "language": "python"}}

# LaTeX equation (display block)
{"type": "equation", "equation": {"expression": "J(\\theta) = ..."}}

# Bullet
{"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": "..."}}]}}
```

#### Export

Write properties to `/tmp/paper_props.json`:
```json
{"Name": "...", "Authors": "...", "Year": 2025, "Tags": ["RL"], "Status": "Summarized", "URL": "...", "GitHub": "https://github.com/...", "Summary": "one-line TL;DR"}
```

Write blocks array to `/tmp/paper_blocks.json`.

```bash
python3 scripts/notion_export.py \
    --properties /tmp/paper_props.json \
    --blocks /tmp/paper_blocks.json
```

To update an existing page:
```bash
python3 scripts/notion_export.py \
    --properties /tmp/paper_props.json \
    --blocks /tmp/paper_blocks.json \
    --update <page_id>
```

## Tags (use from this set, or add new ones)

RL, LLM, Agents, Safety, Training, Inference, Architecture, Alignment, Reasoning, Vision, Multimodal, Diffusion, Efficiency, Data, Evaluation

## Critical Rules

- **NEVER fabricate URLs or arXiv IDs.** Always use the URL from Phase 1 (`fetch_paper.py` output) for the Notion properties. If reviewing from a repo without a paper URL, search for it — do not guess.
- **All metadata (title, authors, year, URL) must come from `fetch_paper.py` output or verified search results.** Never fill these from memory.

## Tips

- Equations: use proper LaTeX with `\mathbb`, `\text`, `\frac`, etc. Use `\underbrace` to annotate parts.
- Code blocks: annotate with comments mapping to paper sections/equations.
- For large repos (>200 files), focus on the one example + files it imports. Don't explore everything.
- If the paper has no equations, skip equation blocks.
- The `"plain text"` language works for ASCII diagrams and tree views.
