from json import load, dumps
import os
import psycopg2
from psycopg2.extras import RealDictCursor

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
    
    def load_week(self, week: str) -> dict[str, str] | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT data FROM meal_weeks WHERE week = %s", (week,))
            result = cur.fetchone()
            if result:
                return dict(result['data'])
            return None
