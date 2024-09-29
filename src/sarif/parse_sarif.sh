#!/bin/sh


if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <github_repo> <git_sha> <sarif_data_path> <toolkit_path> <qhelp_root> <issue_data_path>"
    exit 1
fi

GITHUB_REPO=$1      # owner/repo
GIT_SHA=$2          # commit sha
SARIF_DATA_PATH=$3  
TOOLKIT_PATH=$4
QHELP_ROOT=$5       # http://www.sci.brooklyn.cuny.edu/~chen/uploads/research/qhelp
ISSUE_DATA_PATH=$6


if ! mkdir -p "${ISSUE_DATA_PATH}"; then
    echo "Failed to create directory: ${ISSUE_DATA_PATH}"
    exit 1
fi

for f in ${SARIF_DATA_PATH}/*.sarif; do
    if ! python "${TOOLKIT_PATH}/assemble_gh_issue_data.py" \
        "${f}" \
        "${GITHUB_REPO}" \
        "${GIT_SHA}" \
        "${QHELP_ROOT}" \
        --output-dir "${ISSUE_DATA_PATH}" \
        --output-human-readable true; then
        echo "Failed to parse SARIF file: ${f}"
        exit 1
    fi
done
exit 0

