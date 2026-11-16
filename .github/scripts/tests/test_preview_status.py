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
    assert sync("o/r", "7", REAL_COMMENT, gh).startswith("skip: preview is for")
    assert gh.posts == []


def test_skips_fork_pr():
    gh = FakeGh(head_repo="someone/r")
    assert sync("o/r", "7", REAL_COMMENT, gh) == "skip: fork PR"
    assert gh.posts == []


def test_skips_closed_pr():
    gh = FakeGh(pr_state="closed")
    assert sync("o/r", "7", REAL_COMMENT, gh) == "skip: PR is not open"
    assert gh.posts == []


# --- Check-run mode (#127): the URL from Cloudflare's check run ------------

from preview_status import parse_check_run, sync_from_check_run  # noqa: E402

# A real "Workers Builds: ghrweb" check run summary (PR #125), verbatim.
REAL_SUMMARY = (
    "\nBuild ID: [fd27310d-edfa-47a8-8a7e-8b2750676cfe](https://dash.cloudflare.com/4d332016793fb6b37edf699d14677f2b"
    "/workers/services/view/ghrweb/production/builds/fd27310d-edfa-47a8-8a7e-8b2750676cfe)\n"
    "Script: [ghrweb](https://dash.cloudflare.com/4d332016793fb6b37edf699d14677f2b/workers/services/view/ghrweb/production)\n"
    "Version ID: d886f897-3b1f-4a6b-9067-a45c67e61eeb\n"
    "Preview URL: https://d886f897-ghrweb.enosi-ellinon-ollandias.workers.dev\n"
    "Preview Alias URL: https://cms-news-gr-nvidia-ghrweb.enosi-ellinon-ollandias.workers.dev\n"
)
RUN_URL_PREVIEW = "https://d886f897-ghrweb.enosi-ellinon-ollandias.workers.dev"


def check_run(status="completed", conclusion="success", summary=REAL_SUMMARY, app="cloudflare-workers-and-pages", started="2026-11-16T14:56:00Z"):
    return {
        "app": {"slug": app},
        "status": status,
        "conclusion": conclusion,
        "started_at": started,
        "output": {"summary": summary},
    }


def test_parse_real_check_run():
    assert parse_check_run(check_run()) == RUN_URL_PREVIEW


@pytest.mark.parametrize(
    "run",
    [
        check_run(status="in_progress", conclusion=None),
        check_run(conclusion="failure"),
        check_run(app="someone-else"),
        check_run(summary="Build ID: x\n"),
        check_run(summary=REAL_SUMMARY.replace(RUN_URL_PREVIEW, "https://evil.example.com")),
    ],
)
def test_parse_check_run_rejects(run):
    assert parse_check_run(run) is None


class CheckRunGh(FakeGh):
    """FakeGh that also answers the check-runs API, one answer per poll."""

    def __init__(self, polls, **kw):
        super().__init__(**kw)
        self.polls = list(polls)
        self.check_calls = 0

    def __call__(self, *args):
        if args[0] == "api" and "/check-runs?check_name=" in args[1]:
            assert args[1] == f"repos/o/r/commits/{HEAD}/check-runs?check_name=Workers%20Builds%3A%20ghrweb"
            self.check_calls += 1
            runs = self.polls.pop(0) if len(self.polls) > 1 else self.polls[0]
            return json.dumps({"check_runs": runs})
        return super().__call__(*args)


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_check_run_mode_waits_for_the_build_then_posts():
    gh = CheckRunGh([[], [check_run(status="in_progress", conclusion=None)], [check_run()]])
    clock = Clock()
    out = sync_from_check_run("o/r", "7", HEAD, gh, wait_s=600, sleep=clock.sleep, clock=clock)
    assert out.startswith("posted deploy/preview")
    assert gh.check_calls == 3
    assert any(f"target_url={RUN_URL_PREVIEW}" in a for a in gh.posts[0])


def test_check_run_mode_uses_the_newest_run():
    old = check_run(started="2026-11-16T14:00:00Z", summary=REAL_SUMMARY.replace("d886f897", "aaaaaaaa"))
    gh = CheckRunGh([[old, check_run(started="2026-11-16T15:00:00Z")]])
    clock = Clock()
    sync_from_check_run("o/r", "7", HEAD, gh, wait_s=60, sleep=clock.sleep, clock=clock)
    assert any(f"target_url={RUN_URL_PREVIEW}" in a for a in gh.posts[0])


def test_check_run_mode_gives_up_after_the_wait():
    gh = CheckRunGh([[]])
    clock = Clock()
    out = sync_from_check_run("o/r", "7", HEAD, gh, wait_s=60, sleep=clock.sleep, clock=clock)
    assert out.startswith("skip: no finished Cloudflare build")
    assert gh.posts == []


def test_check_run_mode_skips_a_failed_build():
    gh = CheckRunGh([[check_run(conclusion="failure")]])
    clock = Clock()
    out = sync_from_check_run("o/r", "7", HEAD, gh, wait_s=60, sleep=clock.sleep, clock=clock)
    assert "no usable preview URL" in out
    assert gh.posts == []


def test_check_run_mode_skips_when_a_newer_save_moved_the_head():
    gh = CheckRunGh([[check_run()]], head="f" * 40)
    clock = Clock()

    # The check runs are looked up for HEAD, but the PR has moved on.
    def gh_for_old_sha(*args):
        if args[0] == "api" and "/check-runs?" in args[1]:
            return json.dumps({"check_runs": [check_run()]})
        return gh(*args)

    out = sync_from_check_run("o/r", "7", HEAD, gh_for_old_sha, wait_s=60, sleep=clock.sleep, clock=clock)
    assert out.startswith("skip: preview is for")
    assert gh.posts == []
