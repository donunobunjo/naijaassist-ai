from contextlib import contextmanager

import psycopg
from app.config import settings


@contextmanager
def get_connection():
    """Open a short-lived PostgreSQL connection.

    For a larger deployment, use psycopg_pool and tune pool sizes for the host/database limits.
    """
    conn = psycopg.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()
