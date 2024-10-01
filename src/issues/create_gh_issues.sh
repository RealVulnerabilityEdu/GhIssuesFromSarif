#!/bin/bash -l

###
### To run as part of GitHub Actions, this needs to run as a login shell via the -l option.
###

function is_debugging() {
	if [[ -z ${_SARIF2GHI_MOCKING_FOR_DEBUG_} ]]; then
		return 1
	else
		return 0
	fi
}

if [[ $# -gt 0 ]]; then
	ISSUE_DATA_PATH=$1
fi

if [[ -z ${ISSUE_DATA_PATH+x} ]]; then
	ISSUE_DATA_PATH="_real_word_vul_edu_/issues"
fi

if [[ -d "${ISSUE_DATA_PATH}" ]]; then
	n=0
	for f in "${ISSUE_DATA_PATH}"/*_title.md; do
		t_f=$f
		b_f=${ISSUE_DATA_PATH}/issue_${n}_body.md
		if [[ -f "${t_f}" && -f "${b_f}" ]]; then
			title=$(<"${t_f}")
			body=$(<"${b_f}")
			if is_debugging; then
				echo "gh issue create --title \"${title}\" --body \"${body}\""
			else
				gh issue create --title "${title}" --body "${body}"
			fi
		fi
		((n++)) || true
	done
fi
exit 0
