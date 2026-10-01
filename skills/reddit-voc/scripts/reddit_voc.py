#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["click>=8.1"]
# ///
"""reddit_voc.py — get full Reddit threads for voice-of-customer research.

Runs the Apify Actor harshmaur/reddit-scraper through the logged-in `apify` CLI and writes one
Markdown file per thread. Every paid run prints its worst-case cost first and stops when that
cost is above --max-usd.

Usage:
    uv run reddit_voc.py links < text-with-urls.txt > urls.txt
    uv run reddit_voc.py scrape urls.txt --out-dir research/raw/reddit [--dry-run]
    uv run reddit_voc.py search "investor updates" --subreddit startups --out-dir out [--dry-run]
    uv run reddit_voc.py render out/dataset.json --out-dir out
"""
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import click

ACTOR = "harshmaur/reddit-scraper"
START_FEE_USD = 0.02
RESULT_PRICE_USD = 0.002

THREAD_URL = re.compile(
    r"https?://(?:[a-z0-9-]+\.)?reddit\.com/r/([A-Za-z0-9_]+)/comments/([a-z0-9]+)(?:/([^/\s?#|]+))?",
)


def extract_thread_urls(text):
    urls = {}
    for subreddit, post_id, slug in THREAD_URL.findall(text):
        tail = f"{slug}/" if slug else ""
        urls.setdefault(post_id, f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/{tail}")
    return list(urls.values())


def estimate_cost_usd(posts, max_comments):
    return START_FEE_USD + posts * (1 + max_comments) * RESULT_PRICE_USD


def _base_input(max_posts, max_comments):
    return {
        "crawlCommentsPerPost": max_comments > 0,
        "maxPostsCount": max_posts,
        "maxCommentsPerPost": max_comments,
        "maxCommentsCount": 0,
        "maxCommunitiesCount": 0,
        "searchComments": False,
        "searchCommunities": False,
        "includeNSFW": False,
        "aiAnalysis": False,
    }


def build_scrape_input(urls, max_comments):
    return {"startUrls": [{"url": url} for url in urls], "searchPosts": False, **_base_input(len(urls), max_comments)}


def build_search_input(terms, subreddit, max_posts, max_comments, sort, time):
    actor_input = {
        "searchTerms": list(terms),
        "searchPosts": True,
        "searchSort": sort,
        "searchTime": time,
        **_base_input(max_posts, max_comments),
    }
    if subreddit:
        actor_input["withinCommunity"] = "r/" + subreddit.removeprefix("r/")
    return actor_input


def run_actor(actor_input):
    # stdout goes to a file: the apify CLI exits before a pipe is drained and cuts output at 64 KB.
    with tempfile.TemporaryDirectory() as work:
        input_file, output_file = Path(work, "input.json"), Path(work, "dataset.json")
        input_file.write_text(json.dumps(actor_input))
        with output_file.open("w") as stdout:
            done = subprocess.run(
                ["apify", "call", ACTOR, "--input-file", str(input_file), "--silent", "--output-dataset"],
                stdout=stdout,
                stderr=subprocess.PIPE,
                text=True,
            )
        output = output_file.read_text()
    if done.returncode != 0:
        raise click.ClickException(f"apify failed (exit {done.returncode}): {(done.stderr or output).strip()}")
    return json.loads(output)


def _day(iso):
    return (iso or "")[:10] or "unknown date"


def _render_thread(post, comments):
    first = comments[0] if comments else {}
    subreddit = (post.get("communityName") or "r/" + first.get("subredditName", "unknown")).removeprefix("r/")
    title = post.get("title") or first.get("postTitle") or "(post not scraped)"
    lines = [f"# {title}", ""]
    if post:
        lines += [
            f"- URL: {post.get('postUrl', '')}",
            f"- Subreddit: r/{subreddit}",
            f"- Author: u/{post.get('authorName', 'unknown')}",
            f"- Date (UTC): {_day(post.get('createdAt'))} ({post.get('createdAt', '')})",
            f"- Score: {post.get('score', 0)} · Comments on Reddit: {post.get('commentsCount', 0)}",
            "",
            "## Post",
            "",
            post.get("body") or "(no text: link or media post)",
            "",
        ]
    lines += [f"## Comments scraped: {len(comments)} (highest score first)", ""]
    for comment in sorted(comments, key=lambda item: item.get("score", 0), reverse=True):
        lines += [
            f"### u/{comment.get('authorName', 'unknown')} · {_day(comment.get('commentCreatedAt'))}"
            f" · score {comment.get('score', 0)}",
            f"{comment.get('url', '')}",
            "",
            comment.get("body") or "",
            "",
        ]
    return subreddit, "\n".join(lines)


def render_threads(items):
    posts = {item["parsedId"]: item for item in items if item.get("dataType") == "post"}
    comments = defaultdict(list)
    for item in items:
        if item.get("dataType") == "comment":
            comments[item.get("parsedPostId", "unknown")].append(item)
    files = {}
    for post_id in dict.fromkeys([*posts, *comments]):
        subreddit, markdown = _render_thread(posts.get(post_id, {}), comments[post_id])
        files[f"{subreddit}-{post_id}.md"] = markdown
    return files


def _write_threads(items, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dataset.json").write_text(json.dumps(items, indent=1, ensure_ascii=False))
    files = render_threads(items)
    for name, markdown in files.items():
        (out / name).write_text(markdown)
    click.echo(f"Saved {len(items)} items, {len(files)} thread files in {out}")
    click.echo(f"Billed at most: ${START_FEE_USD + len(items) * RESULT_PRICE_USD:.2f}")


def _paid_run(actor_input, posts, max_comments, max_usd, dry_run, out_dir):
    cost = estimate_cost_usd(posts, max_comments)
    click.echo(f"Worst-case cost: ${cost:.2f} ({posts} posts x up to {1 + max_comments} items, budget ${max_usd:.2f})")
    if dry_run:
        click.echo(json.dumps(actor_input, indent=1))
        return
    if cost > max_usd:
        raise click.ClickException(f"Worst-case cost ${cost:.2f} is above --max-usd ${max_usd:.2f}. Nothing was run.")
    _write_threads(run_actor(actor_input), out_dir)


@click.group()
def cli():
    """Scrape Reddit threads for voice-of-customer quotes (Apify, pay per result)."""


@cli.command()
def links():
    """Read text on stdin, print unique Reddit thread URLs."""
    for url in extract_thread_urls(click.get_text_stream("stdin").read()):
        click.echo(url)


paid_options = [
    click.option("--max-comments", default=25, show_default=True, help="Comments per thread."),
    click.option("--max-usd", default=2.00, show_default=True, help="Stop when worst-case cost is above this."),
    click.option("--dry-run", is_flag=True, help="Print cost and Actor input. Do not call Apify."),
    click.option("--out-dir", default="reddit-voc-out", show_default=True, type=click.Path(file_okay=False)),
]


def with_paid_options(command):
    for option in reversed(paid_options):
        command = option(command)
    return command


@cli.command()
@click.argument("urls_file", type=click.File("r"))
@with_paid_options
def scrape(urls_file, max_comments, max_usd, dry_run, out_dir):
    """Scrape the Reddit thread URLs found in URLS_FILE ('-' for stdin)."""
    urls = extract_thread_urls(urls_file.read())
    if not urls:
        raise click.ClickException("No Reddit thread URLs found.")
    _paid_run(build_scrape_input(urls, max_comments), len(urls), max_comments, max_usd, dry_run, out_dir)


@cli.command()
@click.argument("terms", nargs=-1, required=True)
@click.option("--subreddit", help="Search inside one subreddit only.")
@click.option("--max-posts", default=10, show_default=True, help="Posts per search term.")
@click.option("--sort", default="relevance", show_default=True,
              type=click.Choice(["relevance", "hot", "top", "new", "comments"]))
@click.option("--time", default="all", show_default=True,
              type=click.Choice(["all", "hour", "day", "week", "month", "year"]))
@with_paid_options
def search(terms, subreddit, max_posts, sort, time, max_comments, max_usd, dry_run, out_dir):
    """Search Reddit for each of TERMS and scrape the posts found."""
    actor_input = build_search_input(terms, subreddit, max_posts, max_comments, sort, time)
    _paid_run(actor_input, len(terms) * max_posts, max_comments, max_usd, dry_run, out_dir)


@cli.command()
@click.argument("dataset_file", type=click.File("r"))
@click.option("--out-dir", default="reddit-voc-out", show_default=True, type=click.Path(file_okay=False))
def render(dataset_file, out_dir):
    """Rebuild the thread files from a saved dataset.json. Free."""
    _write_threads(json.load(dataset_file), out_dir)


if __name__ == "__main__":
    cli()
