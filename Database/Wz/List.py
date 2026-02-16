from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Optional, Sequence, Union
from discord import Guild, TextChannel, Message
from Logger import logger
from ..Database import Database
from .Utils import fetch_channel, fetch_message

__all__ = [
    "List"
]

class List():
    CLASSNAME = "WzList"

    TABLE = f"""
    CREATE TABLE IF NOT EXISTS {CLASSNAME} (
    Guild INTEGER,
    Channel INTEGER,
    Message INTEGER,
    Title TEXT,
    Text TEXT,
    FOREIGN KEY (Guild) REFERENCES Servers(Guild),
    PRIMARY KEY (Guild, Message)
    ) WITHOUT ROWID"""

    @dataclass(frozen=True)
    class Record:
        guild: Guild
        channel: Union[Optional[TextChannel], Exception]
        message: Union[Optional[Message], Exception]
        title: Optional[str]
        text: Optional[str]


    def __init__(self, database: Database):
        self.database = database

    async def count(self, *, guild: Guild) -> int:
        try:
            query = f"SELECT COUNT(*) FROM {self.CLASSNAME} WHERE Guild = ?"
            row = await self.database.fetch_one(query, params=(guild.id))
            return row[0] if row else 0
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to get WZ lists: {e}")
            return 0
        
    async def get(self, *, guild: Guild) -> Optional[tuple[Record, ...]]:
        try:
            query = f"SELECT Channel, Message, Title, Text FROM {self.CLASSNAME} WHERE Guild = ?"
            params = (guild.id,)
            records = await self.database.fetch_all(query, params)
            if not records:
                return None

            async def resolve_records(rec) -> tuple[dict, List.Record]:
                c = await fetch_channel(guild=guild, channel_id=rec["Channel"])
                m = await fetch_message(channel=c, message_id=rec["Message"]) if isinstance(c, TextChannel) else c
                return rec, self.Record(
                    guild=guild,
                    channel=c,
                    message=m,
                    title=rec["Title"],
                    text=rec["Text"]
                )
            
            resolved_records = await asyncio.gather(*(resolve_records(rec) for rec in records))
            
            valid_records = []
            stale_records = []

            for raw_record, record in resolved_records:
                if isinstance(record.channel, TextChannel) and isinstance(record.message, Message):
                    valid_records.append(record)
                else:
                    stale_records.append(raw_record["Message"])
                    logger.debug(f"{guild.name} ({guild.id}) - WZ list message {raw_record['Message']} in channel {raw_record['Channel']} is stale and will be removed.")
                
            cleanup_tasks = []
            if stale_records:
                cleanup_tasks.append(self.remove(guild=guild, messages=stale_records))

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)
                logger.debug(f"{guild.name} ({guild.id}) - Removed {len(stale_records)} stale WZ list message(s).")

            return tuple(valid_records) if valid_records else None
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to get WZ lists: {e}")
            return None

    async def add(self, *, guild: Guild, channel: int, message:int, title: str, text: str) -> bool:
        try:
            query = f"INSERT INTO {self.CLASSNAME} (Guild, Channel, Message, Title, Text) VALUES (?, ?, ?, ?, ?)"
            await self.database.execute(query, params=(guild.id, channel, message, title, text))
            logger.info(f"{guild.name} ({guild.id}) - Added WZ list entry.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to add WZ list: {e}")
            return False
        
    async def update(self, *, guild: Guild, message: int, title: str, text: str) -> bool:
        try:
            query = f"UPDATE {self.CLASSNAME} SET Title = ?, Text = ? WHERE Guild = ? AND Message = ?"
            await self.database.execute(query, params=(title, text, guild.id, message))
            logger.info(f"{guild.name} ({guild.id}) - Updated WZ list entry.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to update WZ list: {e}")
            return False
        
    async def remove(self, *, guild: Guild, message: Optional[int] = None, messages: Optional[Sequence[int]] = None) -> bool:
        try:
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
            params = [guild.id]
            if messages is not None:
                placeholders = ','.join('?' for _ in messages)
                query += f" AND Message IN ({placeholders})"
                params.extend(messages)
            elif message is not None:
                query += " AND Message = ?"
                params.append(message)
            await self.database.execute(query, tuple(params))
            logger.info(f"{guild.name} ({guild.id}) - Removed WZ list entry.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to remove WZ list: {e}")
            return False
