import Database 
import asyncio
import discord
import os
import Emojis
from typing import Optional
from discord import app_commands
from Logger import logger
from . import Overviews
from . import Commands


try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - resource monitoring disabled")  

class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents = discord.Intents.default(), global_command_sync: Optional[bool]=True, **options):
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents, **options, logger=logger)
        self.services = Database.Services()
        self.tree = app_commands.CommandTree(self)
        self.overview_manager = Overviews.Manager(self)
        self.global_command_sync = global_command_sync

    async def update_loop(self, interval: int = 900):
        await self.wait_until_ready()
        while not self.is_closed():
            for guild in self.guilds:            
                try:
                    logger.info(f"{guild.name} (ID: {guild.id}) - Starting overview update.")
                    await self.overview_manager.update(guild=guild)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.exception(f"{guild.name} (ID: {guild.id}) - Error updating overviews: {e}")
            await asyncio.sleep(interval)
    
    async def resource_monitor_loop(self, interval: int = 60):
        if not PSUTIL_AVAILABLE:
            logger.info("Resource monitoring disabled (psutil not installed)")
            return
            
        await self.wait_until_ready()
        process = psutil.Process(os.getpid())
        
        while not self.is_closed():
            try:
                cpu_percent = process.cpu_percent(interval=1)
                memory_info = process.memory_info()
                storage = psutil.disk_usage('/')
                memory_mb = memory_info.rss / 1024 / 1024
                
                logger.info(
                    f"Resource Usage - CPU: {cpu_percent:.1f}%, "
                    f"Memory: {memory_mb:.1f} MB, "
                    f"Disk: {storage.percent}%"   
                )
            except Exception as e:
                logger.exception(f"Error monitoring resources: {e}")
            
            await asyncio.sleep(interval)

    async def register_commands(self):
        logger.info("Registering commands...")

        registered_count = 0
        
        for command in Commands.REGISTRY:
            try:
                if isinstance(command, type) and issubclass(command, app_commands.Group):
                    instance = command(self)
                    self.tree.add_command(instance)
                    for subcommand in instance.commands:
                        if isinstance(subcommand, app_commands.Command):
                            logger.debug(f"Registered subcommand: {subcommand.name} in group {instance.name}")
                            registered_count += 1
                        if isinstance(subcommand, app_commands.Group):
                            logger.debug(f"Registered subcommand group: {subcommand.name} in group {instance.name} with {len(subcommand.commands)} subcommands")
                            registered_count += len(subcommand.commands)       
                else:
                    self.tree.add_command(command)
                    registered_count += 1
                    logger.debug(f"Registered command: {getattr(command, 'name', command)}")

            except app_commands.CommandAlreadyRegistered:
                logger.warning(f"Command already registered: {getattr(command, 'name', command)}")
            except Exception as e:
                logger.exception(
                    f"Failed to register command {getattr(command, 'name', command)} "
                    f"({type(command).__name__}): {e}"
                )
        @self.tree.error
        async def tree_on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            try:
                await self.on_appplication_command_error(interaction, error)
            except Exception:
                logger.exception(f"Error while handling app command error: {error}")

        logger.info(f"Total commands registered: {registered_count}")

    async def sync_commands_global(self):
        if self.global_command_sync == True:
            try:
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                logger.info("Global commands synced successfully.")
            except Exception as e:
                logger.exception(f"Failed to sync global commands: {e}")

    async def sync_commands_guilds(self):
        if self.global_command_sync == False:
            for guild in self.guilds:
                try:
                    self.tree.clear_commands(guild=guild)
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync(guild=guild)
                    logger.info(f"{guild.name} (ID: {guild.id}) - Commands synced successfully.")
                except Exception as e:
                    logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to sync commands: {e}")

    async def setup_hook(self):
        await self.services.setup()

        await self.register_commands()
        await self.sync_commands_global()

        asyncio.create_task(self.resource_monitor_loop())
        logger.info("Resource monitoring started.")

        return await super().setup_hook()

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

        for guild in self.guilds: 
            await self.services.servers.add(guild=guild)

        await self.sync_commands_guilds()

        await self.overview_manager.startup()
        logger.debug("Overview manager startup complete.")

    async def on_guild_join(self, guild: discord.Guild):
        if await self.services.servers.add(guild=guild):
            logger.info(f"{guild.name} (ID: {guild.id}) - Joined new guild and added to database.")
        else:
            logger.error(f"{guild.name} (ID: {guild.id}) - Failed to add new guild to database.")
    
    async def on_guild_remove(self, guild: discord.Guild):
        if await self.services.remove_guild_data(guild=guild):
            logger.info(f"{guild.name} (ID: {guild.id}) - Removed guild from database on leave.")
        else:
            logger.error(f"{guild.name} (ID: {guild.id}) - Failed to remove guild from database on leave.")

    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        guild = before.guild
        try:
            reg_roles = await self.services.wz.roles.get(guild=guild)
            if not reg_roles or before.id not in [r.role.id for r in reg_roles]:
                return
            overviews : Overviews.Instances = await self.overview_manager.get_instances(guild=guild)

            if overviews:
                for overview in overviews:
                    await overview.sync()
                    await overview.ensure()

        except Exception as e:
            logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to handle role update for '{before.name}': {e}")

    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        try:
            try:
                configured_roles = await self.services.wz.roles.get(guild=guild)
                if not configured_roles or role.id not in [r.role.id for r in configured_roles]:
                    return
            except Exception as e:
                logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to check if deleted role '{role.name}' was a WZ registration role: {e}")
            
            tasks = []
            tasks.append(self.services.wz.roles.remove(guild=guild, role=role.id))
            tasks.append(self.services.wz.registrations.remove(guild=guild, role=role.id))
        
            asyncio.gather(*tasks)

            overviews : Overviews.Instances = await self.overview_manager.get_instances(guild=guild)
            if overviews:
                for overview in overviews:
                    await overview.sync()
                    await overview.ensure()
        except Exception as e:
            logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to remove deleted role '{role.name}' from WZ registration: {e}")

    async def on_raw_member_remove(self, member: discord.Member):
        guild = member.guild
        try:
            registration : Database.Wz.RegistrationsRecord = await self.services.wz.registrations.get(guild=guild, member=member.id)
            if registration:
                await self.services.wz.registrations.remove(guild=guild, member=member.id)
                overviews : Overviews.Instances = await self.overview_manager.get_instances(guild=guild)
                if overviews:
                    for overview in overviews:
                        await overview.sync()
                        await overview.ensure()
        except Exception as e:
            logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to remove registration for departed member '{member}': {e}")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = before.guild
        try:
            registration : Database.Wz.RegistrationsRecord = await self.services.wz.registrations.get(guild=guild, member=before.id)
            if not registration:
                return
            else:
                overviews : Overviews.Instances = await self.overview_manager.get_instances(guild=guild)
                if overviews:
                    for overview in overviews:
                        await overview.sync()
                        await overview.ensure()
        except Exception as e:
            logger.exception(f"{guild.name} (ID: {guild.id}) - Failed to update registration for member '{before}': {e}")

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        guild = self.get_guild(payload.guild_id)
        if not guild:
            return
        await self.overview_manager.on_message_delete(payload)

    async def on_appplication_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        log_context = f"{interaction.guild.name}({interaction.guild.id}) - {interaction.user} - Command: {interaction.command}"
        send = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        try:
            if isinstance(error, app_commands.MissingPermissions):
                message = f"{Emojis.ERROR} Du hast nicht die erforderlichen Berechtigungen, um diesen Befehl auszuführen."
                logger.warning(f"{log_context} - User missing permissions: {error}")
            elif isinstance(error, app_commands.BotMissingPermissions):
                message = f"{Emojis.ERROR} Mir fehlen die erforderlichen Berechtigungen, um diesen Befehl auszuführen."
                logger.error(f"{log_context} - Bot missing permissions: {error}")
            elif isinstance(error, app_commands.CommandOnCooldown):
                message = f"{Emojis.ERROR} Warte {error.retry_after:.1f} Sekunden, bevor du diesen Befehl erneut verwenden kannst."
                logger.info(f"{log_context} - Command on cooldown: {error}")
            
            else:
                message = f"{Emojis.ERROR} Ein unerwarteter Fehler ist aufgetreten: {error}"
                logger.exception(f"{log_context} - Unexpected error: {error}")
            await send(message, ephemeral=True)
        except Exception as e:
            logger.exception(f"{log_context} - Failed to send error message: {e}")

