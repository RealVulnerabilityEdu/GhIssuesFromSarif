#!/bin/sh

if [ "$#" -ne 6 ] && [ "$#" -ne 7 ]; then
	echo "Usage: $0 <github_repo> <git_sha> <sarif_data_path> <toolkit_path> <qhelp_root> <issue_data_path> [<issue_body_template>]"
	exit 1
fi

GITHUB_REPO=$1 # owner/repo
GIT_SHA=$2     # commit sha
SARIF_DATA_PATH=$3
TOOLKIT_PATH=$4
QHELP_ROOT=$5 # http://www.sci.brooklyn.cuny.edu/~chen/uploads/research/qhelp
ISSUE_DATA_PATH=$6

if [ "$#" -eq 7 ]; then
	ISSUE_BODY_TEMPLATE=$7
else
	ISSUE_BODY_TEMPLATE=""
fi

if ! mkdir -p "${ISSUE_DATA_PATH}"; then
	echo "Failed to create directory: ${ISSUE_DATA_PATH}"
	exit 1
fi

for f in "${SARIF_DATA_PATH}"/*.sarif; do
	if [ -n "${ISSUE_BODY_TEMPLATE}" ]; then
		if ! python "${TOOLKIT_PATH}/assemble_gh_issue_data.py" \
			"${f}" \
			"${GITHUB_REPO}" \
			"${GIT_SHA}" \
			"${QHELP_ROOT}" \
			--output-dir "${ISSUE_DATA_PATH}" \
			--output-human-readable true \
			--issue-body-template "${ISSUE_BODY_TEMPLATE}"; then
			echo "Failed to parse SARIF file: ${f}"
			exit 1
		fi
	else
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
	fi
done
exit 0
