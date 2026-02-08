#!/usr/bin/env python3
"""
MarketGPS SQLite → PostgreSQL Migration Script
Reads from SQLite, creates PostgreSQL schema, and migrates all data.

Usage:
    python scripts/migrate_to_postgres.py --sqlite-path storage/marketgps.db --pg-url postgresql://user:pass@host/db

Options:
    --sqlite-path      Path to SQLite database file
    --pg-url           PostgreSQL connection URL
    --batch-size       Batch size for inserts (default: 1000)
    --dry-run          Show what would be done without executing
    --tables           Comma-separated list of tables to migrate (optional, migrate all if not specified)
"""

import argparse
import sqlite3
import psycopg2
from psycopg2 import sql
import sys
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Table migration order respecting foreign keys
MIGRATION_ORDER = [
    'universe',
    'gating_status',
    'scores_latest',
    'scores_history',
    'rotation_state',
    'users',
    'user_profiles',
    'sessions',
    'subscriptions_state',
    'watchlist',
    'alert_rules',
    'alerts',
    'news_articles',
    'jobs_queue',
    'usage_daily',
    'user_settings',
    'user_interest',
    'provider_logs',
    'calibration_params',
    'asset_logos',
    'app_settings',
    'navigation_history',
    'job_runs',
    'scores_staging',
    'gating_status_staging',
]

# SQLite to PostgreSQL type mappings
TYPE_MAPPING = {
    'TEXT': 'TEXT',
    'INTEGER': 'BIGINT',
    'REAL': 'DOUBLE PRECISION',
    'BLOB': 'BYTEA',
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def print_progress(current: int, total: int, table: str) -> None:
    """Print simple progress bar."""
    if total == 0:
        percent = 100
    else:
        percent = int((current / total) * 100)
    bar_length = 40
    filled = int((bar_length * current) // total) if total > 0 else bar_length
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'\r[{bar}] {percent}% - {table} ({current}/{total})', end='', flush=True)


def get_sqlite_schema(conn: sqlite3.Connection) -> Dict[str, List[Tuple]]:
    """Extract table schemas from SQLite database."""
    cursor = conn.cursor()
    schemas = {}

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table_name,) in tables:
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schemas[table_name] = columns

    return schemas


def convert_sqlite_to_postgres_type(sqlite_type: str) -> str:
    """Convert SQLite type to PostgreSQL type."""
    sqlite_type = sqlite_type.upper().strip()

    # Handle type modifiers (e.g., "TEXT DEFAULT")
    base_type = sqlite_type.split()[0] if ' ' in sqlite_type else sqlite_type

    # Map basic types
    if base_type in TYPE_MAPPING:
        return TYPE_MAPPING[base_type]

    # Default to TEXT
    return 'TEXT'


def create_postgres_schema(pg_conn: psycopg2.extensions.connection,
                          sqlite_schema: Dict[str, List[Tuple]],
                          dry_run: bool = False) -> None:
    """Create PostgreSQL schema based on SQLite schema."""
    cursor = pg_conn.cursor()

    for table_name in MIGRATION_ORDER:
        if table_name not in sqlite_schema:
            continue

        columns = sqlite_schema[table_name]
        col_defs = []

        for col_id, col_name, col_type, not_null, default_val, pk in columns:
            pg_type = convert_sqlite_to_postgres_type(col_type)
            col_def = f'{col_name} {pg_type}'

            if pk:
                col_def += ' PRIMARY KEY'
            elif not_null:
                col_def += ' NOT NULL'

            if default_val:
                # Handle SQLite defaults
                if default_val.startswith("'") and default_val.endswith("'"):
                    col_def += f" DEFAULT '{default_val[1:-1]}'"
                elif default_val.upper() in ('CURRENT_TIMESTAMP', 'DATETIME("NOW")'):
                    col_def += ' DEFAULT CURRENT_TIMESTAMP'
                else:
                    try:
                        int(default_val)
                        col_def += f' DEFAULT {default_val}'
                    except ValueError:
                        if default_val.upper() in ('NULL', 'TRUE', 'FALSE', '0', '1'):
                            col_def += f' DEFAULT {default_val}'

            col_defs.append(col_def)

        create_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(col_defs)});'

        print(f'Creating table: {table_name}...', end=' ')
        if dry_run:
            print('[DRY RUN]')
            print(f'  SQL: {create_sql}')
        else:
            try:
                cursor.execute(create_sql)
                pg_conn.commit()
                print('OK')
            except Exception as e:
                pg_conn.rollback()
                print(f'ERROR: {e}')


def create_postgres_indexes(pg_conn: psycopg2.extensions.connection,
                           sqlite_conn: sqlite3.Connection,
                           dry_run: bool = False) -> None:
    """Create indexes on PostgreSQL tables."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all indexes from SQLite
    sqlite_cursor.execute("""
        SELECT name, tbl_name, sql FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
    """)
    indexes = sqlite_cursor.fetchall()

    for idx_name, table_name, idx_sql in indexes:
        # Replace SQLite syntax with PostgreSQL syntax
        pg_idx_sql = idx_sql.replace(f'CREATE INDEX {idx_name}',
                                     f'CREATE INDEX IF NOT EXISTS {idx_name}')

        print(f'Creating index: {idx_name}...', end=' ')
        if dry_run:
            print('[DRY RUN]')
            print(f'  SQL: {pg_idx_sql}')
        else:
            try:
                pg_cursor.execute(pg_idx_sql)
                pg_conn.commit()
                print('OK')
            except Exception as e:
                pg_conn.rollback()
                print(f'SKIPPED (may exist): {e}')


def migrate_table_data(sqlite_conn: sqlite3.Connection,
                      pg_conn: psycopg2.extensions.connection,
                      table_name: str,
                      batch_size: int = 1000,
                      dry_run: bool = False) -> Tuple[int, int]:
    """
    Migrate data from SQLite table to PostgreSQL.
    Returns (rows_migrated, rows_failed)
    """
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get row count
    sqlite_cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    total_rows = sqlite_cursor.fetchone()[0]

    if total_rows == 0:
        return 0, 0

    # Get column names
    sqlite_cursor.execute(f'PRAGMA table_info({table_name})')
    columns = [col[1] for col in sqlite_cursor.fetchall()]

    # Fetch all data in batches
    sqlite_cursor.execute(f'SELECT * FROM {table_name}')
    rows_migrated = 0
    rows_failed = 0
    batch = []

    while True:
        rows = sqlite_cursor.fetchmany(batch_size)
        if not rows:
            break

        batch.extend(rows)

        if len(batch) >= batch_size:
            rows_migrated_batch, rows_failed_batch = _insert_batch(
                pg_cursor, pg_conn, table_name, columns, batch, dry_run
            )
            rows_migrated += rows_migrated_batch
            rows_failed += rows_failed_batch
            batch = []
            print_progress(rows_migrated, total_rows, table_name)

    # Insert remaining rows
    if batch:
        rows_migrated_batch, rows_failed_batch = _insert_batch(
            pg_cursor, pg_conn, table_name, columns, batch, dry_run
        )
        rows_migrated += rows_migrated_batch
        rows_failed += rows_failed_batch

    print_progress(rows_migrated + rows_failed, total_rows, table_name)
    print()  # New line after progress bar

    return rows_migrated, rows_failed


def _insert_batch(pg_cursor, pg_conn, table_name: str, columns: List[str],
                 rows: List[Tuple], dry_run: bool = False) -> Tuple[int, int]:
    """Insert a batch of rows into PostgreSQL."""
    if not rows:
        return 0, 0

    rows_migrated = 0
    rows_failed = 0

    for row in rows:
        try:
            placeholders = ', '.join(['%s'] * len(columns))
            col_names = ', '.join(columns)
            insert_sql = f'INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

            if dry_run:
                # For dry run, just count
                rows_migrated += 1
            else:
                pg_cursor.execute(insert_sql, row)
                rows_migrated += 1
        except Exception as e:
            rows_failed += 1
            if not dry_run:
                pg_conn.rollback()

    if not dry_run:
        try:
            pg_conn.commit()
        except Exception as e:
            pg_conn.rollback()
            rows_failed += len(rows)
            rows_migrated = 0

    return rows_migrated, rows_failed


def verify_migration(sqlite_conn: sqlite3.Connection,
                    pg_conn: psycopg2.extensions.connection,
                    tables: List[str]) -> None:
    """Verify row counts in both databases."""
    print('\n' + '=' * 80)
    print('MIGRATION VERIFICATION')
    print('=' * 80)

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    total_sqlite = 0
    total_postgres = 0
    mismatches = []

    for table in tables:
        # SQLite count
        try:
            sqlite_cursor.execute(f'SELECT COUNT(*) FROM {table}')
            sqlite_count = sqlite_cursor.fetchone()[0]
        except:
            sqlite_count = 0

        # PostgreSQL count
        try:
            pg_cursor.execute(f'SELECT COUNT(*) FROM {table}')
            postgres_count = pg_cursor.fetchone()[0]
        except:
            postgres_count = 0

        total_sqlite += sqlite_count
        total_postgres += postgres_count

        status = '✓' if sqlite_count == postgres_count else '✗'
        print(f'{status} {table:30s} SQLite: {sqlite_count:8d} | PostgreSQL: {postgres_count:8d}')

        if sqlite_count != postgres_count:
            mismatches.append((table, sqlite_count, postgres_count))

    print('=' * 80)
    print(f'Total rows - SQLite: {total_sqlite:8d} | PostgreSQL: {total_postgres:8d}')
    print('=' * 80)

    if mismatches:
        print('\nWARNING: Row count mismatches detected:')
        for table, sqlite_count, postgres_count in mismatches:
            print(f'  {table}: {sqlite_count} → {postgres_count}')


def main():
    parser = argparse.ArgumentParser(
        description='Migrate MarketGPS database from SQLite to PostgreSQL'
    )
    parser.add_argument('--sqlite-path', required=True, help='Path to SQLite database file')
    parser.add_argument('--pg-url', required=True, help='PostgreSQL connection URL')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--tables', help='Comma-separated list of tables to migrate')

    args = parser.parse_args()

    # Determine which tables to migrate
    if args.tables:
        tables_to_migrate = [t.strip() for t in args.tables.split(',')]
    else:
        tables_to_migrate = MIGRATION_ORDER

    print('=' * 80)
    print('MarketGPS SQLite → PostgreSQL Migration')
    print('=' * 80)
    print(f'SQLite path: {args.sqlite_path}')
    print(f'PostgreSQL URL: {args.pg_url}')
    print(f'Batch size: {args.batch_size}')
    print(f'Dry run: {args.dry_run}')
    print(f'Tables: {", ".join(tables_to_migrate[:3])}{"..." if len(tables_to_migrate) > 3 else ""}')
    print('=' * 80)

    try:
        # Connect to SQLite
        print('\nConnecting to SQLite...')
        sqlite_conn = sqlite3.connect(args.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        print('✓ Connected to SQLite')

        # Connect to PostgreSQL
        print('Connecting to PostgreSQL...')
        pg_conn = psycopg2.connect(args.pg_url)
        pg_conn.autocommit = False
        print('✓ Connected to PostgreSQL')

        # Extract SQLite schema
        print('\nExtracting SQLite schema...')
        sqlite_schema = get_sqlite_schema(sqlite_conn)
        print(f'✓ Found {len(sqlite_schema)} tables')

        # Create PostgreSQL schema
        print('\nCreating PostgreSQL schema...')
        create_postgres_schema(pg_conn, sqlite_schema, args.dry_run)

        # Create indexes
        print('\nCreating indexes...')
        create_postgres_indexes(pg_conn, sqlite_conn, args.dry_run)

        # Migrate data
        print('\nMigrating data...')
        total_migrated = 0
        total_failed = 0

        for table in tables_to_migrate:
            if table not in sqlite_schema:
                print(f'SKIPPED: {table} (not in source database)')
                continue

            migrated, failed = migrate_table_data(
                sqlite_conn, pg_conn, table, args.batch_size, args.dry_run
            )
            total_migrated += migrated
            total_failed += failed

        print(f'\nData migration complete: {total_migrated} rows migrated, {total_failed} rows failed')

        # Verify migration
        if not args.dry_run:
            verify_migration(sqlite_conn, pg_conn, tables_to_migrate)

        # Cleanup
        sqlite_conn.close()
        pg_conn.close()

        print('\n✓ Migration complete!')
        return 0

    except Exception as e:
        print(f'\n✗ Migration failed: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
