import asyncio
from typing import Optional
from Database import Services
from discord import Guild, Client, Color, Asset
from .Instance import Instance 

class BaseOverview:
    IS_SYNCING : bool = False
    IS_WORKING : bool = False
    IS_DELETING : bool = False

    WAIT_INTERVAL : float = 0.2
    WAIT_INTERVAL_LONG : float = 1.0

    async def sleep(self, seconds: float = WAIT_INTERVAL_LONG):
        await asyncio.sleep(seconds)

    async def wait_while_syncing(self):
        while self.IS_SYNCING:
            await self.sleep()

    async def wait_while_working(self):
        while self.IS_WORKING:
            await self.sleep()

    async def wait_while_deleting(self):
        while self.IS_DELETING:
            await self.sleep()

    async def wait_while_busy(self):
        while self.is_busy():
            await self.sleep()
    
    def sync_start(self):
        self.IS_SYNCING = True
    
    def work_start(self):
        self.IS_WORKING = True
        
    def delete_start(self):
        self.IS_DELETING = True

    async def sync_stop(self):
        await self.sleep(self.WAIT_INTERVAL)
        self.IS_SYNCING = False

    async def work_stop(self):
        await self.sleep(self.WAIT_INTERVAL)
        self.IS_WORKING = False

    async def delete_stop(self):
        await self.sleep(self.WAIT_INTERVAL)
        self.IS_DELETING = False

    def is_busy(self) -> bool:
        return self.IS_SYNCING or self.IS_WORKING or self.IS_DELETING

    @property
    def client_color(self) -> Color:
        return max(self.guild.get_member(self.client.user.id).roles, key=lambda r: r.position).color

    @property
    def client_name(self) -> str:
        return self.client.user.name
    
    @property
    def client_avatar(self) -> Asset:
        return self.guild.icon if self.guild.icon else self.client.user.avatar if self.client.user.avatar else None
    
    @property
    def log_context(self) -> str:
        return f"{__name__} - {self.guild.name}({self.guild.id}) :"

    def __init__(self, guild: Guild, services: Services, client: Client):
        self.guild = guild
        self.services = services
        self.client = client

    @classmethod
    async def create(cls, guild: Guild, client: Client) -> Instance:
 
        services = getattr(client, "services", None)

        if services is None:
            raise Exception(f"Client services not found for guild {guild.id}.") 

        return cls(guild, services, client)