from __future__ import annotations
import asyncio
from dataclasses import dataclass
import logging
from typing import Optional, Sequence, Union, List, Tuple
from discord import Guild, TextChannel, Message

from ...utils import fetch_channel, fetch_message, DiscordChannel, DiscordMessage, Id, Ids
from ..database import Database
from ..base import Base


class WzList(Base):
    """
    Die WzList-Klasse verwaltet die Wartelisteninformationen für die WZ-Funktionalität eines Discord-Servers (Guild).
    """
    def __init__(self, database: Database):
        super().__init__(database)
        self.logger = logging.getLogger(__name__)
        
    @property
    def table(self) -> str:
        """
        Gibt die SQL-Definition für die Tabelle zurück, die die WZ-Wartelisteninformationen speichert.
        
        :return: Ein SQL-String, der die Tabelle definiert.
        :rtype: str
        """
        return f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            Guild INTEGER,
            Channel INTEGER,
            Message INTEGER,
            Title TEXT,
            Text TEXT,
        FOREIGN KEY (Guild) REFERENCES Servers(Guild),
        PRIMARY KEY (Guild, Message)
        ) WITHOUT ROWID
        """

    @dataclass(frozen=True)
    class Data:
        guild: Guild
        channel: DiscordChannel
        message: DiscordMessage
        title: Optional[str]
        text: Optional[str]

    type Record = Optional[Data]
    """
    Der Datentyp für einen einzelnen WZ-Warteliste.
    
    :param guild: Das Guild-Objekt, für das die Warteliste gilt.
    :type guild: discord.Guild
    :param channel: Das DiscordChannel-Objekt, das den Kanal repräsentiert, in dem die Warteliste angezeigt wird.
    :type channel: DiscordChannel
    :param message: Das DiscordMessage-Objekt, das die Nachricht repräsentiert, die die Warteliste enthält.
    :type message: DiscordMessage
    :param title: Der Titel der Warteliste. Kann None sein, wenn kein Titel festgelegt ist.
    :type title: Optional[str]
    :param text: Der Text der Warteliste. Kann None sein, wenn kein Text festgelegt ist.
    :type text: Optional[str]
    """
    type Records = Optional[Tuple[Data, ...]]
    """
    Der Datentyp für eine Sammlung von WZ-Wartelisteninformationen. Es kann ein Tuple von Record-Objekten oder None sein, wenn keine Wartelisteninformationen vorhanden sind.
    """

    async def get(self, *, guild: Guild) -> Records:
        """
        Ruft die WZ-Wartelisteninformationen für eine bestimmte Gilde ab und überprüft, ob die zugehörigen Discord-Objekte (Kanäle und Nachrichten) noch gültig sind. 
        Stale Einträge werden automatisch bereinigt.
        
        :param guild: Das Guild-Objekt, für das die Informationen abgerufen werden sollen.
        :type guild: discord.Guild
        :return: Ein Tuple von WzList.Record-Objekten, die die gültigen WZ-Wartelisteninformationen enthalten, oder None, wenn keine gültigen Einträge vorhanden sind.
        :rtype: WzList.Records
        """
        try:
            query = f"""
            SELECT 
                Channel, 
                Message, 
                Title, 
                Text 
            FROM 
                {self.table_name} 
            WHERE 
                Guild = ?
            """
            params = (guild.id,)
            records = await self.database.fetch_all(query, params)
            if not records:
                return None

            async def resolve_records(rec) -> tuple[dict, WzList.Record]:
                """
                Hilfsfunktion, um die Channel- und Message-IDs in den Datenbankeinträgen aufzulösen.
                
                :param rec: Ein einzelner Datenbankeintrag mit Channel- und Message-IDs.
                :type rec: dict
                :return: Ein Tuple bestehend aus dem ursprünglichen Datenbankeintrag und einem WzList.Record mit den aufgelösten Discord-Objekten.
                :rtype: tuple[dict, WzList.Record]
                """
                c = await fetch_channel(guild=guild, channel_id=rec["Channel"])
                m = await fetch_message(channel=c, message_id=rec["Message"]) if isinstance(c, TextChannel) else c
                return rec, self.Data(
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
                    self.logger.debug(f"{self.log_prefix(guild)} WZ list message {raw_record['Message']} in channel {raw_record['Channel']} is stale and will be removed.")
                
            cleanup_tasks = []
            if stale_records:
                cleanup_tasks.append(self.remove(guild=guild, messages=stale_records))

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)
                self.logger.debug(f"{self.log_prefix(guild)} Removed {len(stale_records)} stale WZ list message(s).")

            return tuple(valid_records) if valid_records else None
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to get WZ lists: {e}")
            return None

    async def add(self, *, guild: Guild, channel: Id, message: Id, title: str, text: str) -> bool:
        """
        Fügt einen neuen Eintrag zur WZ-Warteliste für eine bestimmte Gilde hinzu.
        
        :param guild: Das Guild-Objekt, für das die Informationen gelten.
        :type guild: discord.Guild
        :param channel: Die ID des Kanals, in dem die WZ-Warteliste angezeigt wird.
        :type channel: int
        :param message: Die ID der Nachricht, die die WZ-Warteliste repräsentiert.
        :type message: int
        :param title: Der Titel der WZ-Warteliste.
        :type title: str
        :param text: Der Text der WZ-Warteliste.
        :type text: str
        :return: True, wenn der Eintrag erfolgreich hinzugefügt wurde, False sonst.
        :rtype: bool
        """
        try:
            query = f"INSERT INTO {self.table_name} (Guild, Channel, Message, Title, Text) VALUES (?, ?, ?, ?, ?)"
            await self.database.execute(query, params=(guild.id, channel, message, title, text))
            self.logger.info(f"{self.log_prefix(guild)} Added WZ list entry.")
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to add WZ list: {e}")
            return False
        
    async def update(self, *, guild: Guild, message: Id, title: str, text: str) -> bool:
        """
        Aktualisiert einen bestehenden Eintrag in der WZ-Warteliste für eine bestimmte Gilde.
        
        :param guild: Das Guild-Objekt, für das die Informationen gelten.
        :type guild: discord.Guild
        :param message: Die ID der Nachricht, die aktualisiert werden soll.
        :type message: int
        :param title: Der neue Titel der WZ-Warteliste.
        :type title: str
        :param text: Der neue Text der WZ-Warteliste.
        :type text: str
        :return: True, wenn der Eintrag erfolgreich aktualisiert wurde, False sonst.
        :rtype: bool
        """
        try:
            query = f"UPDATE {self.table_name} SET Title = ?, Text = ? WHERE Guild = ? AND Message = ?"
            await self.database.execute(query, params=(title, text, guild.id, message))
            self.logger.info(f"{self.log_prefix(guild)} Updated WZ list entry.")
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to update WZ list: {e}")
            return False
        
    async def remove(self, *, guild: Guild, message: Optional[Id] = None, messages: Optional[Ids] = None) -> bool:
        """
        Entfernt einen oder mehrere WZ-Listeneinträge für eine bestimmte Gilde.
        
        :param guild: Das Guild-Objekt, für das die Informationen gelten.
        :type guild: discord.Guild
        :param message: Die ID der Nachricht, die entfernt werden soll. Optional, wenn `messages` verwendet wird.
        :type message: Optional[Id]
        :param messages: Eine Sequenz von Nachrichten-IDs, die entfernt werden sollen. Optional, wenn `message` verwendet wird.
        :type messages: Optional[Ids]
        :return: True, wenn die Entfernung erfolgreich war, False sonst.
        :rtype: bool
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE Guild = ?"
            params = [guild.id]
            if messages is not None:
                placeholders = ','.join('?' for _ in messages)
                query += f" AND Message IN ({placeholders})"
                params.extend(messages)
            elif message is not None:
                query += " AND Message = ?"
                params.append(message)
            await self.database.execute(query, tuple(params))
            self.logger.info(f"{self.log_prefix(guild)} Removed WZ list entry.")
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to remove WZ list: {e}")
            return False
        
