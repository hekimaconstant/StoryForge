import sqlite3
import os
import psycopg2

# PATH ENFORCEMENT
DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(DATABASE_DIR, 'database.db')
SCHEMA = os.path.join(os.path.dirname(DATABASE_DIR), 'schema.sql')
DATABASE_URL = os.environ.get('DATABASE_URL')


#THE DUAL COMPATIBILITY (SQLITE & POSTGRES)
class HybridRow:
    """Acts like a tuple/list AND a dictionary simultaneously"""
    def __init__(self, row_tuple, column_names):
        self._tuple = row_tuple
        self._colnames = column_names
        
        # Map columns
        self._mapping = {name: index for index, name in enumerate(column_names)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._tuple[key]
        
        return self._tuple[self._mapping[key]]

    def get(self, key, default=None):
        """Allows safe dict-like .get() lookups"""
        if key in self._mapping:
            return self._tuple[self._mapping[key]]
        return default

    def keys(self):
        """Allows dictionary key list evaluations for Jinja templates"""
        return self._colnames

    def __iter__(self):
        """Allows standard loops across row contents"""
        return iter(self._tuple)


# Postgres Adapter to SQLITE
class PostgresCursorAdapter:
    """Wraps a psycopg2 cursor to supply HybridRow objects seamlessly"""
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor

        # Grab the column metadata
        self._colnames = [desc[0] for desc in pg_cursor.description] if pg_cursor.description else []

    def fetchone(self):
        row = self._cursor.fetchone()
        # Convert the standard row
        return HybridRow(row, self._colnames) if row is not None else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [HybridRow(r, self._colnames) for r in rows]

    def __iter__(self):
        """Allows loop iteration directly over the cursor"""
        for row in self._cursor:
            yield HybridRow(row, self._colnames)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnectionAdapter:
    """Wraps a psycopg2 connection to mimic sqlite3 connection behavior globally"""
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, parameters=None):
        """Intercepts .execute(), replaces SQLite placeholders, and runs it"""
        # Convert sqlite rows to postgres
        cursor = self._conn.cursor()
        
        #   PLACEHOLDER CONVERTER: ? to %s
        if isinstance(sql, str):
            sql = sql.replace('?', '%s')
            
        if parameters:
            cursor.execute(sql, parameters)
        else:
            cursor.execute(sql)
            
        return PostgresCursorAdapter(cursor)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


# --- DATABASE CONNECTION CORE ---
def get_db_connection():
    """Opens a connection to PostgreSQL in production, falling back to SQLite locally"""
    if DATABASE_URL:
        raw_connection = psycopg2.connect(DATABASE_URL)
        return PostgresConnectionAdapter(raw_connection)
    else:
        connection = sqlite3.connect(DATABASE)
        connection.row_factory = sqlite3.Row
        return connection


def init_db():
    """Creates the database tables based on schema.sql"""
    if DATABASE_URL:
        return True
    else:
        if not os.path.exists(DATABASE):
            os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
            connection = sqlite3.connect(DATABASE)
            
            try:
                if os.path.exists(SCHEMA):
                    with open(SCHEMA, mode='r', encoding='utf-8') as file:
                        connection.executescript(file.read())
                    connection.commit()
            except Exception:
                pass
            finally:
                connection.close()
