import json

import pytest

from preview_status import CONTEXT, parse_comment, sync

# A real Cloudflare Workers Builds comment (PR #57), verbatim.
REAL_COMMENT = (
    '## Deploying with &nbsp;<a href="https://workers.dev"><img alt="Cloudflare Workers" '
    'src="https://workers.cloudflare.com/logo.svg" width="16"></a> &nbsp;Cloudflare Workers\n'
    "The latest updates on your project. Learn more about [integrating Git with Workers]"
    "(https://developers.cloudflare.com/workers/ci-cd/builds/git-integration/).\n\n"
    "| Status | Name | Latest Commit | Preview URL | Updated (UTC) |\n"
    "| -|-|-|-|-|\n"
    "| ✅ Deployment successful! <br>[View logs](https://dash.cloudflare.com/?to=/4d332016793fb6b37edf699d14677f2b"
    "/workers/services/view/ghrweb/production/builds/6732fa52-1903-44ef-8ca3-be924f9adc49) | ghrweb | 2faccd3c | "
    "<a href='https://a3424301-ghrweb.enosi-ellinon-ollandias.workers.dev'>Commit Preview URL</a><br><br>"
    "<a href='https://chore-gemini-stable-model-ghrweb.enosi-ellinon-ollandias.workers.dev'>Branch Preview URL</a>"
    " | Oct 09 2026, 10:22 AM |"
)
URL = "https://a3424301-ghrweb.enosi-ellinon-ollandias.workers.dev"
HEAD = "2faccd3c7afb8f227d793f6105b5b4bc681edaf9"


def test_parse_real_comment():
    assert parse_comment(REAL_COMMENT) == ("2faccd3c", URL)


def test_parse_ignores_unfinished_build():
    body = REAL_COMMENT.replace("Deployment successful!", "Deploying...")
    assert parse_comment(body) is None


@pytest.mark.parametrize(
    "bad",
    [
        "https://evil.example.com",
        "https://a3424301-ghrweb.enosi-ellinon-ollandias.workers.dev.evil.com",
        "https://a3424301-ghrweb.enosi-ellinon-ollandias.workers.dev/../x",
        "http://a3424301-ghrweb.enosi-ellinon-ollandias.workers.dev",
        "https://a3424301-other.enosi-ellinon-ollandias.workers.dev",
        "https://evil.com/?x=-ghrweb.enosi-ellinon-ollandias.workers.dev",
    ],
)
def test_parse_rejects_foreign_urls(bad):
    assert parse_comment(REAL_COMMENT.replace(URL, bad)) is None


class FakeGh:
    def __init__(self, pr_state="open", head_repo="o/r", head=HEAD, statuses=()):
        self.pr = {
            "state": pr_state,
            "head": {"sha": head, "repo": {"full_name": head_repo}},
        }
        self.statuses = list(statuses)
        self.posts = []

    def __call__(self, *args):
        if args == ("api", "repos/o/r/pulls/7"):
            return json.dumps(self.pr)
        if args == ("api", f"repos/o/r/commits/{self.pr['head']['sha']}/statuses"):
            return json.dumps(self.statuses)
        if args[:3] == ("api", "-X", "POST"):
            self.posts.append(args)
            return "{}"
        raise AssertionError(f"unexpected gh call: {args}")


def test_posts_status_on_head():
    gh = FakeGh()
    out = sync("o/r", "7", REAL_COMMENT, gh)
    assert out.startswith("posted")
    assert gh.posts == [
        (
            "api", "-X", "POST", f"repos/o/r/statuses/{HEAD}",
            "-f", "state=success",
            "-f", f"target_url={URL}",
            "-f", "description=Cloudflare preview",
            "-f", f"context={CONTEXT}",
        )
    ]


def test_shows_the_link_in_the_status_comment():
    seen = []
    gh = FakeGh()
    out = sync("o/r", "7", REAL_COMMENT, gh, lambda head, url: seen.append((head, url)) or "comment ok")
    assert seen == [(HEAD, URL)] and out.endswith("; comment ok")


def test_shows_the_link_even_when_the_status_already_exists():
    seen = []
    gh = FakeGh(statuses=[{"context": CONTEXT, "state": "success", "target_url": URL}])
    sync("o/r", "7", REAL_COMMENT, gh, lambda head, url: seen.append(url) or "")
    assert seen == [URL] and gh.posts == []


def test_a_failing_comment_update_does_not_lose_the_status():
    def broken(head, url):
        raise RuntimeError("api down")

    gh = FakeGh()
    out = sync("o/r", "7", REAL_COMMENT, gh, broken)
    assert out.startswith("posted") and "not updated" in out and len(gh.posts) == 1


def test_no_link_for_a_stale_comment():
    seen = []
    gh = FakeGh(head="9" * 40)
    sync("o/r", "7", REAL_COMMENT, gh, lambda *a: seen.append(a) or "")
    assert seen == []


def test_idempotent_when_status_already_set():
    gh = FakeGh(statuses=[{"context": CONTEXT, "state": "success", "target_url": URL}])
    assert sync("o/r", "7", REAL_COMMENT, gh).startswith("skip")
    assert gh.posts == []


def test_reposts_when_newest_status_has_other_url():
    old = {"context": CONTEXT, "state": "success", "target_url": "https://x"}
    gh = FakeGh(statuses=[old])
    assert sync("o/r", "7", REAL_COMMENT, gh).startswith("posted")


def test_skips_stale_comment():
    gh = FakeGh(head="9999999999999999999999999999999999999999")
    assert sync("o/r", "7", REAL_COMMENT, gh).startswith("skip: comment is for")
    assert gh.posts == []


def test_skips_fork_pr():
    gh = FakeGh(head_repo="someone/r")
    assert sync("o/r", "7", REAL_COMMENT, gh) == "skip: fork PR"
    assert gh.posts == []


def test_skips_closed_pr():
    gh = FakeGh(pr_state="closed")
    assert sync("o/r", "7", REAL_COMMENT, gh) == "skip: PR is not open"
    assert gh.posts == []
