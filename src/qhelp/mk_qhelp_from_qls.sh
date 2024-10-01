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

langs=(cpp csharp go java javascript misc python ql ruby rust shared swift)
for lang in "${langs[@]}"; do
	if [[ ! -d "${QHELP_DIR}/${lang}" ]]; then
		mkdir -p "${QHELP_DIR}/${lang}"
	fi
	for f in "codeql/${lang}/ql/src/codeql-suites"/*.qls; do
		codeql generate query-help --format=markdown --output "${QHELP_DIR}/${lang}" "$f"
	done
done
