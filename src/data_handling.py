from json import dumps
import random
import psycopg2
from psycopg2.extras import RealDictCursor

# Data handling classes for meal planning and pantry directory

# MealDB handles the storage and retrieval of meal plans for different weeks
class MealDB:
    def __init__(self, host: str, database: str, username: str, password: str, port: int = 5432):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=username,
            password=password,
            port=port
        )
        self.__init_table()
    
    def __init_table(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS meal_weeks (
                    week VARCHAR(10) PRIMARY KEY,
                    data JSONB NOT NULL
                )
            """)
            self.conn.commit()
    
    def save_week(self, week: str, data: dict[str, str]) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO meal_weeks (week, data) VALUES (%s, %s)
                ON CONFLICT (week) DO UPDATE SET data = meal_weeks.data || EXCLUDED.data
            """, (week, dumps(data)))
            self.conn.commit()
    
    def load_week(self, week: str) -> dict[str, map] | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT data FROM meal_weeks WHERE week = %s", (week,))
            result = cur.fetchone()
            if result:
                return dict(result['data'])
            return None

# PantryDirectoryDB handles the storage and retrieval of pantry items
class PantryDirectoryDB:
    def __init__(self, host: str, database: str, username: str, password: str, port: int = 5432):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=username,
            password=password,
            port=port
        )
        self.__init_table()
    
    def __init_table(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pantry_directory (
                    id BIGINT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(255) NOT NULL
                )
            """)
            self.conn.commit()

    # Add a new item to the pantry directory with a unique ID
    def add_item(self, name: str, category: str) -> None:
        with self.conn.cursor() as cur:
            while True:
                item_id = random.randint(1000000000, 9999999999)
                try:
                    cur.execute("INSERT INTO pantry_directory (id, name, category) VALUES (%s, %s, %s)", (item_id, name, category))
                    self.conn.commit()
                    break
                except psycopg2.IntegrityError:
                    self.conn.rollback()
                    continue

    # Retrieve all items from the pantry directory, returning a list of dictionaries
    def get_all_items(self) -> list[dict[str, str]]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, category FROM pantry_directory ORDER BY id")
            return [dict(row) for row in cur.fetchall()]
    
    # Retrieve a single item by its ID, returning a dictionary or None if not found
    def get_item_by_id(self, item_id: int) -> dict[str, str] | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, category FROM pantry_directory WHERE id = %s", (item_id,))
            result = cur.fetchone()
            if result:
                return dict(result)
            return None
    
    def delete_item(self, item_id: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM pantry_directory WHERE id = %s", (item_id,))
            self.conn.commit()

# PantryDB handles the storage and retrieval of pantry items with expiration dates
class PantryDB:
    def __init__(self, host: str, database: str, username: str, password: str, port: int = 5432):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=username,
            password=password,
            port=port
        )
        self.__init_table()
    
    def __init_table(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pantry (
                    serial BIGINT PRIMARY KEY,
                    id BIGINT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    ingestion_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expiration_date DATE NOT NULL
                )
            """)
            self.conn.commit()
    
    # Add an item to the pantry using its ID from the pantry directory and an expiration date
    def add_item(self, pdpb: PantryDirectoryDB, item_id: int, expiration_date: str) -> int:
        with self.conn.cursor() as cur:
            item = pdpb.get_item_by_id(item_id)
            if not item:
                raise Exception("Item ID not found in pantry directory")
            while True:
                serial = random.randint(1000000000, 9999999999)
                try:
                    cur.execute("""
                        INSERT INTO pantry (serial, id, name, category, expiration_date) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (serial, item['id'], item['name'], item['category'], expiration_date))
                    self.conn.commit()
                    return serial
                except psycopg2.IntegrityError:
                    self.conn.rollback()
                    continue
    
    # Get the count of a specific item in the pantry by its ID
    def item_count(self, item_id: int) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pantry WHERE id = %s", (item_id,))
            return 0 if not (result := cur.fetchone()) else result[0]
    
    # Remove an item from the pantry by its unique serial number
    def remove_item(self, serial: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM pantry WHERE serial = %s", (serial,))
            self.conn.commit()
    
    # Retrieve all items from the pantry, returning a list of dictionaries
    def get_all_items(self) -> list[dict[str, str]]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT serial, id, name, category, expiration_date FROM pantry ORDER BY expiration_date")
            return [dict(row) for row in cur.fetchall()]
    
    # Retrieve a single item by its serial number
    def get_item_by_serial(self, serial: int) -> dict[str, str] | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT serial, id, name, category, expiration_date FROM pantry WHERE serial = %s", (serial,))
            result = cur.fetchone()
            if result:
                return dict(result)
            return None
    
    # Remove the oldest item by item ID (based on expiration date)
    def remove_oldest_by_id(self, item_id: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM pantry WHERE serial = (
                    SELECT serial FROM pantry WHERE id = %s ORDER BY expiration_date ASC LIMIT 1
                )
            """, (item_id,))
            self.conn.commit()
