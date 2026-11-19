"""Act as a reviewer for synthetic test commits."""
import sys


def record_fixture_review(call, scripts, *selection):
    reviewer = [sys.executable, str(scripts / "code_review.py")]
    diff = call(*reviewer, "show", *selection)
    scope = diff.splitlines()[0].split()[1]
    call(*reviewer, "record", *selection, "--scope", scope, "--summary", "测试夹具模拟已审阅这组变更")
    return scope
