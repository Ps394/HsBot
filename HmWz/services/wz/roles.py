from __future__ import annotations
import asyncio
import logging

from ...types import Optional, Tuple, dataclass, Id, Ids, Guild
from ..base import Base
from ..database import Database

class WzRoles(Base):
    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)

    @dataclass(frozen=True)
    class TableCols:
        Guild: str = "Guild"
        Role: str = "Role"
        Permanent: str = "Permanent"
        Score: str = "Score"
        
    @property
    def table(self) -> str:
        """
        Gibt die SQL-Anweisung zurück, um die Tabelle für WZ-Registrierungsrollen zu erstellen.
        """
        return f"""
        CREATE TABLE IF NOT EXISTS {self.table_name}(
        {self.TableCols.Guild} INTEGER,
        {self.TableCols.Role} INTEGER,
        {self.TableCols.Permanent} BOOLEAN,
        {self.TableCols.Score} INTEGER DEFAULT 1,
        PRIMARY KEY ({self.TableCols.Guild}, {self.TableCols.Role})
        )WITHOUT ROWID
        """

    @dataclass(frozen=True)
    class Data:
        guild: Guild
        role: Id
        permanent: bool
        score: int
    
    type Record = Optional[Data]
    """
    Repräsentiert eine WZ-Registrierungsrolle in einem Guild, einschließlich der Rolle selbst, ob sie permanent ist und welche Punktzahl sie hat.

    :param guild: Das Guild-Objekt, zu dem die Rolle gehört.
    :type guild: discord.Guild
    :param role: Die ID der Discord-Rolle, die die Rolle repräsentiert.
    :type role: int
    :param permanent: Gibt an, ob die Rolle permanent ist.
    :type permanent: bool
    :param score: Die Punktzahl der Rolle.
    :type score: int
    """
    
    type Records = Optional[Tuple[Data, ...]]
    """Repräsentiert eine Sammlung von WZ-Registrierungsrollen, die in einem Guild registriert sind. Kann None sein, wenn keine Rollen gefunden wurden."""

    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)

    async def count(self, *, guild: Guild, permanent: Optional[bool] = None, roles: Optional[Ids] = None) -> int:
        """
        Zählt die Anzahl der WZ-Registrierungsrollen in einem Guild, optional gefiltert nach Permanenz oder einer Liste von Rollen-IDs.
        
        :param guild: Das Guild-Objekt, für das die Rollen gezählt werden sollen.
        :type guild: Guild
        :param permanent: Optionaler Filter, um nur permanente oder nicht-permanente Rollen zu zählen.
        :type permanent: Optional[bool]
        :param roles: Optionale Liste von Rollen-IDs, um nur bestimmte Rollen zu zählen.
        :type roles: Optional[Ids]
        :return: Die Anzahl der WZ-Registrierungsrollen, die den angegebenen Kriterien entsprechen.
        :rtype: int
        :raises ValueError: Wenn sowohl permanent als auch roles Filter gleichzeitig angegeben werden.
        """
        try:
            if permanent is not None and roles:
                raise ValueError("Cannot provide both permanent and roles filters.")
            
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {self.TableCols.Guild} = ?"
            params = [guild.id]

            if permanent is not None:
                query += f" AND {self.TableCols.Permanent} = ?"
                params.append(int(permanent))
            elif roles:
                placeholders = ','.join('?' for _ in roles)
                query += f" AND {self.TableCols.Role} IN ({placeholders})"
                params.extend(roles)

            row = await self.database.fetch_one(query, tuple(params))
            self.logger.debug(f"{self.log_prefix(guild)} WZ registration roles counted.")
            return row[0] if row else 0
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to count WZ registration roles: {e}")
            return 0
        
    async def get(self, *, guild: Guild, permanent: Optional[bool] = None) -> Records:
        """
        Holt alle WZ-Registrierungsrollen für ein Guild, optional gefiltert nach Permanenz. 
        Bereinigt automatisch verwaiste Rollen, die nicht mehr existieren.
        
        :param guild: Das Guild-Objekt, für das die Rollen abgerufen werden sollen.
        :type guild: Guild
        :param permanent: Optionaler Filter, um nur permanente oder nicht-permanente Rollen abzurufen.
        :type permanent: Optional[bool]
        :return: Eine Sammlung von WZ-Registrierungsrollen oder None, wenn keine Rollen gefunden wurden.
        :rtype: Records
        """
        try:
            query = f"SELECT {self.TableCols.Role}, {self.TableCols.Permanent}, {self.TableCols.Score} FROM {self.table_name} WHERE {self.TableCols.Guild} = ?"
            params = [guild.id]

            if permanent is not None:
                query += f" AND {self.TableCols.Permanent} = ?"
                params.append(int(permanent))

            records = await self.database.fetch_all(query, tuple(params))
            if not records:
                return None

            async def resolve_records(rec):
                """
                Hilfsfunktion, um die Rolle für einen Datensatz aufzulösen und gleichzeitig Fehler zu protokollieren.
                """
                return self.Data(
                    guild=guild,
                    role=rec[self.TableCols.Role],
                    permanent=bool(rec[self.TableCols.Permanent]),
                    score=rec[self.TableCols.Score]
                )
            out = []
            out : WzRoles.Records = await asyncio.gather(*(resolve_records(rec) for rec in records))
            
            return out if out else None
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to get WZ registration roles: {e}")
            return None

    async def add(self, *, guild: Guild, role: Id, permanent: Optional[bool] = False, score: Optional[int] = 1) -> bool:
        """
        Fügt eine neue WZ-Registrierungsrolle zu einem Guild hinzu oder aktualisiert sie, wenn sie bereits existiert.
        
        :param guild: Das Guild-Objekt, zu dem die Rolle hinzugefügt werden soll.
        :type guild: Guild
        :param role: Die ID der Rolle, die als WZ-Registrierungsrolle hinzu
        gefügt werden soll.
        :type role: int
        :param permanent: Gibt an, ob die Rolle dauerhaft sein soll.
        :type permanent: Optional[bool]
        :param score: Der Score-Wert der Rolle.
        :type score: Optional[int]
        :return: True, wenn die Rolle erfolgreich hinzugefügt oder aktualisiert wurde, False bei einem Fehler.
        :rtype: bool
        """
        try:
            await self.database.execute(
                f"INSERT OR REPLACE INTO {self.table_name} (Guild, Role, Permanent, Score) VALUES (?, ?, ?, ?)",
                (guild.id, role, int(permanent), score)
            )
            self.logger.info(f"{self.log_prefix(guild)} Added WZ registration role {role}.")
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to add WZ registration role {role}: {e}")
            return False

    async def remove(self, *, guild: Guild, role: Optional[Id] = None, roles: Optional[Ids] = None) -> bool:
        """
        Entfernt eine oder mehrere WZ-Registrierungsrollen aus einem Guild.

        :param guild: Das Guild-Objekt, aus dem die Rolle(n) entfernt werden sollen.
        :type guild: Guild
        :param role: Die ID der Rolle, die entfernt werden soll.
        :type role: Optional[Id]
        :param roles: Eine Sequenz von Rollen-IDs, die entfernt werden sollen.
        :type roles: Optional[Ids]
        :return: True, wenn die Rolle(n) erfolgreich entfernt wurden, False bei einem Fehler.
        :rtype: bool
        """
        try:
            if role and roles:
                raise ValueError("Cannot provide both role and roles filters.")
            query = f"DELETE FROM {self.table_name} WHERE Guild = ?"
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
            self.logger.info(f"{self.log_prefix(guild)} Removed WZ registration role {target}.")
            return True
        except Exception as e:
            self.logger.exception(f"{self.log_prefix(guild)} Failed to remove WZ registration role {target}: {e}")
            return False
        
        