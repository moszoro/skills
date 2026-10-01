"""Acceptance tests for reddit_voc.py — issue moszoro/skills#18 (AC1-AC7).

Run: uv run --with pytest --with click pytest skills/reddit-voc/scripts/tests -q
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reddit_voc  # noqa: E402

THREAD_A = "https://www.reddit.com/r/startups/comments/1oc6w06/we_ditched_the_word_doc/"
THREAD_B = "https://www.reddit.com/r/SaaS/comments/1we8to2/data_room_mess/"

DATASET = [
    {
        "dataType": "post",
        "parsedId": "1oc6w06",
        "title": "We ditched the Word doc",
        "body": "We sent our seed-round investor updates as long Word documents.",
        "postUrl": THREAD_A,
        "authorName": "founder_ann",
        "communityName": "r/startups",
        "score": 120,
        "commentsCount": 2,
        "createdAt": "2025-11-03T10:15:00.000Z",
    },
    {
        "dataType": "comment",
        "id": "c_low",
        "parsedPostId": "1oc6w06",
        "body": "Low score comment.",
        "authorName": "user_low",
        "score": 3,
        "commentCreatedAt": "2025-11-03T11:00:00.000Z",
        "url": THREAD_A + "comment/c_low/",
    },
    {
        "dataType": "comment",
        "id": "c_high",
        "parsedPostId": "1oc6w06",
        "body": "High score comment with *markdown* kept.",
        "authorName": "user_high",
        "score": 40,
        "commentCreatedAt": "2025-11-04T09:30:00.000Z",
        "url": THREAD_A + "comment/c_high/",
    },
]


@pytest.fixture
def apify_calls(monkeypatch):
    """Replace the `apify` process (the only external seam) and record each call."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        kwargs["stdout"].write(json.dumps(DATASET))
        return subprocess.CompletedProcess(cmd, 0, stderr="")

    monkeypatch.setattr(reddit_voc.subprocess, "run", fake_run)
    return calls


def write_urls(tmp_path, urls):
    path = tmp_path / "urls.txt"
    path.write_text("\n".join(urls))
    return str(path)


# AC1 ---------------------------------------------------------------------------------------------
def test_links_keeps_unique_thread_urls_and_drops_the_rest():
    messy = "\n".join(
        [
            "https://www.reddit.com/r/startups/comments/1oc6w06/we_ditched_the_word_doc/?utm_source=share | title",
            "https://old.reddit.com/r/startups/comments/1oc6w06/we_ditched_the_word_doc/",
            "https://www.reddit.com/r/SaaS/comments/1we8to2/data_room_mess/ni4tqzb/",
            "https://www.reddit.com/r/ExperiencedFounders/",
            "https://example.com/r/x/comments/abc123/not_reddit/",
        ]
    )

    result = CliRunner().invoke(reddit_voc.cli, ["links"], input=messy)

    assert result.exit_code == 0
    assert result.output.splitlines() == [THREAD_A, THREAD_B]


# AC2 ---------------------------------------------------------------------------------------------
def test_worst_case_cost_is_start_fee_plus_items_times_result_price():
    # 30 threads, each 1 post + 25 comments = 780 items. 0.02 + 780 * 0.002 = 1.58
    assert reddit_voc.estimate_cost_usd(posts=30, max_comments=25) == pytest.approx(1.58)


# AC3 ---------------------------------------------------------------------------------------------
def test_scrape_refuses_when_worst_case_cost_is_over_budget(tmp_path, apify_calls):
    urls = write_urls(tmp_path, [THREAD_A, THREAD_B])

    # 2 threads x (1 + 25) = 52 items -> 0.02 + 0.104 = 0.124 USD > 0.10
    result = CliRunner().invoke(
        reddit_voc.cli,
        ["scrape", urls, "--max-comments", "25", "--max-usd", "0.10", "--out-dir", str(tmp_path / "out")],
    )

    assert result.exit_code != 0
    assert "0.12" in result.output
    assert apify_calls == []
    assert not (tmp_path / "out").exists()


# AC4 + AC5 ---------------------------------------------------------------------------------------
def test_dry_run_prints_cost_and_actor_input_without_calling_apify(tmp_path, apify_calls):
    urls = write_urls(tmp_path, [THREAD_A, THREAD_B])

    result = CliRunner().invoke(
        reddit_voc.cli,
        ["scrape", urls, "--max-comments", "10", "--dry-run", "--out-dir", str(tmp_path / "out")],
    )

    assert result.exit_code == 0
    assert apify_calls == []
    # 2 x (1 + 10) = 22 items -> 0.02 + 0.044 = 0.064 -> shown as 0.06
    assert "0.06" in result.output
    actor_input = json.loads(result.output[result.output.index("{") :])
    assert actor_input["startUrls"] == [{"url": THREAD_A}, {"url": THREAD_B}]
    assert actor_input["crawlCommentsPerPost"] is True
    assert actor_input["maxPostsCount"] == 2
    assert actor_input["maxCommentsPerPost"] == 10
    assert actor_input["aiAnalysis"] is False
    assert actor_input["includeNSFW"] is False


def test_search_input_caps_posts_per_term_and_limits_to_one_subreddit(tmp_path, apify_calls):
    result = CliRunner().invoke(
        reddit_voc.cli,
        [
            "search", "investor updates", "data room",
            "--subreddit", "startups", "--max-posts", "5", "--max-comments", "4",
            "--dry-run", "--out-dir", str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0
    assert apify_calls == []
    # 2 terms x 5 posts x (1 + 4) = 50 items -> 0.02 + 0.10 = 0.12
    assert "0.12" in result.output
    actor_input = json.loads(result.output[result.output.index("{") :])
    assert actor_input["searchTerms"] == ["investor updates", "data room"]
    assert actor_input["withinCommunity"] == "r/startups"
    assert actor_input["maxPostsCount"] == 5
    assert actor_input["maxCommentsPerPost"] == 4
    assert actor_input["aiAnalysis"] is False


# AC6 ---------------------------------------------------------------------------------------------
def test_scrape_writes_one_markdown_file_per_thread_with_verbatim_text(tmp_path, apify_calls):
    urls = write_urls(tmp_path, [THREAD_A])
    out = tmp_path / "out"

    result = CliRunner().invoke(reddit_voc.cli, ["scrape", urls, "--out-dir", str(out)])

    assert result.exit_code == 0, result.output
    assert apify_calls[0][:3] == ["apify", "call", "harshmaur/reddit-scraper"]
    assert json.loads((out / "dataset.json").read_text()) == DATASET
    files = sorted(p.name for p in out.glob("*.md"))
    assert files == ["startups-1oc6w06.md"]
    text = (out / "startups-1oc6w06.md").read_text()
    assert "# We ditched the Word doc" in text
    assert THREAD_A in text
    assert "r/startups" in text
    assert "u/founder_ann" in text
    assert "2025-11-03" in text
    assert "We sent our seed-round investor updates as long Word documents." in text
    assert "High score comment with *markdown* kept." in text
    assert THREAD_A + "comment/c_high/" in text
    assert text.index("u/user_high") < text.index("u/user_low")


# AC7 ---------------------------------------------------------------------------------------------
def test_apify_failure_is_reported_and_writes_no_thread_files(tmp_path, monkeypatch):
    message = "Error: Your remaining usage of $0.001617 this billing cycle isn't enough for this run."

    def failing_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stderr=message)

    monkeypatch.setattr(reddit_voc.subprocess, "run", failing_run)
    urls = write_urls(tmp_path, [THREAD_A])
    out = tmp_path / "out"

    result = CliRunner().invoke(reddit_voc.cli, ["scrape", urls, "--out-dir", str(out)])

    assert result.exit_code != 0
    assert "remaining usage" in result.output
    assert not list(out.glob("*.md"))


# Regression: the real `apify` CLI exits before a piped stdout is drained, so a dataset above the
# 64 KB pipe buffer arrived cut ("Unterminated string ... char 65211"). Found on the first live run.
FAKE_APIFY = """#!/usr/bin/env python3
import fcntl, json, os
big = [{"dataType": "post", "parsedId": "big1", "title": "Big", "body": "x" * 300000,
        "postUrl": "https://www.reddit.com/r/startups/comments/big1/big/", "authorName": "a",
        "communityName": "r/startups", "score": 1, "commentsCount": 0,
        "createdAt": "2026-01-01T00:00:00.000Z"}]
fcntl.fcntl(1, fcntl.F_SETFL, fcntl.fcntl(1, fcntl.F_GETFL) | os.O_NONBLOCK)
try:
    os.write(1, json.dumps(big).encode())
except BlockingIOError:
    pass
os._exit(0)
"""


def test_dataset_larger_than_the_pipe_buffer_is_read_whole(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "apify"
    fake.write_text(FAKE_APIFY)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin")
    urls = write_urls(tmp_path, ["https://www.reddit.com/r/startups/comments/big1/big/"])
    out = tmp_path / "out"

    result = CliRunner().invoke(reddit_voc.cli, ["scrape", urls, "--max-comments", "0", "--out-dir", str(out)])

    assert result.exit_code == 0, result.output
    assert len(json.loads((out / "dataset.json").read_text())[0]["body"]) == 300000
    assert (out / "startups-big1.md").exists()
