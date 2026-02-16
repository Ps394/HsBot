from dataclasses import dataclass
from Logger import logger
from discord import Guild
from typing import Optional
from .Utils import NotFound, Forbidden, HTTPException
from ..Database import Database

__all__ = [
    "Config"
]

class Config():
    CLASSNAME = "WzConfig"

    TABLE = f"""
    CREATE TABLE IF NOT EXISTS {CLASSNAME} (
        Guild INTEGER PRIMARY KEY,
        ChannelID INTEGER,
        ScoreModLvl BOOLEAN DEFAULT 0,
        Matchmaker BOOLEAN DEFAULT 0,
        FOREIGN KEY (Guild) REFERENCES Servers(Guild)
    ) WITHOUT ROWID"""

    @dataclass(frozen=True)
    class Record:
        guild: Guild
        channel_id: Optional[int]
        score_mod_lvl: bool
        matchmaker: bool

    def __init__(self, database: Database):
        self.database = database

    async def get(self, *, guild: Guild) -> Optional[Record]:
        try:
            query = f"SELECT ChannelID, ScoreModLvl, Matchmaker FROM {self.CLASSNAME} WHERE Guild = ?"
            row = await self.database.fetch_one(query, (guild.id,))
            
            if not row:
                return None
            
            logger.info(f"{guild.name} ({guild.id}) - WZ config retrieved.")
            return self.Record(
                guild=guild,
                channel_id=row["ChannelID"],
                score_mod_lvl=bool(row["ScoreModLvl"]),
                matchmaker=bool(row["Matchmaker"])
            )
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to get WZ config: {e}")
            return None

    async def upsert(self, *, guild: Guild, channel_id: Optional[int] = None, score_mod_lvl: Optional[bool] = None, matchmaker: Optional[bool] = None) -> bool:
        try:
            cols = []
            vals = []
            
            if channel_id is not None:
                cols.append("ChannelID")
                vals.append(channel_id)
            if score_mod_lvl is not None:
                cols.append("ScoreModLvl")
                vals.append(int(score_mod_lvl))
            if matchmaker is not None:
                cols.append("Matchmaker")
                vals.append(int(matchmaker))

            if not cols:
                return False

            columns = "Guild, " + ", ".join(cols)
            placeholders = ", ".join(["?"] * (1 + len(cols)))
            update_clause = ", ".join([f"{c}=excluded.{c}" for c in cols])
            
            query = f"""
                INSERT INTO {self.CLASSNAME} ({columns}) 
                VALUES ({placeholders}) 
                ON CONFLICT(Guild) DO UPDATE SET {update_clause}
            """
            params = [guild.id] + vals
            
            await self.database.execute(query, tuple(params))
            logger.info(f"{guild.name} ({guild.id}) - WZ config upserted.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to upsert WZ config: {e}")
            return False

    async def remove(self, *, guild: Guild) -> bool:
        try:
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
            await self.database.execute(query, (guild.id,))
            logger.info(f"{guild.name} ({guild.id}) - WZ config removed.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to remove WZ config: {e}")
            return False