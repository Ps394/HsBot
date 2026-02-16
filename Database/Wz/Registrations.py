from __future__ import annotations
import datetime
import asyncio
from dataclasses import dataclass
from typing import Optional, Sequence, Union
from discord import Guild, Role, Member
from Database.Wz import Roles
from Logger import logger
from ..Database import Database
from .Utils import fetch_member, fetch_role, NotFound, Forbidden, HTTPException
__all__ = [
    "Registrations"
]

class Registrations():
    CLASSNAME = "WzRegistrations"

    TABLE = f"""
    CREATE TABLE IF NOT EXISTS {CLASSNAME}(
    Guild INTEGER,
    Member INTEGER,
    Role INTEGER,
    Timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (Guild, Member)
    )WITHOUT ROWID"""

    @dataclass(frozen=True)
    class Record:
        guild: Guild
        member: Union[Optional[Member], Exception]
        role: Union[Optional[Role], Exception]
        timestamp: str

    def __init__(self, database: Database):
        self.database = database

    async def fetch_member(self, *, guild: Guild, member_id: int) -> Optional[Member]:
        try:
            return await guild.fetch_member(member_id)
        except NotFound as e:
            logger.debug(f"{guild.name} ({guild.id}) - {member_id} fetched failure: Not found")
            return NotFound(f"WZ registration member {member_id} not found")
        except Forbidden as e:
            logger.debug(f"{guild.name} ({guild.id}) - {member_id} fetched failure: Forbidden")
            return Forbidden(f"Forbidden to access WZ registration member {member_id}")
        except HTTPException as e:
            logger.debug(f"{guild.name} ({guild.id}) - {member_id} fetched failure: {e}")
            return e
        
    async def fetch_role(self, *, guild: Guild, role_id: int) -> Optional[Role]:
        try:
            return await guild.fetch_role(role_id)
        except NotFound as e:
            logger.debug(f"{guild.name} ({guild.id}) - {role_id} fetched failure: Not found")
            return NotFound(f"WZ registration role {role_id} not found")
        except Forbidden as e:
            logger.debug(f"{guild.name} ({guild.id}) - {role_id} fetched failure: Forbidden")
            return Forbidden(f"Forbidden to access WZ registration role {role_id}")
        except HTTPException as e:
            logger.debug(f"{guild.name} ({guild.id}) - {role_id} fetched failure: {e}")
            return e

    async def count(self, *, guild: Guild, role: Optional[int]=None, roles: Optional[Sequence[int]]=None) -> int:
        try:
            if roles:
                roles = tuple(roles)
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
          
            query = f"SELECT COUNT(*) FROM {self.CLASSNAME} WHERE Guild = ?"
            params = [guild.id]
            if role:
                query += " AND Role = ?"
                params.append(role)
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND Role IN ({placeholders})"
                params.extend(roles)
            
            row = await self.database.fetch_one(query, params)
            logger.debug(f"{guild.name} ({guild.id}) - WZ registrations counted: {row[0] if row else 0} with filters role={role}, roles={roles}")
            return row[0] if row else 0
        except Exception as e:
            logger.exception(f"Failed to count WZ registrations for guild {guild.id}: {e}")
            return 0

    async def get(self, *, guild: Guild, member: Optional[int]=None, role: Optional[int]=None, roles: Optional[Sequence[int]]=None) -> Union[tuple[Record, ...], Record, None]:
        try:
            roles = tuple(roles) if roles else None

            if member and (role or roles):
                raise ValueError("Cannot combine member with role or roles filters.")
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
            
            query = f"SELECT * FROM {self.CLASSNAME} WHERE Guild = ?"
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
                if isinstance(record_member, Member) and isinstance(record_role, Role):
                    valid_records.append(self.Record(
                        guild=guild,
                        member=record_member,
                        role=record_role,
                        timestamp=record["Timestamp"]
                    ))

                if isinstance(record_member, NotFound):
                    logger.debug(f"{guild.name} ({guild.id}) - WZ registration member {record['Member']} not found, marking for removal.")
                    stale_members.append(record["Member"])
                    continue
                elif isinstance(record_member, Forbidden) or isinstance(record_member, HTTPException):
                    logger.debug(f"{guild.name} ({guild.id}) - Failed to fetch WZ registration member {record['Member']}: {record_member}")
                    continue
                if isinstance(record_role, NotFound):
                    logger.debug(f"{guild.name} ({guild.id}) - WZ registration role {record['Role']} not found, marking for removal.")
                    stale_roles.append(record["Role"])
                elif isinstance(record_role, (Forbidden, HTTPException)):
                    logger.debug(f"{guild.name} ({guild.id}) - Failed to fetch WZ registration role {record['Role']}: {record_role}")

            cleanup_tasks = []
            if stale_members:
                cleanup_tasks.append(self.remove(guild=guild, members=stale_members))

            if stale_roles:
                from .Roles import Roles
                roles_service = Roles(self.database)
                cleanup_tasks.append(roles_service.remove(guild=guild, roles=stale_roles))
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks)
                
            if not valid_records:
                return None
            return valid_records[0] if member else tuple(valid_records)
        except Exception as e:
            logger.exception(f"Failed to get WZ registrations for guild {guild.id}: {e}")
            return None

    async def add(self, *, guild: Guild, member: int, role: int) -> bool:
        try:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            query = f"""INSERT OR REPLACE INTO {self.CLASSNAME} (Guild, Member, Role, Timestamp) VALUES (?, ?, ?, ?)"""
            params = (guild.id, member, role, timestamp)
            await self.database.execute(query, params)
            return True    
        except Exception as e:
            logger.exception(f"Failed to add WZ registration for guild {guild.id}, member {member}: {e}")
            return False

    async def remove(self, *, guild: Guild, member: Optional[int]=None, role: Optional[int]=None, roles: Optional[Sequence[int]]=None, members: Optional[Sequence[int]]=None) -> bool:
        try:
            args = [member, role, roles, members]
            if sum(arg is not None for arg in args) > 1:
                raise ValueError("Cannot combine multiple filters. Provide only one of member, role, roles, or members.")

            roles = tuple(roles) if roles else None
            members = tuple(members) if members else None
            query = f"DELETE FROM {self.CLASSNAME} WHERE Guild = ?"
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
            logger.exception(f"Failed to remove WZ registrations for guild {guild.id}: {e}")
            return False
