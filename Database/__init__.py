from Logger import logger
from . import Database, Servers, Wz
from discord import Guild

__all__ = [
    "Database",
    "Servers",
    "Wz",
]

class Services:
    def __init__(self, *, folder: str = "data", filename: str = "data.db") -> None:
        self.database = Database.Database(folder=folder, filename=filename)
        self.servers = Servers.Servers(self.database)
        self.wz = Wz.Wz(self.database)

    async def remove_guild_data(self, *, guild: Guild) -> bool:
        try:
            await self.servers.remove(guild=guild)
            await self.wz.remove_guild_data(guild=guild)
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to remove guild data: {e}")
            return False

    async def setup(self) -> None:
        queries = []
        queries.append(self.servers.TABLE)
        queries.extend(self.wz.tables)
        logger.info("Setting up database tables...") 
        for query in queries:
            try:
                await self.database.execute(query)
            except Exception as e:
                logger.exception(f"Failed to create table: {e}")
        logger.info("Database setup complete.")
        