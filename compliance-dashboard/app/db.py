"""
Database connection and session management
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
from app.settings import settings


class Database:
    """Database connection manager"""

    def __init__(self):
        self.connection_params = {
            'host': settings.db_host,
            'port': settings.db_port,
            'database': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password
        }

    def get_connection(self):
        """Get a new database connection"""
        return psycopg2.connect(**self.connection_params)

    @contextmanager
    def get_cursor(self, dict_cursor=True) -> Generator:
        """
        Context manager for database cursor
        Automatically commits on success, rolls back on error
        """
        conn = self.get_connection()
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)

        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for transactions
        Returns connection for manual cursor creation
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


# Global database instance
db = Database()


def get_db():
    """Dependency for FastAPI routes"""
    return db
