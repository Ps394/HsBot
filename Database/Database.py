import os
import aiosqlite
from contextlib import asynccontextmanager
from Logger import logger

__all__ = [
    "Database",
]

class Database:
    def __init__(self,*, folder: str = "data", filename: str = "data.db") -> None:
        os.makedirs(folder, exist_ok=True)
        self.file = os.path.join(folder, filename)

    @asynccontextmanager
    async def connect(self):
        database = None
        try:
            database = await aiosqlite.connect(self.file)
            await database.execute("PRAGMA foreign_keys = ON;")
            await database.execute("PRAGMA journal_mode = WAL;")
            await database.execute("PRAGMA synchronous = NORMAL;")
            database.row_factory = aiosqlite.Row
            yield database
        except Exception as e:
            logger.exception(f"Database connection error: {e}")
            raise
        finally:
            if database:
                await database.close()

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        async with self.connect() as connection:
            await connection.execute(query, params)
            await connection.commit()
            
    async def fetch_all(self, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self.connect() as connection:
            async with connection.execute(query, params) as cursor:
                return await cursor.fetchall()
    
    async def fetch_one(self, query: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self.connect() as connection:
            async with connection.execute(query, params) as cursor:
                return await cursor.fetchone()

