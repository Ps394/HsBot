from discord import Guild
from typing import Optional, Sequence, Union
from Logger import logger
from . import Utils
from .Config import Config
from .Roles import Roles
from .Registration import Registration
from .Registrations import Registrations
from .List import List

type ConfigRecord = Optional[Config.Record]
type RegistrationRecord = Optional[Registration.Record]

type RegistrationsRecord = Optional[Registrations.Record]
type RegistrationsRecords = tuple[RegistrationsRecord]

type RolesRecord = Optional[Roles.Record]
type RolesRecords = tuple[RolesRecord]

type ListRecord = Optional[List.Record]
type ListRecords = tuple[ListRecord]


__all__ = [
    "Utils",
    "Config",
    "Roles",
    "Registration",
    "Registrations",
    "List",
    "Wz",
    "ConfigRecord",
    "RegistrationRecord",
    "RegistrationsRecord",
    "RegistrationsRecords",
    "RolesRecord",
    "RolesRecords",
    "ListRecord",
    "ListRecords"
]

class Wz:
    def __init__(self, database):
        self.config = Config(database)
        self.roles = Roles(database)
        self.registration = Registration(database)
        self.registrations = Registrations(database)
        self.list = List(database)

    async def remove_guild_data(self, *, guild: Guild) -> bool:
        try:
            results = [
                await self.config.database.execute(f"DELETE FROM {Config.CLASSNAME} WHERE Guild = ?", (guild.id,)),
                await self.roles.database.execute(f"DELETE FROM {Roles.CLASSNAME} WHERE Guild = ?", (guild.id,)),
                await self.registration.database.execute(f"DELETE FROM {Registration.CLASSNAME} WHERE Guild = ?", (guild.id,)),
                await self.registrations.database.execute(f"DELETE FROM {Registrations.CLASSNAME} WHERE Guild = ?", (guild.id,)),
                await self.list.database.execute(f"DELETE FROM {List.CLASSNAME} WHERE Guild = ?", (guild.id,))        
            ]
            if all(results):
                logger.info(f"{guild.name} ({guild.id}) - Wiped all WZ data.")
                return True
            else:
                logger.warning(f"{guild.name} ({guild.id}) - Failed to wipe some WZ data.")
                return False
        except Exception as e:
            logger.exception(f"{guild.name} ({guild.id}) - Critical failure during WZ data wipe: {e}")
            return False

    @property
    def tables(self) -> list[str]:
        return [
            Config.TABLE,
            Roles.TABLE,
            Registration.TABLE,
            Registrations.TABLE,
            List.TABLE
        ]