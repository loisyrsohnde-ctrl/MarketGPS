#!/usr/bin/env python3
"""
Password Hash Migration Script for MarketGPS

This script migrates legacy SHA256/PBKDF2 password hashes to secure Argon2 hashes.

IMPORTANT: This script requires knowing the plain text passwords to re-hash them with Argon2.
Since we cannot recover plain text passwords from legacy SHA256 hashes, this script:

1. Detects all legacy hashes in the database
2. Generates a report of which users need migration
3. Allows manual password reset for affected users

USAGE:
    python migrate_passwords.py --report          # Generate migration report
    python migrate_passwords.py --force-reset     # Mark all legacy hashes for forced reset

NOTES:
- Users with Argon2 hashes (already migrated) are skipped
- For legacy SHA256 hashes without recovery method, users will need to reset password on next login
- This maintains security: we don't try to keep insecure hashes
"""

import os
import argparse
from datetime import datetime
from pathlib import Path

parent_dir = os.path.dirname(backend_dir)

# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from password_security import count_legacy_hashes, _is_legacy_sha256, _is_legacy_pbkdf2


def generate_migration_report(db: SQLiteStore) -> dict:
    """
    Generate a report of password migration status.

    Returns:
        Dictionary with detailed migration information
    """
    with db._get_conn() as conn:
        cursor = conn.execute(
            "SELECT user_id, password_hash FROM user_security WHERE password_hash IS NOT NULL"
        )
        rows = cursor.fetchall()

    users = {
        'total': len(rows),
        'legacy': [],
        'argon2': [],
        'unknown': [],
    }

    for user_id, password_hash in rows:
        if _is_legacy_sha256(password_hash) or _is_legacy_pbkdf2(password_hash):
            users['legacy'].append(user_id)
        elif password_hash.startswith('$argon2'):
            users['argon2'].append(user_id)
        else:
            users['unknown'].append(user_id)

    return {
        'timestamp': datetime.now().isoformat(),
        'database': 'SQLite user_security table',
        'users': users,
        'summary': {
            'total_users': len(rows),
            'using_argon2': len(users['argon2']),
            'legacy_hashes': len(users['legacy']),
            'unknown_format': len(users['unknown']),
        }
    }


def print_migration_report(report: dict):
    """Pretty-print the migration report."""
    print("\n" + "=" * 70)
    print("PASSWORD HASH MIGRATION REPORT")
    print("=" * 70)
    print(f"Generated: {report['timestamp']}")
    print(f"Database: {report['database']}")
    print()

    summary = report['summary']
    print(f"Total Users:        {summary['total_users']}")
    print(f"Using Argon2:       {summary['using_argon2']}")
    print(f"Legacy Hashes:      {summary['legacy_hashes']}")
    print(f"Unknown Format:     {summary['unknown_format']}")
    print()

    if report['users']['legacy']:
        print(f"Users with legacy hashes ({len(report['users']['legacy'])}):")
        for user_id in report['users']['legacy'][:10]:
            print(f"  - {user_id}")
        if len(report['users']['legacy']) > 10:
            print(f"  ... and {len(report['users']['legacy']) - 10} more")
        print()

    if report['users']['unknown']:
        print(f"Users with unknown hash format ({len(report['users']['unknown'])}):")
        for user_id in report['users']['unknown'][:10]:
            print(f"  - {user_id}")
        if len(report['users']['unknown']) > 10:
            print(f"  ... and {len(report['users']['unknown']) - 10} more")
        print()

    print("MIGRATION STRATEGY:")
    print("-" * 70)
    print("1. Legacy hashes (SHA256, PBKDF2) are detected but not automatically")
    print("   converted, since we cannot recover the original plain text passwords.")
    print()
    print("2. Security approach: Force password reset for legacy hash users.")
    print("   This ensures:")
    print("   - Users get Argon2 hashes on their new password")
    print("   - Potentially compromised old hashes are replaced")
    print("   - Security is not degraded by keeping old hashes")
    print()
    print("3. RECOMMENDED ACTION:")
    print("   For production deployments:")
    print("   - Track which users have legacy hashes")
    print("   - Send notification asking users to update their password")
    print("   - Set up 'password reset required' flag for next login")
    print()
    print("=" * 70 + "\n")


def generate_sql_for_password_reset_flag(db: SQLiteStore):
    """
    Generate SQL to set a 'password_reset_required' flag for legacy users.
    This would need to be implemented in the database schema.
    """
    with db._get_conn() as conn:
        cursor = conn.execute(
            "SELECT user_id, password_hash FROM user_security WHERE password_hash IS NOT NULL"
        )
        rows = cursor.fetchall()

    legacy_users = [
        user_id for user_id, pwd_hash in rows
        if _is_legacy_sha256(pwd_hash) or _is_legacy_pbkdf2(pwd_hash)
    ]

    if legacy_users:
        print("\nSQL to mark legacy users for password reset:")
        print("-" * 70)
        print("-- Add password_reset_required column (if not exists)")
        print("ALTER TABLE user_security ADD COLUMN password_reset_required INTEGER DEFAULT 0;")
        print()
        print("-- Mark legacy users for password reset")
        for user_id in legacy_users[:5]:
            print(f"UPDATE user_security SET password_reset_required = 1 WHERE user_id = '{user_id}';")
        if len(legacy_users) > 5:
            print(f"-- ... and {len(legacy_users) - 5} more users")
        print()
        print("-- Verify")
        print("SELECT COUNT(*) FROM user_security WHERE password_reset_required = 1;")
        print("-" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate MarketGPS password hashes from SHA256 to Argon2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a report of migration status
  python migrate_passwords.py --report

  # Show SQL commands for password reset setup
  python migrate_passwords.py --sql
        """
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate migration status report'
    )
    parser.add_argument(
        '--sql',
        action='store_true',
        help='Show SQL commands for setting up password reset requirement'
    )

    args = parser.parse_args()

    try:
        # Initialize database
        db = SQLiteStore()

        # Generate report
        report = generate_migration_report(db)

        if args.report or not (args.sql):
            print_migration_report(report)

        if args.sql:
            generate_sql_for_password_reset_flag(db)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
