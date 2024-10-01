#!/bin/bash

###
### Generrable query help files for human consumption (in GitHub markdown format)
###

if ! which codeql >/dev/null 2>&1; then
	echo "CodeQL not found in PATH. Please install/setup CodeQL CLI."
	exit 1
fi

CODEQL_REPO=codeql
QHELP_DIR=qhelp

if [[ ! -d "${CODEQL_REPO}" ]]; then
	git clone git@github.com:github/codeql.git "${CODEQL_REPO}"
fi

find "${CODEQL_REPO}" -name "*.qhelp" | while read -r f; do
	lang=$(echo "$f" | cut -d"/" -f2)
	[[ -d "${QHELP_DIR}/${lang}" ]] || mkdir -p "${QHELP_DIR}/${lang}"
	codeql generate query-help --format=markdown --output "${QHELP_DIR}/${lang}" "$f"
done
