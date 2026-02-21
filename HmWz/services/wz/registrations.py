from __future__ import annotations
import datetime
import asyncio
from dataclasses import dataclass
from typing import Optional, Union, Tuple
from discord import Guild

from ...utils import fetch_member, fetch_role, DiscordMember, DiscordRole, Ids, Id
from ..database import Database
from ..base import Base
from .roles import WzRoles

class WzRegistrations(Base):
    """
    Die WzRegistrations-Klasse verwaltet die Registrierungsinformationen für die WZ-Funktionalität eines Discord-Servers (Guild). 
    Sie ermöglicht das Hinzufügen, Abrufen und Entfernen von Registrierungen, die aus einem Mitglied und einer zugehörigen Rolle bestehen. 
    """
    def __init__(self, database: Database):
        super().__init__(database)
        self.roles_service = WzRoles(database)

    @property
    def table(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.table_name}(
            Guild INTEGER,
            Member INTEGER,
            Role INTEGER,
            Timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (Guild, Member)
        )WITHOUT ROWID
        """

    @dataclass(frozen=True)
    class Data:
        guild: Guild
        member: DiscordMember
        role: DiscordRole
        timestamp: str

    type Record = Optional[Data]
    """
    Basisdatentyp für eine Wz-Registrierung, bestehend aus einem Guild, einem Member, einer Role und einem Timestamp.
    
    :param guild: Das Guild-Objekt, für das die Registrierung gilt.
    :type guild: discord.Guild
    :param member: Das DiscordMember-Objekt, das das registrierte Mitglied repräsentiert.
    :type member: DiscordMember
    :param role: Das DiscordRole-Objekt, das die mit der Registrierung verknüpften Rolle repräsentiert.
    :type role: DiscordRole
    :param timestamp: Der Zeitstempel der Registrierung.
    :type timestamp: str
    """
    type Records = Union[Optional[Tuple[Data, ...]], Record]
    """
    Der Datentyp für die WZ-Registrierungsinformationen einer Guild. Er kann entweder ein einzelner Record oder ein Tuple von Records sein, oder None, wenn keine Registrierungen vorhanden sind.
    """

    def __init__(self, database: Database):
        self.database = database
        self.roles_service = WzRoles(database)

    async def count(self, *, guild: Guild, role: Optional[Id]=None, roles: Optional[Ids]=None) -> int:
        """
        Zählt die Anzahl der WZ-Registrierungen in einem Guild, optional gefiltert nach einer bestimmten Rolle oder einer Liste von Rollen.

        :param guild: Das Guild-Objekt, für das die Anzahl der Registrierungen gezählt werden soll.
        :type guild: discord.Guild
        :param role: Optionaler Filter, um nur Registrierungen mit einer bestimmten Rolle zu zählen.
        :type role: Optional[int]
        :param roles: Optionaler Filter, um nur Registrierungen mit bestimmten Rollen zu zählen.
        :type roles: Optional[tuple[int, ...]]
        :return: Die Anzahl der WZ-Registrierungen, die den angegebenen Filtern entsprechen.
        :rtype: int
        :raises ValueError: Wenn sowohl role als auch roles Filter gleichzeitig angegeben werden.
        """
        try:
            if roles:
                roles = tuple(roles)
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
          
            query = f"""
            SELECT 
                COUNT(*) 
            FROM 
                {self.table_name} 
            WHERE 
                Guild = ?
            """

            params = [guild.id]
            if role:
                query += " AND Role = ?"
                params.append(role)
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)
            
            row = await self.database.fetch_one(query, params)
            self.logger.debug(f"{self.log_prefix(guild)} Counted WZ registrations with filters role={role}, roles={roles}: {row[0] if row else 0}")
            return row[0] if row else 0
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to count WZ registrations: {e}")
            return 0

    async def get(self, *, guild: Guild, member: Optional[Id]=None, role: Optional[Id]=None, roles: Optional[Ids]=None) -> Records:
        """
        Ruht die WZ-Registrierungsinformationen für eine bestimmte Gilde ab, optional gefiltert nach Mitglied oder Rolle(n).
        Stale Einträge (d.h. solche, deren Mitglied oder Rolle nicht mehr existiert) werden automatisch bereinigt.

        :param guild: Das Guild-Objekt, für das die Informationen abgerufen werden sollen.
        :type guild: discord.Guild
        :param member: Optionaler Filter, um die Registrierung eines bestimmten Mitglieds abzurufen
        :type member: Optional[int]
        :param role: Optionaler Filter, um Registrierungen mit einer bestimmten Rolle abzurufen
        :type role: Optional[int]
        :param roles: Optionaler Filter, um Registrierungen mit bestimmten Rollen abzurufen
        :type roles: Optional[tuple[int, ...]]  
        :return: Die WZ-Registrierungsinformationen, die den angegebenen Filtern entsprechen.
        :rtype: Records
        :raises ValueError: Wenn sowohl member als auch role/roles Filter gleichzeitig angegeben werden.
        """
        try:
            roles = tuple(roles) if roles else None

            if member and (role or roles):
                raise ValueError("Cannot combine member with role or roles filters.")
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
            
            query = f"SELECT * FROM {self.table_name} WHERE Guild = ?"
            params = [guild.id]
            if member:
                query += " AND Member = ?"
                params.append(member)
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)
            elif role:
                query += " AND Role = ?"
                params.append(role)

            records = await self.database.fetch_all(query, tuple(params))
            if not records:
                return None
            
            async def resolve_records(rec):
                m = await fetch_member(guild=guild, member_id=rec["Member"])
                r = await fetch_role(guild=guild, role_id=rec["Role"])
                return rec, m, r

            resolved_records = await asyncio.gather(*(resolve_records(rec) for rec in records))

            valid_records = []
            stale_members = []
            stale_roles = []

            for record, record_member, record_role in resolved_records:
                if isinstance(record_member, int) or isinstance(record_role, int):
                    stale_members.append(record["Member"])
                    stale_roles.append(record["Role"]) if isinstance(record_role, int) else None
                    self.logger.info(f"{self.log_prefix(guild)} WZ registration for member {record['Member']} with role {record['Role']} is stale and will be removed.")
                    continue
                else:
                    valid_records.append(self.Data(
                        guild=guild,
                        member=record_member,
                        role=record_role,
                        timestamp=record["Timestamp"]
                    ))

            cleanup_tasks = []
            if stale_members:
                cleanup_tasks.append(self.remove(guild=guild, members=stale_members))
            if stale_roles:
                cleanup_tasks.append(self.roles_service.remove(guild=guild, roles=stale_roles))
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)
                
            if not valid_records:
                return None
            return valid_records[0] if member else tuple(valid_records)
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to get WZ registrations: {e}")
            return None

    async def add(self, *, guild: Guild, member: Id, role: Id) -> bool:
        """
        Fügt eine neue WZ-Registrierung für ein Mitglied mit einer zugehörigen Rolle hinzu oder aktualisiert sie.

        :param guild: Das Guild-Objekt, für das die Registrierung hinzugefügt werden soll.
        :type guild: discord.Guild
        :param member: Die ID des Mitglieds, das registriert werden soll.
        :type member: int
        :param role: Die ID der Rolle, die mit der Registrierung verknüpft werden soll.
        :type role: int
        :return: True, wenn die Registrierung erfolgreich hinzugefügt oder aktualisiert wurde, False sonst.
        :rtype: bool
        """
        try:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            query = f"""INSERT OR REPLACE INTO {self.table_name} (Guild, Member, Role, Timestamp) VALUES (?, ?, ?, ?)"""
            params = (guild.id, member, role, timestamp)
            await self.database.execute(query, params)
            return True    
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to add WZ registration for member {member}: {e}")
            return False

    async def remove(self, *, guild: Guild, member: Optional[Id]=None, role: Optional[Id]=None, roles: Optional[Ids]=None, members: Optional[Ids]=None) -> bool:
        """
        Entfernt WZ-Registrierungen basierend auf den angegebenen Filtern.

        :param guild: Das Guild-Objekt, für das die Registrierung entfernt werden soll.
        :type guild: discord.Guild
        :param member: Die ID des Mitglieds, dessen Registrierung entfernt werden soll.
        :type member: int
        :param role: Die ID der Rolle, deren Registrierung entfernt werden soll.
        :type role: int
        :param roles: Eine Liste von Rollen-IDs, deren Registrierungen entfernt werden sollen.
        :type roles: list[int]
        :param members: Eine Liste von Mitglieder-IDs, deren Registrierungen entfernt werden sollen.
        :type members: list[int]
        :return: True, wenn die Registrierung erfolgreich entfernt wurde, False sonst.
        :rtype: bool
        :raises ValueError: Wenn ungültige Kombinationen von Filtern bereitgestellt werden (z.B. sowohl member als auch members).
        """
        try:
            args = [member, role, roles, members]
            if sum(arg is not None for arg in args) > 1:
                raise ValueError("Cannot combine multiple filters. Provide only one of member, role, roles, or members.")

            roles = tuple(roles) if roles else None
            members = tuple(members) if members else None
            query = f"DELETE FROM {self.table_name} WHERE Guild = ?"
            params = [guild.id]

            if member:
                query += " AND Member = ?"
                params.append(member)
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)
            elif role:
                query += " AND Role = ?"
                params.append(role)
            elif members:
                placeholders = ','.join('?' for _ in members)
                query += f" AND Member IN ({placeholders})"
                params.extend(members)
            await self.database.execute(query, tuple(params))
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to remove WZ registrations: {e}")
            return False
