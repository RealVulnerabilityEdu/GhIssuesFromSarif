# Run tasks

1. Generate help files

   ```bash
   sarif2issues_path="."
   bash ${sarif2issues_path}/src/qhelp/mk_qhelp_from_qhelp.sh
   ```

1. Generate ID-Help mapping

   ```bash
   python ${sarif2issues_path}/src/qhelp/query_help_map.py codeql qhelp qhelp/codeql_id_help_mapping.csv
   ```
