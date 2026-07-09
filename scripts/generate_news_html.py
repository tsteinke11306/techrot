#!/usr/bin/env python3
"""
generate_news_html.py
=====================
Generates a daily AI News Brief HTML article from the article template,
and updates the news archive index page.

Usage:
    python3 scripts/generate_news_html.py --date 2026-06-25 --content "report text"

Designed to run from the repo root (e.g., /tmp/techrot-site or the cloned GitHub Pages repo).

The --content argument should be plain text in the same format as the email report:
    STORY HEADLINE
    Summary text (1-2 sentences).
    Source: URL
    Source: URL

    NEXT HEADLINE
    Summary text.
    Source: URL

Stories are separated by blank lines. Each story starts with a headline (all-caps or title case),
followed by a summary line, then one or more "Source: URL" lines.
"""

import argparse
import html
import os
import re
import sys
from datetime import datetime


TEMPLATE_PATH = "news/article-template.html"
INDEX_PATH = "news/index.html"
OUTPUT_DIR = "news"


def parse_date(date_str: str) -> str:
    """Validate and return the date string in YYYY-MM-DD format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print(f"ERROR: Invalid date format '{date_str}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)


def format_date_display(date_str: str) -> str:
    """Convert YYYY-MM-DD to a readable display format like 'June 25, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")


def parse_stories(content: str) -> list:
    """
    Parse the plain-text report into a list of story dicts.
    Each story: {headline, summary, sources: [url, ...]}

    Handles content where stories may have blank lines between headline,
    summary, and source sections by merging adjacent blocks that belong
    to the same story. Story boundaries are detected by numbered entries
    (1., 2), etc.) or by the headline-only-block + following-blocks pattern.
    """
    stories = []
    # Split on blank lines to get raw blocks
    raw_blocks = re.split(r'\n\s*\n', content.strip())

    # Classify each block into text lines and source URLs
    classified = []
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        text_lines = []
        sources = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            source_match = re.match(r'^Source:\s*(.+)$', line, re.IGNORECASE)
            if source_match:
                sources.append(source_match.group(1).strip())
            elif re.match(r'^https?://', line):
                sources.append(line)
            else:
                text_lines.append(line)

        classified.append({
            'text_lines': text_lines,
            'sources': sources,
        })

    # Walk through classified blocks and merge into stories
    i = 0
    while i < len(classified):
        block = classified[i]
        text_lines = list(block['text_lines'])
        sources = list(block['sources'])

        # Source-only block: orphan, append to previous story if exists
        if not text_lines and sources:
            if stories:
                stories[-1]['sources'].extend(sources)
            i += 1
            continue

        # If headline-only (1 text line, no sources), look ahead for summary + sources
        if len(text_lines) <= 1 and not sources:
            j = i + 1
            while j < len(classified):
                nb = classified[j]
                if not nb['text_lines'] and nb['sources']:
                    # Source-only block: add sources and stop
                    sources.extend(nb['sources'])
                    j += 1
                    break
                elif nb['text_lines'] and not nb['sources']:
                    # Text-only block: this is the summary
                    text_lines.extend(nb['text_lines'])
                    j += 1
                    # Check if the next block has sources
                    if j < len(classified) and not classified[j]['text_lines'] and classified[j]['sources']:
                        sources.extend(classified[j]['sources'])
                        j += 1
                    break
                else:
                    # Mixed block or empty: stop merging
                    break
            i_next = j
        else:
            i_next = i + 1

        # First text line is headline, rest are summary
        headline = text_lines[0] if text_lines else ''
        summary = ' '.join(text_lines[1:]).strip() if len(text_lines) > 1 else ''

        # Strip leading number prefix from headline (e.g., "1)", "1.", "1:")
        headline = re.sub(r'^\d+[\.\)\:]\s*', '', headline)

        if headline:
            stories.append({
                'headline': headline,
                'summary': summary,
                'sources': sources,
            })

        i = i_next

    return stories


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text, quote=True)


def extract_domain(url: str) -> str:
    """Extract a readable domain from a URL for display."""
    # Remove protocol
    domain = re.sub(r'^https?://', '', url)
    # Remove www
    domain = re.sub(r'^www\.', '', domain)
    # Take just the domain part (before first /)
    domain = domain.split('/')[0]
    # Truncate if too long
    if len(domain) > 40:
        domain = domain[:37] + '...'
    return domain


def generate_story_html(stories: list) -> str:
    """Generate the HTML for the stories section."""
    story_blocks = []

    for idx, story in enumerate(stories, 1):
        headline = escape_html(story['headline'])
        summary = escape_html(story['summary'])

        # Build source links
        source_links = []
        for url in story['sources']:
            domain = escape_html(extract_domain(url))
            safe_url = escape_html(url)
            source_links.append(
                f'      <a href="{safe_url}" target="_blank" rel="noopener noreferrer">'
                f'<span class="source-icon">▶</span> {domain}</a>'
            )

        sources_html = '\n'.join(source_links) if source_links else '      <span style="font-size:12px;color:var(--fg-faint);">// no sources</span>'

        story_html = f"""    <div class="story">
      <div class="story-num">// STORY_{idx:02d}</div>
      <h2>{headline}</h2>
      <p class="summary">{summary}</p>
      <div class="sources">
{sources_html}
      </div>
    </div>"""
        story_blocks.append(story_html)

    return '\n\n'.join(story_blocks)


def generate_article(date_str: str, stories: list, top_headline: str) -> str:
    """Read the template and produce the final article HTML."""
    template_path = os.path.join(TEMPLATE_PATH)
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    date_display = format_date_display(date_str)
    stories_html = generate_story_html(stories)

    # Replace template placeholders
    article = template.replace('{{DATE}}', date_str)
    article = article.replace('{{DATE_DISPLAY}}', date_display)
    article = article.replace('{{TOP_HEADLINE}}', escape_html(top_headline))

    # Replace the stories section placeholder
    article = article.replace('<!--STORIES-->', stories_html)

    return article


def generate_archive_entry(date_str: str, top_headline: str) -> str:
    """Generate a single archive entry HTML block."""
    date_display = format_date_display(date_str)
    safe_headline = escape_html(top_headline)
    safe_date = escape_html(date_display)

    return f"""    <a class="archive-entry" href="{date_str}.html">
      <span class="date">{safe_date}</span>
      <span class="headline">{safe_headline}</span>
      <span class="arrow">▶</span>
    </a>"""


def update_index(date_str: str, top_headline: str):
    """Update the news index page to add a new entry at the top."""
    if not os.path.exists(INDEX_PATH):
        print(f"ERROR: Index not found at {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index_content = f.read()

    new_entry = generate_archive_entry(date_str, top_headline)

    # Check if this date already exists in the index
    existing_pattern = re.compile(
        r'<a class="archive-entry" href="' + re.escape(date_str) + r'\.html"'
    )
    if existing_pattern.search(index_content):
        print(f"NOTE: Entry for {date_str} already exists in index. Skipping index update.")
        return

    # Insert the new entry after the archive entries marker
    marker = '<!--ARCHIVE_ENTRIES-->'
    if marker in index_content:
        index_content = index_content.replace(
            marker,
            marker + '\n' + new_entry
        )
    else:
        # Fallback: find the first archive-entry and insert before it
        first_entry_pattern = re.compile(r'(\s*)(<a class="archive-entry")')
        match = first_entry_pattern.search(index_content)
        if match:
            indent = match.group(1)
            index_content = index_content[:match.start()] + indent + new_entry + '\n' + index_content[match.start():]
        else:
            print("WARNING: Could not find insertion point in index. Index not updated.", file=sys.stderr)
            return

    # Remove the empty-state block now that at least one entry exists
    # The empty-state div contains two child divs:
    #   <div class="empty-state">
    #     <div class="icon">...</div>
    #     <div>...</div>
    #   </div>
    if 'class="archive-entry"' in index_content:
        index_content = re.sub(
            r'\n\s*<div class="empty-state">\s*'
            r'<div class="icon">.*?</div>\s*'
            r'<div>.*?</div>\s*'
            r'</div>',
            '',
            index_content,
            count=1,
            flags=re.DOTALL
        )

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"Updated index: {INDEX_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate a daily AI News Brief HTML article and update the archive index.'
    )
    parser.add_argument(
        '--date',
        required=True,
        help='Date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--content',
        required=True,
        help='Plain text report content (same format as the email)'
    )
    parser.add_argument(
        '--repo-root',
        default='.',
        help='Path to the repo root (default: current directory)'
    )

    args = parser.parse_args()

    # Validate date
    date_str = parse_date(args.date)

    # Change to repo root if specified
    if args.repo_root and args.repo_root != '.':
        os.chdir(args.repo_root)

    # Parse stories from the content
    stories = parse_stories(args.content)

    if not stories:
        print("ERROR: No stories found in content.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(stories)} stories from content.")

    # Get top headline for index/meta
    top_headline = stories[0]['headline']
    print(f"Top headline: {top_headline}")

    # Generate the article HTML
    article_html = generate_article(date_str, stories, top_headline)

    # Write the article file
    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(article_html)
    print(f"Generated article: {output_path}")

    # Update the index
    update_index(date_str, top_headline)

    print(f"\nDone! Article published at /news/{date_str}.html")


if __name__ == '__main__':
    main()