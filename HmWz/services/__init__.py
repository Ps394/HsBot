import logging
from discord import Guild
from .database import Database
from .servers import Servers
from .wz import Wz

class Services:
    def __init__(self, *, folder: str = "data", filename: str = "data.db") -> None:
        self.logger = logging.getLogger(__name__)
        self.database = Database(folder=folder, filename=filename)
        self.servers = Servers(self.database)
        self.wz = Wz(self.database)

    async def remove_guild_data(self, *, guild: Guild) -> bool:
        try:
            await self.servers.remove(guild=guild)
            await self.wz.remove_guild_data(guild=guild)
            return True
        except Exception as e:
            self.logger.exception(f"{guild.name} ({guild.id}) - Failed to remove guild data: {e}")
            return False

    async def setup(self) -> None:
        queries = []
        queries.append(self.servers.table)
        queries.extend(self.wz.tables)
        self.logger.info("Setting up database tables...") 
        for query in queries:
            try:
                await self.database.execute(query)
            except Exception as e:
                self.logger.exception(f"Failed to create table: {e}")
        self.logger.info("Database setup complete.")
        