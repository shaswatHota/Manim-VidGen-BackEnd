"""
Manim Documentation Scraper
============================
Scrapes the following pages preserving their structure (headings, text, code blocks):
  - Quickstart
  - Manim's Building Blocks
  - All sub-pages listed under Reference Manual

Output: manim_docs.json  — structured content per page
        manim_docs.md    — human-readable Markdown version (same layout as the website)
"""

import time
import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin

BASE_URL = "https://docs.manim.community/en/stable"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Pages to always scrape ────────────────────────────────────────────────────
FIXED_PAGES = [
    {
        "title": "Quickstart",
        "url": f"{BASE_URL}/tutorials/quickstart.html",
    },
    {
        "title": "Manim's Building Blocks",
        "url": f"{BASE_URL}/tutorials/building_blocks.html",
    },
]

# ── Reference Manual index page ───────────────────────────────────────────────
REFERENCE_MANUAL_URL = f"{BASE_URL}/reference.html"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_soup(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [ERROR] Could not fetch {url}: {e}")
        return None


def extract_reference_sub_urls(index_url: str) -> list[dict]:
    """
    Parse the Reference Manual index page and collect every sub-page link
    listed in the toctree / reference table.
    """
    print(f"Fetching Reference Manual index: {index_url}")
    soup = get_soup(index_url)
    if not soup:
        return []

    links = []
    seen = set()

    # Manim docs render toctree entries inside <div class="toctree-wrapper">
    # and also in the main body as <a> tags relative to the base.
    content_div = soup.find("div", {"role": "main"}) or soup.body

    for a in content_div.find_all("a", href=True):
        href = a["href"]
        # Skip anchors, external links, and the index itself
        if href.startswith("#") or href.startswith("http") and BASE_URL not in href:
            continue
        full_url = urljoin(index_url, href).split("#")[0]
        if full_url not in seen and full_url != index_url and full_url.startswith(BASE_URL):
            seen.add(full_url)
            title = a.get_text(strip=True) or full_url.split("/")[-1]
            links.append({"title": title, "url": full_url})

    print(f"  Found {len(links)} sub-page(s) under Reference Manual.")
    return links


def extract_page_content(url: str) -> list[dict]:
    """
    Extract the structured content of a documentation page as an ordered list
    of blocks, each being one of:
      {"type": "heading", "level": int, "text": str}
      {"type": "paragraph", "text": str}
      {"type": "code",      "language": str, "text": str}
      {"type": "list_item", "text": str}
      {"type": "note",      "text": str}       # admonitions
    """
    soup = get_soup(url)
    if not soup:
        return []

    # The main content lives inside <div role="main"> or <article>
    main = (
        soup.find("div", {"role": "main"})
        or soup.find("article")
        or soup.find("div", class_="body")
        or soup.body
    )

    blocks = []

    def walk(node):
        if isinstance(node, NavigableString):
            return
        if not isinstance(node, Tag):
            return

        tag = node.name

        # ── Headings ─────────────────────────────────────────────────────────
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            text = node.get_text(strip=True)
            # Strip trailing ¶ permalink symbols
            text = text.rstrip("¶").strip()
            if text:
                blocks.append({"type": "heading", "level": level, "text": text})
            return  # don't recurse into heading

        # ── Code blocks ──────────────────────────────────────────────────────
        if tag == "pre":
            code_node = node.find("code") or node
            language = ""
            classes = code_node.get("class", [])
            for cls in classes:
                if cls.startswith("language-"):
                    language = cls.replace("language-", "")
                    break
            # Also try highlight div wrapper
            parent = node.parent
            if parent and "highlight-" in " ".join(parent.get("class", [])):
                for cls in parent.get("class", []):
                    if cls.startswith("highlight-"):
                        language = cls.replace("highlight-", "").replace(" notranslate", "")
            blocks.append({
                "type": "code",
                "language": language or "python",
                "text": node.get_text(),
            })
            return

        # ── Admonitions (Note, Warning, etc.) ────────────────────────────────
        if tag == "div" and any(
            cls in node.get("class", [])
            for cls in ("note", "warning", "tip", "important", "admonition")
        ):
            text = node.get_text(strip=True)
            if text:
                blocks.append({"type": "note", "text": text})
            return

        # ── Paragraphs ───────────────────────────────────────────────────────
        if tag == "p":
            text = node.get_text(strip=True)
            if text:
                blocks.append({"type": "paragraph", "text": text})
            return

        # ── List items ───────────────────────────────────────────────────────
        if tag == "li":
            # Only grab direct text, not nested lists (they'll be walked separately)
            text_parts = []
            for child in node.children:
                if isinstance(child, NavigableString):
                    text_parts.append(str(child).strip())
                elif isinstance(child, Tag) and child.name not in ("ul", "ol"):
                    text_parts.append(child.get_text(strip=True))
            text = " ".join(t for t in text_parts if t)
            if text:
                blocks.append({"type": "list_item", "text": text})
            # Still recurse for nested lists
            for child in node.children:
                if isinstance(child, Tag) and child.name in ("ul", "ol"):
                    walk(child)
            return

        # ── Recurse into everything else ─────────────────────────────────────
        for child in node.children:
            walk(child)

    walk(main)
    return blocks


# ─────────────────────────────────────────────────────────────────────────────
# Renderers
# ─────────────────────────────────────────────────────────────────────────────

def blocks_to_markdown(blocks: list[dict]) -> str:
    """Convert extracted blocks back into clean Markdown."""
    lines = []
    for b in blocks:
        btype = b["type"]
        if btype == "heading":
            lines.append(f"\n{'#' * b['level']} {b['text']}\n")
        elif btype == "paragraph":
            lines.append(f"{b['text']}\n")
        elif btype == "code":
            lang = b.get("language", "python")
            lines.append(f"\n```{lang}\n{b['text'].rstrip()}\n```\n")
        elif btype == "list_item":
            lines.append(f"- {b['text']}")
        elif btype == "note":
            lines.append(f"\n> **Note:** {b['text']}\n")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    all_pages = []

    # 1. Fixed pages
    pages_to_scrape = list(FIXED_PAGES)

    # 2. Reference Manual sub-pages
    ref_sub_pages = extract_reference_sub_urls(REFERENCE_MANUAL_URL)
    pages_to_scrape.extend(ref_sub_pages)

    print(f"\nTotal pages to scrape: {len(pages_to_scrape)}\n")

    md_output = []

    for i, page in enumerate(pages_to_scrape, 1):
        print(f"[{i}/{len(pages_to_scrape)}] Scraping: {page['title']} — {page['url']}")
        blocks = extract_page_content(page["url"])

        page_data = {
            "title": page["title"],
            "url": page["url"],
            "blocks": blocks,
        }
        all_pages.append(page_data)

        # Build Markdown section
        md_output.append(f"\n\n{'='*70}")
        md_output.append(f"# {page['title']}")
        md_output.append(f"Source: {page['url']}")
        md_output.append("=" * 70)
        md_output.append(blocks_to_markdown(blocks))

        # Be polite to the server
        time.sleep(0.5)

    # ── Save JSON ─────────────────────────────────────────────────────────────
    json_path = "manim_docs.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_pages, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON saved → {json_path}")

    # ── Save Markdown ─────────────────────────────────────────────────────────
    md_path = "manim_docs.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_output))
    print(f"✅ Markdown saved → {md_path}")

    # ── Quick summary ─────────────────────────────────────────────────────────
    print("\n── SUMMARY ──────────────────────────────────────────────────────────")
    for p in all_pages:
        total = len(p["blocks"])
        codes = sum(1 for b in p["blocks"] if b["type"] == "code")
        print(f"  {p['title'][:55]:<56} {total:>4} blocks  ({codes} code blocks)")


if __name__ == "__main__":
    main()