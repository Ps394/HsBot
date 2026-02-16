import asyncio
from Logger import logger
from typing import Type
from discord import RawMessageDeleteEvent, Guild, Client
from .Registry import REGISTRY
from .Instance import Instance, Instances

from . import Registration

__all__ = ["Manager", "Instance", "Instances", "Registration"]


class Manager:
    def __init__(self, client: Client):
        self.client = client
        self.instances_cache = {}

    async def get_instance(self, guild: Guild, instance_type: Type[Instance]) -> Instance:
        instances = await self.get_instances(guild)
        for instance in instances:
            if isinstance(instance, instance_type):
                return instance
        raise Exception(f"Instance of type {instance_type} not found for guild {guild.id}.")
 
    async def get_instances(self, guild: Guild) -> Instances:
        if guild.id not in self.instances_cache:
            instances = []
            for factory in REGISTRY:
                try:
                    instance = await factory.create(guild, self.client)
                    instances.append(instance)
                except Exception as e:
                    logger.exception(f"Failed to create overview instance for guild {guild.id}: {e}")
            self.instances_cache[guild.id] = instances
        return self.instances_cache[guild.id]
        
    async def startup(self):
        tasks = [self.init_guild(g) for g in self.client.guilds]
        await asyncio.gather(*tasks)
        logger.info("Manager startup complete.")

    async def init_guild(self, guild: Guild):
        instances = await self.get_instances(guild)
        for instance in instances:
            try:
                await instance.sync()
                await instance.ensure()
                logger.debug(f"Overview instance {instance.__class__.__name__} for guild {guild.id} synced successfully.")
            except Exception as e:
                logger.exception(f"Failed to sync overview instance for guild {guild.id}: {e}")

    async def sync(self, guild: Guild):
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.sync()
            except Exception as e:
                logger.exception(f"Failed to sync overview instance for guild {guild.id}: {e}")
                status = False
        return status

    async def ensure(self, guild: Guild) -> bool:
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.ensure()
            except Exception as e:
                logger.exception(f"Failed to ensure overview instance for guild {guild.id}: {e}")
                status = False
        return status
    
    async def send(self, guild: Guild) -> bool:
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.send()
            except Exception as e:
                logger.exception(f"Failed to send overview instance for guild {guild.id}: {e}")
                status = False
        return status
    
    async def update(self, guild: Guild) -> bool:
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.update()
            except Exception as e:
                logger.exception(f"Failed to update overview instance for guild {guild.id}: {e}")
                status = False
        return status
    
    async def clean(self, guild: Guild) -> bool:
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.clean()
            except Exception as e:
                logger.exception(f"Failed to clean overview instance for guild {guild.id}: {e}")
                status = False
        return status
    
    async def delete(self, guild: Guild) -> bool:
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.delete()
            except Exception as e:
                logger.exception(f"Failed to delete overview instance for guild {guild.id}: {e}")
                status = False
        return status
    
    async def on_message_delete(self, payload: RawMessageDeleteEvent) -> bool:
        guild = self.client.get_guild(payload.guild_id)
        if not guild:
            return False
        
        instances = await self.get_instances(guild)
        status = True
        for instance in instances:
            try:
                await instance.on_message_delete(payload)
            except Exception as e:
                logger.exception(f"Failed to handle message delete for overview instance in guild {guild.id}: {e}")
                status = False
        return status