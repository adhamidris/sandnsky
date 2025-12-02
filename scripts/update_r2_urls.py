#!/usr/bin/env python
"""
Replace old R2 public URLs with new ones across all text/char columns.

Usage:
  python scripts/update_r2_urls.py \
      --old https://old-domain \
      --new https://new-domain \
      [--apply] [--tables web_trip web_tripgalleryimage ...]

By default runs in dry-run mode (reports matches but does not update).
Use --apply to perform updates.

Requires Django settings; run from project root where manage.py lives.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

TEXT_DATA_TYPES = {
    "char",
    "varchar",
    "tinytext",
    "text",
    "mediumtext",
    "longtext",
}


def get_text_columns(include_tables: Iterable[str] | None = None) -> List[Tuple[str, str]]:
    table_filter = tuple(include_tables) if include_tables else None
    with connection.cursor() as cursor:
        params = [connection.settings_dict["NAME"], *([] if not table_filter else table_filter)]
        table_clause = ""
        if table_filter:
            placeholders = ",".join(["%s"] * len(table_filter))
            table_clause = f" AND table_name IN ({placeholders})"
        cursor.execute(
            f"""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND data_type IN ({','.join(['%s'] * len(TEXT_DATA_TYPES))})
              {table_clause}
            ORDER BY table_name, column_name
            """,
            [connection.settings_dict["NAME"], *TEXT_DATA_TYPES, *(table_filter or [])],
        )
        rows = cursor.fetchall()
    return [(row[0], row[1]) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace old R2 public URLs in DB")
    parser.add_argument("--old", required=True, help="Old domain/prefix to replace")
    parser.add_argument("--new", required=True, help="New domain/prefix")
    parser.add_argument(
        "--substring",
        action="store_true",
        help="Treat --old as plain substring rather than literal prefix",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform updates (default dry-run)",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Optional list of specific tables to scan (defaults to all text columns)",
    )
    args = parser.parse_args()

    columns = get_text_columns(args.tables)
    if not columns:
        print("No text columns found for provided criteria.")
        sys.exit(0)

    old = args.old
    new = args.new
    like_pattern = f"%{old}%"
    qn = connection.ops.quote_name

    total_matches = 0
    total_updates = 0

    with connection.cursor() as cursor:
        for table, column in columns:
            select_sql = (
                f"SELECT COUNT(*) FROM {qn(table)} "
                f"WHERE {qn(column)} LIKE %s"
            )
            cursor.execute(select_sql, [like_pattern])
            matches = cursor.fetchone()[0]
            if not matches:
                continue

            total_matches += matches
            print(f"{table}.{column}: {matches} matching rows")
            if args.apply:
                update_sql = (
                    f"UPDATE {qn(table)}"
                    f" SET {qn(column)} = REPLACE({qn(column)}, %s, %s)"
                    f" WHERE {qn(column)} LIKE %s"
                )
                cursor.execute(update_sql, [old, new, like_pattern])
                updated = cursor.rowcount
                total_updates += updated
                print(f"  → updated {updated} rows")

    if args.apply:
        print(f"Done. Updated {total_updates} rows total across {len(columns)} columns.")
    else:
        print(
            f"Dry run complete. {total_matches} rows would be affected. "
            "Re-run with --apply to modify the database."
        )


if __name__ == "__main__":
    main()
