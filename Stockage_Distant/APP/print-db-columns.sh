#!/usr/bin/env bash
set -euo pipefail

# Print all columns for all SQLite tables in a readable format.
# Usage:
#   ./print-db-columns.sh
#   ./print-db-columns.sh /path/to/database.db
#   ./print-db-columns.sh --include-internal
#   ./print-db-columns.sh --help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DB="$SCRIPT_DIR/app.db"
DB_PATH="$DEFAULT_DB"
INCLUDE_INTERNAL=0

show_help() {
  cat <<'EOF'
Print all columns of all tables from a SQLite database.

Usage:
  ./print-db-columns.sh [DB_PATH] [--include-internal]

Arguments:
  DB_PATH               Optional path to SQLite database (default: ./app.db)

Options:
  --include-internal    Include SQLite internal tables (sqlite_*)
  -h, --help            Show this help
EOF
}

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      show_help
      exit 0
      ;;
    --include-internal)
      INCLUDE_INTERNAL=1
      ;;
    *)
      if [[ "$DB_PATH" != "$DEFAULT_DB" ]]; then
        echo "Error: multiple database paths provided." >&2
        exit 1
      fi
      DB_PATH="$arg"
      ;;
  esac
done

if [[ ! -f "$DB_PATH" ]]; then
  echo "Error: database file not found: $DB_PATH" >&2
  exit 1
fi

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "Error: sqlite3 is required but was not found in PATH." >&2
  echo "Install it and re-run this script." >&2
  exit 1
fi

TABLE_FILTER="name NOT LIKE 'sqlite_%'"
if [[ "$INCLUDE_INTERNAL" -eq 1 ]]; then
  TABLE_FILTER="1=1"
fi

mapfile -t TABLES < <(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND $TABLE_FILTER ORDER BY name;")

if [[ "${#TABLES[@]}" -eq 0 ]]; then
  echo "No tables found in: $DB_PATH"
  exit 0
fi

echo "Database: $DB_PATH"
echo "Tables found: ${#TABLES[@]}"
echo

for table in "${TABLES[@]}"; do
  echo "============================================================"
  echo "Table: $table"
  echo "------------------------------------------------------------"
  printf "%-4s | %-24s | %-12s | %-8s | %-15s | %-3s\n" "CID" "COLUMN" "TYPE" "NULL" "DEFAULT" "PK"
  echo "--------------------------------------------------------------------------"

  sqlite3 -separator '|' "$DB_PATH" "PRAGMA table_info('$table');" | while IFS='|' read -r cid name ctype notnull dflt pk; do
    [[ -z "$dflt" ]] && dflt="NULL"
    nullable="YES"
    [[ "$notnull" == "1" ]] && nullable="NO"
    printf "%-4s | %-24s | %-12s | %-8s | %-15s | %-3s\n" "$cid" "$name" "$ctype" "$nullable" "$dflt" "$pk"
  done
  echo
done
