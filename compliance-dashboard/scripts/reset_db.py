"""
Database reset script
Drops all tables and recreates the schema
WARNING: This will delete all data!
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create database connection from environment variables"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'compliance_db'),
        user=os.getenv('DB_USER', 'compliance_user'),
        password=os.getenv('DB_PASSWORD', 'compliance_pass')
    )


def reset_database():
    """Drop all tables and types, then recreate schema"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Dropping all tables and types...")

        # Drop all tables with CASCADE
        cursor.execute("""
            DROP TABLE IF EXISTS maintenance_events CASCADE;
            DROP TABLE IF EXISTS ncrs CASCADE;
            DROP TABLE IF EXISTS inspections CASCADE;
            DROP TABLE IF EXISTS processing_runs CASCADE;
            DROP TABLE IF EXISTS documents CASCADE;
        """)

        # Drop all custom types
        cursor.execute("""
            DROP TYPE IF EXISTS document_source CASCADE;
            DROP TYPE IF EXISTS processing_stage CASCADE;
            DROP TYPE IF EXISTS processing_status CASCADE;
            DROP TYPE IF EXISTS inspection_result CASCADE;
            DROP TYPE IF EXISTS ncr_status CASCADE;
            DROP TYPE IF EXISTS ncr_severity CASCADE;
        """)

        # Drop views
        cursor.execute("""
            DROP VIEW IF EXISTS overdue_ncrs CASCADE;
            DROP VIEW IF EXISTS recent_failures CASCADE;
        """)

        conn.commit()
        print("All tables, types, and views dropped successfully")

        # Now run the schema file
        schema_file = Path(__file__).parent / 'schema.sql'

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        print(f"\nReading schema from: {schema_file}")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        print("Recreating schema...")
        cursor.execute(schema_sql)
        conn.commit()

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\nRecreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        print("\nDatabase reset completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error resetting database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Main reset function with confirmation"""
    print("=" * 60)
    print("WARNING: Database Reset")
    print("=" * 60)
    print("This will DELETE ALL DATA in the database!")
    print("=" * 60)

    response = input("\nAre you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Reset cancelled")
        sys.exit(0)

    try:
        reset_database()
    except Exception as e:
        print(f"\nReset failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
