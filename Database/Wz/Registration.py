from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union
from discord import Guild, TextChannel, Message
from Logger import logger
from ..Database import Database
from .Utils import fetch_channel, fetch_message

__all__ = [
    "Registration"
]

class Registration():
    CLASSNAME = "WzRegistration"

    TABLE = f"""
    CREATE TABLE IF NOT EXISTS {CLASSNAME} (
    Guild INTEGER PRIMARY KEY,
    Channel INTEGER,
    Message INTEGER,
    Title TEXT,
    Description TEXT,
    Link TEXT,
    FOREIGN KEY (Guild) REFERENCES Servers(Guild)
    )WITHOUT ROWID;"""    

    @dataclass(frozen=True)
    class Record:
        guild: Guild
        channel: Union[Optional[TextChannel], Exception]
        message: Union[Optional[Message], Exception]
        title: Optional[str]
        description: Optional[str]
        link: Optional[str]

        @property
        def is_valid(self) -> bool:
            return isinstance(self.channel, TextChannel) and isinstance(self.message, Message)

    def __init__(self, database: Database):
        self.database = database

    async def get(self, *, guild: Guild) -> Optional[Record]:
        """
        Docstring for get
        
        :param self: Description
        :param guild: Description
        :type guild: Guild
        :return: Description
        :rtype: Record | None
        """
        try:
            query = f"SELECT Channel, Message, Title, Description, Link FROM {self.CLASSNAME} WHERE Guild = ?"
            params = (guild.id,)
            record = await self.database.fetch_one(query, params)
            
            if not record:
                return None

            channel = await fetch_channel(guild=guild, channel_id=record["Channel"])

            if isinstance(channel, TextChannel):
                message = await fetch_message(channel=channel, message_id=record["Message"])
            else:
                message = channel

            return self.Record(
                guild=guild,
                channel=channel,
                message=message,
                title=record["Title"],
                description=record["Description"],
                link=record["Link"]
            )
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to get WZ registration: {e}")
            return None
        
    async def setup_channel(self, *, guild: Guild, channel: int)->bool:
        try:
            query = f"""
            INSERT INTO {self.CLASSNAME} (Guild, Channel) VALUES (?, ?)
            ON CONFLICT(Guild) DO UPDATE SET Channel = excluded.Channel
            """
            await self.database.execute(query, (guild.id, channel))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration channel {channel}.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration channel: {e}")
            return False
    
    async def setup_link(self, *, guild: Guild, link: Optional[str] = "")->bool:
        try:
            # Validate URL scheme if link is provided
            if link:
                from urllib.parse import urlparse
                parsed = urlparse(link)
                if parsed.scheme not in ('http', 'https', 'discord'):
                    logger.warning(f"{guild.name} ({guild.id}) - Invalid URL scheme '{parsed.scheme}' for link. Must be http, https, or discord.")
                    return False
                if not parsed.netloc:
                    logger.warning(f"{guild.name} ({guild.id}) - Invalid URL '{link}' - missing domain.")
                    return False
            
            query = f"""
            INSERT INTO {self.CLASSNAME} (Guild, Link) VALUES (?, ?)
            ON CONFLICT(Guild) DO UPDATE SET Link = excluded.Link
            """
            await self.database.execute(query, (guild.id, link if link else None))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration link {link}.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration link: {e}")
            return False
        
    async def setup_message(self, *, guild: Guild, title: Optional[str] = None, description: Optional[str] = None)->bool:
        try:
            updates = []
            params = []

            if title is not None:
                updates.append("Title = ?")
                params.append(title[:255]) 
            if description is not None:
                updates.append("Description = ?")
                params.append(description[:4095])

            if not updates:
                logger.warning(f"{guild.name} ({guild.id}) - No title or description provided for WZ registration message setup.")
                return False

            query = f"UPDATE {self.CLASSNAME} SET {', '.join(updates)} WHERE Guild = ?"
            params.append(guild.id)

            await self.database.execute(query, tuple(params))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration message with title and description.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration message: {e}")
            return False

    async def setup_title(self, *, guild: Guild, title: Optional[str] = "")->bool:
        try:
            query = f"""
            INSERT INTO {self.CLASSNAME} (Guild, Title) VALUES (?, ?)
            ON CONFLICT(Guild) DO UPDATE SET Title = excluded.Title
            """
            await self.database.execute(query, (guild.id, title[:255]))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration title {title}.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration title: {e}")
            return False
        
    async def setup_description(self, *, guild: Guild, description: Optional[str] = "")->bool:
        try:
            query = f"""
            INSERT INTO {self.CLASSNAME} (Guild, Description) VALUES (?, ?)
            ON CONFLICT(Guild) DO UPDATE SET Description = excluded.Description
            """
            await self.database.execute(query, (guild.id, description[:4095]))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration description.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration description: {e}")
            return False

    async def setup_registration(self, *, guild: Guild, message: Optional[int], title: Optional[str] = None, description: Optional[str] = None, link: Optional[str] = None) -> bool:
        try:
            updates = ["Message = ?"]
            params = [message]

            if title:
                updates.append("Title = ?")
                params.append(title[:255]) 
            if description:
                updates.append("Description = ?")
                params.append(description[:4095])
            if link:
                updates.append("Link = ?")
                params.append(link)

            query = f"UPDATE {self.CLASSNAME} SET {', '.join(updates)} WHERE Guild = ?"
            params.append(guild.id)

            await self.database.execute(query, tuple(params))
            logger.debug(f"{guild.name} ({guild.id}) - Set up WZ registration for message {message}.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to setup WZ registration: {e}")
            return False
  
    async def remove(self, *, guild: Guild) -> bool:
        try:
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
            params = (guild.id,)
            await self.database.execute(query, params)
            logger.debug(f"{guild.name} ({guild.id}) - Removed WZ registration.")
            return True
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Failed to remove WZ registration: {e}")
            return False