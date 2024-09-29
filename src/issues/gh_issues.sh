#!/bin/bash

ISSUE_DATA_PATH="_real_word_vul_edu_/issues"

if [[ -d "${ISSUE_DATA_PATH}" ]]; then
    n=0
    for f in ${ISSUE_DATA_PATH}/*_title.md; do
        t_f=${ISSUE_DATA_PATH}/issue_${n}_title.md
        b_f=${ISSUE_DATA_PATH}/issue_${n}_body.md
        if [[ -f "${t_f}" && -f "${b_f}" ]]; then
            title=$(<${t_f})
            body=$(<${b_f})
            gh issue create --title "${title}" --body "${body}"
        fi
        let n++
    done
fi
exit 0