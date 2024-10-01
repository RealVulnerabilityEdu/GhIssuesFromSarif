"""Test the compose_issue_body function."""

from issues.compose_issue_body import compose_issue_body


def test_create_issue_body_1():
    actual_body = compose_issue_body(
        "data/issue_body_template.md",
        "VERY BAD VULNERABILITY 1.",
        "SNIPPET_1",
        "SNIPPET_1_WITH_CONTEXT",
        "The_BIG_HELP_1",
    )
    with open("data/issue/issue_body_1.md", mode="rt", encoding="utf-8") as f:
        expected_body = f.read()
    assert actual_body == expected_body

def test_create_issue_body_2():
    actual_body = compose_issue_body(
        "data/issue_body_template.md",
        "VERY BAD VULNERABILITY #2.",
        "https://SNIPPET_2",
        "https://SNIPPET_2_WITH_CONTEXT",
        "The_BIG_HELP_2_LINE_1\nThe_BIG_HELP_2_LINE_2",
    )
    with open("data/issue/issue_body_2.md", mode="rt", encoding="utf-8") as f:
        expected_body = f.read()
    assert actual_body == expected_body
