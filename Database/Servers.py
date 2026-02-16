from Logger import logger
from .Database import Database
from discord import Guild

__all__ = [
    "Servers"
]

class Servers():
    CLASSNAME = "Servers"

    TABLE = """
    CREATE TABLE IF NOT EXISTS Servers (
        Guild INTEGER PRIMARY KEY,
        Name TEXT
    ) WITHOUT ROWID"""

    def __init__(self, database: Database):
        self.database = database

    async def count(self) -> int:
        try:
            query = f"SELECT COUNT(*) FROM {self.CLASSNAME}"
            row = await self.database.fetch_one(query)
            logger.info("Counted servers in database.")
            return row[0] if row else 0
        except Exception as e:
            logger.exception(f"Failed to count servers: {e}")
            return 0

    async def add(self, *, guild: Guild) -> bool:
        try:
            query = f"""
                INSERT INTO {self.CLASSNAME} (Guild, Name) 
                VALUES (?, ?) 
                ON CONFLICT(Guild) DO UPDATE SET Name = excluded.Name
            """
            await self.database.execute(query, (guild.id, guild.name))
            logger.info(f"{guild.name} ({guild.id}) - Added/Updated server.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to add/update server: {e}")
            return False

    async def remove(self, *, guild: Guild) -> bool:
        try:
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
            await self.database.execute(query, (guild.id,))
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to remove server: {e}")
            return False