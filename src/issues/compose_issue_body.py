"""Compose issue body for GH issue creation"""

import argparse
import pathlib
import urllib.parse
import urllib.request


class IssueBodyTemplate:
    """Issue body template for GH issue creation"""

    def __init__(self, template_location):
        p = urllib.parse.urlparse(template_location)
        if not p.scheme:
            uri = pathlib.Path(template_location).resolve().as_uri()
        else:
            uri = template_location
        with urllib.request.urlopen(uri) as f:
            self.template = f.read().decode("utf-8")

    def fill(
        self, vulnerability_msg, short_snippet_url, long_code_snippet_url, issue_help
    ):
        issue_body = self.template.replace("{{vulnerability-message}}", vulnerability_msg)
        issue_body = issue_body.replace(
            "{{code-snippet-without-context}}", short_snippet_url
        )
        issue_body = issue_body.replace(
            "{{code-snippet-with-context}}", long_code_snippet_url
        )
        issue_body = issue_body.replace("{{vulnerability-help}}", issue_help)
        return issue_body


def parse_command_line():
    parser = argparse.ArgumentParser(
        description="Issue body template for GH issue creation"
    )
    parser.add_argument(
        "template_location",
        type=str,
    )
    parser.add_argument(
        "vulnerability_msg",
        type=str,
    )
    parser.add_argument(
        "short_snippet_url",
        type=str,
    )
    parser.add_argument(
        "long_code_snippet_url",
        type=str,
    )
    parser.add_argument(
        "issue_help",
        type=str,
    )
    return parser.parse_args()


def compose_issue_body(
    template_location,
    vulnerability_msg,
    short_snippet_url,
    long_code_snippet_url,
    issue_help,
):
    issue_body_template = IssueBodyTemplate(template_location)
    issue_body = issue_body_template.fill(
        vulnerability_msg, short_snippet_url, long_code_snippet_url, issue_help
    )
    return issue_body


def main(
    template_location,
    vulnerability_msg,
    short_snippet_url,
    long_code_snippet_url,
    issue_help,
):
    issue_body = compose_issue_body(
        template_location,
        vulnerability_msg,
        short_snippet_url,
        long_code_snippet_url,
        issue_help,
    )
    print(issue_body)


if __name__ == "__main__":
    args = parse_command_line()
    main(
        args.template_location,
        args.vulnerability_msg,
        args.short_snippet_url,
        args.long_code_snippet_url,
        args.issue_help,
    )
