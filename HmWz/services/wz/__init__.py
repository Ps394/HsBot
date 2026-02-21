import logging
from discord import Guild
from typing import Tuple
from ..database import Database
from .config import WzConfig
from .roles import WzRoles
from .registration import WzRegistration
from .registrations import WzRegistrations
from .list import WzList

type ConfigRecord = WzConfig.Record
""" 
Der Datentyp für die WZ-Konfiguration eines Servers (Guild) in der Datenbank. Er enthält die folgenden Felder:

:param guild: Das Guild-Objekt, für das die Konfiguration gilt.
:type guild: discord.Guild
:param channel_id: [Deprecated] Die ID des Discord-Kanals, der für WZ verwendet wird. Kann None sein, wenn kein Kanal festgelegt ist.
:type channel_id: Optional[int]
:param score_mod_lvl: Ein boolescher Wert, der angibt, ob die Score-Mod-Level-Funktion aktiviert ist. Kann None sein, wenn der Wert nicht festgelegt ist.
:type score_mod_lvl: Optional[bool]
:param matchmaker: Ein boolescher Wert, der angibt, ob die Matchmaker-Funktion aktiviert ist. Kann None sein, wenn der Wert nicht festgelegt ist.
:type matchmaker: Optional[bool]
"""

type RegistrationRecord = WzRegistration.Record
"""
Der Datentyp für die Registrierungskanal- und -nachrichteninformationen einer Guild im WZ-Modul.

:param guild: Das Guild-Objekt, für das die Informationen gelten.
:type guild: discord.Guild
:param channel: Das DiscordChannel-Objekt, das den Registrierungskanal repräsentiert. Kann auch die Kanal-ID als int sein, wenn der Kanal nicht gefunden werden konnte.
:type channel: DiscordChannel
:param message: Das DiscordMessage-Objekt, das die Registrierungsmeldung repräsentiert. Kann auch die Nachrichten-ID als int sein, wenn die Nachricht nicht gefunden werden konnte.
:type message: DiscordMessage
:param title: Der Titel der Registrierungsmeldung. Kann None sein, wenn kein Titel festgelegt werden soll.
:type title: Optional[str]
:param description: Die Beschreibung der Registrierungsmeldung. Kann None sein, wenn keine Beschreibung festgelegt werden soll.
:type description: Optional[str]
:param link: [Deprecated] Ein optionaler Link, der in der Registrierungsmeldung angezeigt werden kann. Kann None sein, wenn kein Link festgelegt ist.
:type link: Optional[str]
"""
type RegistrationsRecord = WzRegistrations.Record
"""
Der Datentyp für die Informationen über registrierte Benutzer einer Guild im WZ-Modul.

:param guild: Das Guild-Objekt, für das die Informationen gelten.
:type guild: discord.Guild
:param user_id: Die ID des registrierten Benutzers als int.
:type user_id: int
:param registration_time: Der Zeitpunkt der Registrierung als datetime-Objekt.
:type registration_time: datetime.datetime
:param score_mod_lvl: Ein boolescher Wert, der angibt, ob die Score-Mod-Level-Funktion für diesen Benutzer aktiviert ist. Kann None sein, wenn der Wert nicht festgelegt ist.
:type score_mod_lvl: Optional[bool]
:param matchmaker: Ein boolescher Wert, der angibt, ob die Matchmaker-Funktion für diesen Benutzer aktiviert ist. Kann None sein, wenn der Wert nicht festgelegt ist.
:type matchmaker: Optional[bool]
"""
type RegistrationsRecords = WzRegistrations.Records
"""
Der Datentyp für eine Tuple von RegistrationsRecord-Objekten, die die Informationen über registrierte Benutzer einer Guild im WZ-Modul repräsentieren.
"""
type RolesRecord = WzRoles.Record
"""
Der Datentyp für die Rolleninformationen einer Guild im WZ-Modul.

:param guild: Das Guild-Objekt, für das die Informationen gelten.
:type guild: discord.Guild
:param role: Das DiscordRole-Objekt, das die Rolle repräsentiert.
:type role: DiscordRole
:param permanent: Ein boolescher Wert, der angibt, ob die Rolle permanent ist.
:type permanent: bool
:param score: Die Punktzahl der Rolle als int.
:type score: int

"""
type RolesRecords = WzRoles.Records
"""
Der Datentyp für eine Tuple von RolesRecord-Objekten, die die Rolleninformationen einer Guild im WZ-Modul repräsentieren.
"""

type ListRecord = WzList.Record
"""
Der Datentyp für die Listeneinträge einer Guild im WZ-Modul.

:param guild: Das Guild-Objekt, für das die Informationen gelten.
:type guild: discord.Guild
:param channel: Das DiscordChannel-Objekt, das den Kanal repräsentiert, in dem die Warteliste angezeigt wird.
:type channel: DiscordChannel
:param message: Das DiscordMessage-Objekt, das die Nachricht repräsentiert, die die Warteliste enthält.
:type message: DiscordMessage
:param title: Der Titel der Warteliste. Kann None sein, wenn kein Titel festgelegt ist.
:type title: Optional[str]
:param text: Der Text der Warteliste. Kann None sein, wenn kein Text festgelegt ist. Kann None sein, wenn kein Text festgelegt ist.
:type text: Optional[str]
"""
type ListRecords = WzList.Records
"""
Der Datentyp für eine Tuple von ListRecord-Objekten, die die Listeneinträge einer Guild im WZ-Modul repräsentieren.
"""

class Wz:
    """
    Die Hauptklasse des WZ-Moduls, die alle Funktionen und Datenstrukturen für die Verwaltung von WZ-bezogenen Informationen in einer Discord-Guild bereitstellt. Sie enthält Unterklassen für die Konfiguration, Rollenverwaltung, Registrierungskanal- und -nachrichtenverwaltung sowie die Verwaltung von registrierten Benutzern.
    """
    def __init__(self, database: Database):
        self.logger = logging.getLogger(__name__)
        self.config = WzConfig(database)
        self.roles = WzRoles(database)
        self.registration = WzRegistration(database)
        self.registrations = WzRegistrations(database)
        self.list = WzList(database)

    async def remove_guild_data(self, *, guild: Guild) -> bool:
        """
        Entfernt alle WZ-bezogenen Daten für eine bestimmte Guild aus der Datenbank. 
        Dies umfasst die Konfiguration, Rolleninformationen, Registrierungskanal- und -nachrichteninformationen sowie die Informationen über registrierte Benutzer."""
        try:
            results = [
                await self.config.remove(guild=guild),
                await self.registration.remove(guild=guild),
                await self.roles.remove(guild=guild),
                await self.list.remove(guild=guild),
                await self.registrations.remove(guild=guild)     
            ]
            if all(results):
                self.logger.info(f"{guild.name} ({guild.id}) - Wiped all WZ data.")
                return True
            else:
                self.logger.warning(f"{guild.name} ({guild.id}) - Failed to wipe some WZ data.")
                return False
        except Exception as e:
            self.logger.exception(f"{guild.name} ({guild.id}) - Critical failure during WZ data wipe: {e}")
            return False

    @property
    def tables(self) -> Tuple[str]:
        """
        Gibt eine Liste der Tabellennamen zurück, die von diesem Service verwendet werden. Diese Eigenschaft wird verwendet, um die Datenbanktabellen zu identifizieren, die für die Speicherung von WZ-bezogenen Informationen erforderlich sind.
        
        :return: Eine Liste von Tabellennamen als Strings.
        :rtype: Tuple[str]
        """
        return (
            self.config.table,
            self.roles.table,
            self.registration.table,
            self.registrations.table,
            self.list.table
        )