"""Establishing mapping between ql and ql help"""

import argparse
import csv
import os
import pathlib

CODQl_LANGS = (
    "cpp",
    "csharp",
    "go",
    "java",
    "javascript",
    "misc",
    "python",
    "ql",
    "ruby",
    "rust",
    "shared",
    "swift",
)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        description="Establishing mapping between ql and ql help"
    )
    parser.add_argument(
        "codeql_repo",
        help="Path to the codeql repository",
    )
    parser.add_argument(
        "qhelp_md_dir",
        help="Path to the directory containing the ql help markdown files",
    )
    parser.add_argument(
        "out_mapping_file",
        help="Path to the output file containing the mapping",
    )
    return parser.parse_args()


def get_rule_id(ql_path):
    with open(ql_path, mode="rt", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith(" * @id "):
            return line.replace(" * @id ", "").strip()
    # raise ValueError(f"No rule id found in ql file {ql_path}")
    return None


def get_qhelp_markdown_path(codeql_repo_dir, qhelp_path, qhelp_md_dir):
    parts = pathlib.Path(os.path.relpath(qhelp_path, start=codeql_repo_dir)).parts
    lang = parts[0]
    if lang not in CODQl_LANGS:
        raise ValueError(f"Unexpected language in qhelp_path: {lang}")

    if codeql_repo_dir not in qhelp_path:
        raise ValueError(
            "qhelp_path does not contain codeql_repo_dir, "
            f"expected {codeql_repo_dir}/..., got {qhelp_path}"
        )
    dirs = pathlib.Path(qhelp_path).parts
    if len(dirs) < 2:
        raise ValueError(
            "qhelp_path is too short, expected at least 2 parts, "
            "but found {qhelp_path}"
        )
    if "src" not in dirs:
        raise ValueError("qhelp_path does not contain 'src', got '{qhelp_path}'")
    src_indx = dirs.index("src")
    d_qhelp = dirs[src_indx + 1 :]
    f_qhelp = d_qhelp[-1]
    d_qhelp = d_qhelp[:-1]
    f_qhelp = f"{os.path.splitext(f_qhelp)[0]}.md"

    return os.path.join(qhelp_md_dir, lang, *d_qhelp, f_qhelp)


def make_mapping(codeql_repo, qhelp_md_dir):
    mapping = []
    for root, _, file_names in os.walk(codeql_repo):
        for f in file_names:
            if f.endswith(".ql"):
                ql_path = os.path.join(root, f)
                rule_id = get_rule_id(ql_path)
                qhelp_path = os.path.join(root, f"{os.path.splitext(f)[0]}.qhelp")
                if rule_id and os.path.exists(qhelp_path):
                    ql_path = os.path.relpath(ql_path, start=codeql_repo)
                    qhelp_md_path = get_qhelp_markdown_path(
                        codeql_repo, qhelp_path, qhelp_md_dir
                    )
                    qhelp_path = os.path.relpath(qhelp_path, start=codeql_repo)
                    qhelp_md_path = os.path.relpath(qhelp_md_path, start=qhelp_md_dir)
                    mapping.append((rule_id, ql_path, qhelp_path, qhelp_md_path))
    return mapping


def validate_mapping(mapping, qhelp_md_dir):
    for _, _, _, qhelp_md_path in mapping:
        if not os.path.exists(os.path.join(qhelp_md_dir, qhelp_md_path)):
            print(f"qhelp_md_path does not exist: {qhelp_md_path}")


def save_to_csv(mapping, out_mapping_file):
    with open(out_mapping_file, mode="wt", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rule_id", "ql_path", "qhelp_path", "qhelp_md_path"])
        writer.writerows(mapping)


def main(codeql_repo, qhelp_md_dir, out_mapping_file):
    mapping = make_mapping(codeql_repo, qhelp_md_dir)
    validate_mapping(mapping, qhelp_md_dir)
    save_to_csv(mapping, out_mapping_file)


if __name__ == "__main__":
    args = parse_cmdline()
    main(args.codeql_repo, args.qhelp_md_dir, args.out_mapping_file)
