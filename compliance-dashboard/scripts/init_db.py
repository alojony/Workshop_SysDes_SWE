"""
Database initialization script
Creates all tables and initial schema
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
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


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database='postgres',
            user=os.getenv('DB_USER', 'compliance_user'),
            password=os.getenv('DB_PASSWORD', 'compliance_pass')
        )
        conn.autocommit = True
        cursor = conn.cursor()

        db_name = os.getenv('DB_NAME', 'compliance_db')

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )

        if not cursor.fetchone():
            print(f"Creating database: {db_name}")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"Database {db_name} created successfully")
        else:
            print(f"Database {db_name} already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")
        raise


def run_schema_file():
    """Execute the schema SQL file"""
    schema_file = Path(__file__).parent / 'schema.sql'

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    print(f"Reading schema from: {schema_file}")
    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Executing schema...")
        cursor.execute(schema_sql)
        conn.commit()
        print("Schema created successfully!")

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

    except Exception as e:
        conn.rollback()
        print(f"Error executing schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Main initialization function"""
    print("=" * 60)
    print("Compliance Dashboard - Database Initialization")
    print("=" * 60)

    try:
        # Step 1: Create database if needed
        create_database_if_not_exists()

        # Step 2: Run schema file
        run_schema_file()

        print("\n" + "=" * 60)
        print("Database initialization completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nInitialization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
