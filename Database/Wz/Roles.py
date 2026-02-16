from __future__ import annotations
import asyncio
from dataclasses import dataclass
from discord import Guild, Role, NotFound, Forbidden, HTTPException
from Logger import logger
from ..Database import Database
from typing import Optional, Sequence, Tuple, Union
from .Utils import fetch_role, NotFound, Forbidden, HTTPException

__all__ = [
    "Roles"
]

class Roles():
    CLASSNAME = "WzRoles"

    TABLE = f"""
    CREATE TABLE IF NOT EXISTS {CLASSNAME}(
    Guild INTEGER,
    Role INTEGER,
    Permanent BOOLEAN,
    Score INTEGER DEFAULT 1,
    PRIMARY KEY (Guild, Role)
    )WITHOUT ROWID
    """

    @dataclass(frozen=True)
    class Record:
        guild: Guild
        role: Optional[Role]
        permanent: bool
        score: int

    def __init__(self, database: Database):
        self.database = database

    async def count(self, *, guild: Guild, permanent: Optional[bool] = None, roles: Optional[Sequence[int]] = None) -> int:
        try:
            if permanent is not None and roles:
                raise ValueError("Cannot provide both permanent and roles filters.")
            
            query = f"SELECT COUNT(*) FROM {self.CLASSNAME} WHERE Guild = ?"
            params = [guild.id]

            if permanent is not None:
                query += " AND Permanent = ?"
                params.append(int(permanent))
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)

            row = await self.database.fetch_one(query, tuple(params))
            logger.debug(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - WZ registration roles counted.")
            return row[0] if row else 0
        except Exception as e:
            logger.exception(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to count WZ registration roles: {e}")
            return 0
        
    async def get(self, *, guild: Guild, permanent: Optional[bool] = None) -> Union[tuple[Record], None]:
        try:
            query = f"SELECT Role, Permanent, Score FROM {self.CLASSNAME} WHERE Guild = ?"
            params = [guild.id]

            if permanent is not None:
                query += " AND Permanent = ?"
                params.append(int(permanent))

            records = await self.database.fetch_all(query, tuple(params))
            if not records:
                return None

            async def resolve_records(rec):
                r = await fetch_role(guild=guild, role_id=rec["Role"])
                return rec, r
            
            resolved_records = await asyncio.gather(*(resolve_records(rec) for rec in records))

            valid_records = []
            stale_roles = []

            for record, record_role in resolved_records:
                if isinstance(record_role, Role):
                    valid_records.append(self.Record(
                        guild=guild, 
                        role=record_role, 
                        permanent=bool(record["Permanent"]), 
                        score=record["Score"]))
                if isinstance(record_role, NotFound):
                    logger.debug(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - WZ registration role {record['Role']} not found, marking for removal.")
                    stale_roles.append(record["Role"])
                elif isinstance(record_role, (Forbidden, HTTPException)):
                    logger.debug(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to fetch WZ registration role {record['Role']}: {record_role}")
  
            cleanup_tasks = []
            if stale_roles:
                cleanup_tasks.append(self.remove(guild=guild, roles=stale_roles))
                try:
                    from .Registrations import Registrations
                    registrations_service = Registrations(self.database)
                    cleanup_tasks.append(registrations_service.remove(guild=guild, roles=stale_roles))
                except Exception as e:
                    logger.exception(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to cascade removal of stale registrations: {e}")

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)
                
            return tuple(valid_records) if valid_records else None
        except Exception as e:
            logger.exception(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to get WZ registration roles: {e}")
            return None

    async def add(self, *, guild: Guild, role: int, permanent: Optional[bool] = False, score: Optional[int] = 1) -> bool:
        try:
            await self.database.execute(
                f"INSERT OR REPLACE INTO {self.CLASSNAME} (Guild, Role, Permanent, Score) VALUES (?, ?, ?, ?)",
                (guild.id, role, int(permanent), score)
            )
            logger.debug(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Added WZ registration role {role}.")
            return True
        except Exception as e:
            logger.exception(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to add WZ registration role {role}: {e}")
            return False

    async def remove(self, *, guild: Guild, role: Optional[int] = None, roles: Optional[Sequence[int]] = None) -> bool:
        try:
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
            params = [guild.id]
            if role:
                query += " AND Role = ?"
                params.append(role)
                target = f"role {role}"
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)
                target = f"roles {roles}"
            else:
                target = "all roles"
            await self.database.execute(query, tuple(params))
            logger.debug(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Removed WZ registration role {target}.")
            return True
        except Exception as e:
            logger.exception(f"{self.CLASSNAME} - {guild.name} ({guild.id}) - Failed to remove WZ registration role {target}: {e}")
            return False
        
        