"""Process Sarif file and assemble data for GH issue creation

   This initial version does not use any Sarif library to process the file
   and it also does not depend on any external python packages.

   Tested with Python 3.11.

   For debug purpose, use environment variable to set the location of the
   codebase, i.e.,

      _SARIF2GHISSUE_LOCAL_CODEBASE_LOCATION_=path/to/codebase
"""

import argparse
import csv
import json
import os
import pathlib
import sys
import urllib
import urllib.parse
import urllib.request

DEFAULT_ISSUE_BODY_TEMPLATE = (
    "We have found a potential software security vulnerability: "
    "{{vulnerability-message}}: \n\n"
    "The following shows the code snippet where the vulnerability is found:\n\n"
    "{{code-snippet-without-context}}"
    "\n\n"
    "The following shows more complete picture with "
    "lines above and below the vulnerable code:\n\n"
    "{{code-snippet-with-context}}"
    "\n\n"
    "{{vulnerability-help}}"
)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        description="Assemble software vulnerability data for GH issue creating"
    )
    parser.add_argument(
        "sarif_file",
        type=str,
        help="Path to the SARIF file containing vulnerability data",
    )
    parser.add_argument(
        "repository",
        type=str,
        help=(
            "Name (owner/repo_name) of the GitHub repository "
            "containing the vulnerabilities",
        ),
    )
    parser.add_argument(
        "commit_sha",
        type=str,
        help="SHA of the commit that introduced the vulnerabilities",
    )
    parser.add_argument(
        "vul_helper_root",
        type=str,
        help="Root directory/URL of the vulnerability reference",
    )
    parser.add_argument(
        "--issue-body-template",
        type=str,
        default="",
        help="Path to the issue body template",
        required=False,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="issues",
        help="Output directory to save the issue data",
        required=False,
        dest="output_dir",
    )
    parser.add_argument(
        "--output-human-readable",
        type=bool,
        default=False,
        help="Output human readable issue data",
        required=False,
        dest="human_readable",
    )
    return parser.parse_args()


def get_gh_code_snippet_single_line(repository, commit_sha, location, region):
    line_no = region["startLine"]
    snippet_url = (
        f"https://github.com/{repository}/blob/" f"{commit_sha}/{location}#L{line_no}"
    )
    return snippet_url


def get_gh_code_snippet_multi_line(repository, commit_sha, location, region):
    line_no_begin = region["startLine"]
    line_no_end = region["endLine"]
    snippet_url = (
        f"https://github.com/{repository}/blob/{commit_sha}/"
        f"{location}#L{line_no_begin}-L{line_no_end}"
    )
    return snippet_url


def get_gh_code_snippet_url(repository, commit_sha, location, region):
    if "endLine" not in region:
        snippet_url = get_gh_code_snippet_single_line(
            repository, commit_sha, location, region
        )
    else:
        snippet_url = get_gh_code_snippet_multi_line(
            repository, commit_sha, location, region
        )
    return snippet_url


def make_context_region(region, context_lines=3, location=None, codebase_location=None):
    start_line = region["startLine"]
    end_line = region.get("endLine", start_line)
    start_line = max(1, start_line - context_lines)
    if location:
        if codebase_location:
            code_location = pathlib.Path(codebase_location).joinpath(
                urllib.parse.unquote(location)
            )
        else:
            code_location = urllib.parse.unquote(location)
        nlines = len(open(code_location, mode="rt", encoding="utf-8").readlines())
        end_line = min(end_line + context_lines, nlines)
    else:
        end_line += context_lines
    return {"startLine": start_line, "endLine": end_line}


def get_gh_code_snippet_msg(
    repository, commit_sha, message, location, region, codebase_location=None
):
    message = escape_github_markdown(message)
    msg = f"We have found a potential software security vulnerablity: {message}: \n\n"
    msg += "The following shows the code snippet where the vulnerability is found:\n\n"
    snippet_url = get_gh_code_snippet_url(repository, commit_sha, location, region)
    msg += f"{snippet_url}\n\n"
    msg += (
        "The following shows more complete picture with "
        "lines above and below the vulnerable code:\n\n"
    )
    context_region = make_context_region(
        region, location=location, codebase_location=codebase_location
    )
    snippet_url = get_gh_code_snippet_url(
        repository, commit_sha, location, context_region
    )
    msg += f"{snippet_url}\n\n"
    return msg


def get_gh_short_long_code_snippet_urls(
    repository, commit_sha, location, region, codebase_location=None
):
    short_snippet_url = get_gh_code_snippet_url(
        repository, commit_sha, location, region
    )
    context_region = make_context_region(
        region, location=location, codebase_location=codebase_location
    )
    long_snippet_url = get_gh_code_snippet_url(
        repository, commit_sha, location, context_region
    )
    return short_snippet_url, long_snippet_url


def get_uri(uri_like):
    p = urllib.parse.urlparse(uri_like)
    if not p.scheme:
        uri = pathlib.Path(uri_like).resolve().as_uri()
    else:
        uri = uri_like
    return uri


def escape_github_markdown(text):
    # https://github.com/mattcone/markdown-guide/blob/master/_basic-syntax/escaping-characters.md
    # special_chars = [
    #     "\\",  # 	backslash
    #     r"`",  # 	backtick (see also escaping backticks in code)
    #     r"*",  # 	asterisk
    #     r"",  # 	underscore
    #     r"{",
    #     r"}",  # curly braces
    #     r"[",
    #     r"]",  # brackets
    #     r"<",
    #     r">",  # angle brackets
    #     r"(",
    #     r")",  # parentheses
    #     r"#",  # 	pound sign
    #     r"+",  # 	plus sign
    #     r"-",  # 	minus sign (hyphen)
    #     r".",  # 	dot
    #     r"!",  # 	exclamation mark
    #     r"|",  # 	pipe (see also escaping pipe in tables)
    # ]
    special_chars = [
        r"[",
        r"]",  # brackets
        r"(",
        r")",  # parentheses
    ]
    c_list = [f"\\{c}" if c in special_chars else c for c in text]
    return "".join(c_list)


def load_vul_rule_help_mapping(file_path):
    uri = get_uri(file_path)
    mapping = {}
    with urllib.request.urlopen(uri) as csvfile:
        reader = csv.DictReader(csvfile.read().decode("utf-8").splitlines())
        for row in reader:
            mapping[row["rule_id"]] = row["qhelp_md_path"]
    return mapping


def get_vulnerability_help_msg(helper_root, mapping, rule_id):
    help_uri = get_uri(f"{helper_root}/{mapping[rule_id]}")
    with urllib.request.urlopen(help_uri.replace(" ", "%20")) as f:
        help_md = f.read().decode("utf-8")
    return help_md


class IssueBodyTemplate:
    """Issue body template for GH issue creation"""

    @classmethod
    def load(cls, template_location):
        p = urllib.parse.urlparse(template_location)
        if not p.scheme:
            uri = pathlib.Path(template_location).resolve().as_uri()
        else:
            uri = template_location
        with urllib.request.urlopen(uri) as f:
            return f.read().decode("utf-8")

    def __init__(self, issue_template, is_uri=True):
        if is_uri:
            self.template = self.load(issue_template)
        else:
            self.template = issue_template

    def fill(
        self, vulnerability_msg, short_snippet_url, long_code_snippet_url, issue_help
    ):
        issue_body = self.template.replace(
            "{{vulnerability-message}}", vulnerability_msg
        )
        issue_body = issue_body.replace(
            "{{code-snippet-without-context}}", short_snippet_url
        )
        issue_body = issue_body.replace(
            "{{code-snippet-with-context}}", long_code_snippet_url
        )
        issue_body = issue_body.replace("{{vulnerability-help}}", issue_help)
        return issue_body


def compose_issue_body(
    issue_template,
    vulnerability_msg,
    short_snippet_url,
    long_code_snippet_url,
    issue_help,
):
    issue_body_template = IssueBodyTemplate(issue_template, is_uri=False)
    issue_body = issue_body_template.fill(
        vulnerability_msg, short_snippet_url, long_code_snippet_url, issue_help
    )
    return issue_body


def make_issue_list(
    sarif_file,
    repository,
    commit_sha,
    vul_helper_root,
    issue_body_template=None,
    local_codebase_location=None,
    only_first_location=True,
):
    if not issue_body_template:
        issue_body_template = DEFAULT_ISSUE_BODY_TEMPLATE
    else:
        issue_body_template = IssueBodyTemplate.load(issue_body_template)

    with open(sarif_file, mode="rt", encoding="utf-8") as f:
        sarif_data = json.load(f)
    if "runs" not in sarif_data:
        raise ValueError("Invalid SARIF file for GH issue creation: no 'runs'")

    runs = sarif_data["runs"]
    issue_list = []
    for run in runs:
        if "results" not in run:
            raise ValueError(
                "Invalid SARIF file for GH issue creation: no 'results' in 'runs'"
            )
        results = run["results"]
        if len(results) == 0:
            print("No vulnerabilities found in the SARIF file")
            return

        mapping = load_vul_rule_help_mapping(f"{vul_helper_root}/id_help_mapping.csv")

        for r in results:
            rule_id = r["ruleId"]
            vulnerability_msg = escape_github_markdown(r["message"]["text"])
            for vul in r["locations"]:
                location = vul["physicalLocation"]["artifactLocation"]["uri"]
                region = vul["physicalLocation"]["region"]

                (
                    short_snippet_url,
                    long_snippet_url,
                ) = get_gh_short_long_code_snippet_urls(
                    repository,
                    commit_sha,
                    location,
                    region,
                    codebase_location=local_codebase_location,
                )
                issue_help_md = get_vulnerability_help_msg(
                    vul_helper_root, mapping, rule_id
                )
                issue_body = compose_issue_body(
                    issue_body_template,
                    vulnerability_msg,
                    short_snippet_url,
                    long_snippet_url,
                    issue_help_md,
                )
                issue = {
                    "title": f"Potential software security vulnerability: {rule_id}",
                    "body": issue_body,
                }
                issue_list.append(issue)
                if only_first_location:
                    break
    return issue_list


def disp_issue_list(issue_list):
    # print(json.dumps(issue_list, indent=2))
    for idx, issue in enumerate(issue_list):
        print(f"\n\n-------- Issue {idx} ---------")
        print(issue["title"])
        print(issue["body"])
        print("\n\n")


def save_issue_list(issue_list, output_dir):
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    for idx, issue in enumerate(issue_list):
        title_file_path = f"{output_dir}/issue_{idx}_title.md"
        with open(title_file_path, mode="wt", encoding="utf-8") as f:
            f.write(issue["title"])
        body_file_path = f"{output_dir}/issue_{idx}_body.md"
        with open(body_file_path, mode="wt", encoding="utf-8") as f:
            f.write(issue["body"])
        print(
            f"Saved issue {idx} to {title_file_path} and {body_file_path}",
            file=sys.stderr,
        )


def get_local_codebase_location():
    return os.environ.get("_SARIF2GHISSUE_LOCAL_CODEBASE_LOCATION_")


def main(
    sarif_file,
    repository,
    commit_sha,
    vul_helper_root,
    issue_body_template,
    output_dir,
    human_readable,
):
    issue_list = make_issue_list(
        sarif_file,
        repository,
        commit_sha,
        vul_helper_root,
        issue_body_template=issue_body_template,
        local_codebase_location=get_local_codebase_location(),
    )
    if not issue_list:
        print("No vulnerabilities found in the SARIF file", file=sys.stderr)
        return
    if human_readable:
        disp_issue_list(issue_list)
    if output_dir:
        save_issue_list(issue_list, output_dir)


if __name__ == "__main__":
    args = parse_cmdline()
    main(
        args.sarif_file,
        args.repository,
        args.commit_sha,
        args.vul_helper_root,
        args.issue_body_template,
        args.output_dir,
        args.human_readable,
    )
