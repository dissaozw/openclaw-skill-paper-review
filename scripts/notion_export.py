#!/usr/bin/env python3
"""Export paper review to Notion Papers database.

Usage:
    python3 notion_export.py --db <database_id> --properties <json_file> --blocks <json_file>

Properties JSON: {"Name": "...", "Authors": "...", "Year": 2025, "Tags": ["RL","LLM"], "Status": "Summarized", "URL": "..."}
Blocks JSON: array of Notion block objects (the page body)

Requires: NOTION_API_KEY env var or ~/.config/notion/api_key
"""
import argparse
import json
import os
import sys
import urllib.request


def get_api_key() -> str:
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key
    key_file = os.path.expanduser("~/.config/notion/api_key")
    if os.path.exists(key_file):
        return open(key_file).read().strip()
    raise RuntimeError("No Notion API key found")


def create_page(db_id: str, properties: dict, blocks: list) -> dict:
    key = get_api_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    # Build Notion properties
    notion_props = {}
    
    if "Name" in properties:
        notion_props["Name"] = {"title": [{"text": {"content": properties["Name"]}}]}
    if "Authors" in properties:
        notion_props["Authors"] = {"rich_text": [{"text": {"content": properties["Authors"]}}]}
    if "Year" in properties:
        notion_props["Year"] = {"number": int(properties["Year"])}
    if "Tags" in properties:
        notion_props["Tags"] = {"multi_select": [{"name": t} for t in properties["Tags"]]}
    if "Status" in properties:
        notion_props["Status"] = {"select": {"name": properties["Status"]}}
    if "URL" in properties:
        notion_props["URL"] = {"url": properties["URL"]}
    if "Summary" in properties:
        # Truncate to 2000 chars (Notion rich_text limit)
        summary = properties["Summary"][:2000]
        notion_props["Summary"] = {"rich_text": [{"text": {"content": summary}}]}
    
    payload = {
        "parent": {"database_id": db_id},
        "properties": notion_props,
    }
    
    # Create page first (without blocks — blocks added separately to handle >100)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=data, headers=headers, method="POST"
    )
    resp = urllib.request.urlopen(req)
    page = json.loads(resp.read())
    page_id = page["id"]
    
    # Append blocks in batches of 100
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i+100]
        block_payload = {"children": [{"object": "block", **b} for b in batch]}
        data = json.dumps(block_payload).encode()
        req = urllib.request.Request(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            data=data, headers=headers, method="PATCH"
        )
        urllib.request.urlopen(req)
    
    return page


def update_page(page_id: str, blocks: list) -> None:
    """Replace all blocks on an existing page."""
    key = get_api_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    # Delete existing blocks
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    while True:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        for block in data.get("results", []):
            dreq = urllib.request.Request(
                f"https://api.notion.com/v1/blocks/{block['id']}",
                headers=headers, method="DELETE"
            )
            try:
                urllib.request.urlopen(dreq)
            except:
                pass
        if not data.get("has_more"):
            break
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={data['next_cursor']}"
    
    # Append new blocks
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i+100]
        payload = {"children": [{"object": "block", **b} for b in batch]}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            data=data, headers=headers, method="PATCH"
        )
        urllib.request.urlopen(req)


def main():
    parser = argparse.ArgumentParser(description="Export paper review to Notion")
    parser.add_argument("--db", required=True, help="Notion database ID")
    parser.add_argument("--properties", required=True, help="JSON file with page properties")
    parser.add_argument("--blocks", required=True, help="JSON file with Notion blocks")
    parser.add_argument("--update", help="Update existing page ID instead of creating new")
    args = parser.parse_args()
    
    with open(args.properties) as f:
        properties = json.load(f)
    with open(args.blocks) as f:
        blocks = json.load(f)
    
    if args.update:
        update_page(args.update, blocks)
        print(json.dumps({"page_id": args.update, "action": "updated"}))
    else:
        page = create_page(args.db, properties, blocks)
        print(json.dumps({"page_id": page["id"], "url": page.get("url", ""), "action": "created"}))


if __name__ == "__main__":
    main()
