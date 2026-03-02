from __future__ import annotations
import logging

from discord import Embed, Interaction, ButtonStyle, utils
from discord.ui import View, Button
from .registry import register
from .basic_overview import BasicOverview

from ...services import wz
from ...emojis import Emojis
from ...types import Optional, dataclass, field, List, Tuple, Guild, TextChannel, Message, Member, Role
from ...utils import fetch_channel, fetch_message, fetch_member, fetch_role
from ...exception import HTTPException, Forbidden, NotFound, InteractionResponded, RateLimited
from ...event import RawMessageDeleteEvent

logger = logging.getLogger(__name__)

@register
class RegistrationOverview(BasicOverview):
    """
    Übersicht, die die Registrierung für den nächsten WZ verwaltet und anzeigt.
    Sie zeigt die registrierten Benutzer und ihre Rollen an und ermöglicht es den Benutzern,
    sich für den nächsten WZ anzumelden oder abzumelden, indem sie auf die entsprechenden Schaltflächen klicken.
    """

    @dataclass
    class Configuration:
        @dataclass
        class ConfigurationRoles:
            permanent: List[Role] = None
            records: wz.RolesRecords = None
            non_permanent: List[Role] = None
            @property
            def all(self) -> Tuple[Role,...]:
                out = tuple(self.permanent) + tuple(self.non_permanent)
                return tuple(out)
    
        title: Optional[str] = None
        description: Optional[str] = None
        channel: Optional[TextChannel] = None
        roles: ConfigurationRoles = field(default_factory=ConfigurationRoles)   
        record: wz.RegistrationRecord = None

        @property
        def is_valid(self) -> bool:
            return self.channel is not None and self.roles is not None and len(self.roles.all) > 0

    @dataclass
    class Registration:
        @dataclass
        class Stats:
            total: int = 0
            permanent: int = 0
            non_permanent: int = 0
        @dataclass
        class Registrations:
            type RegistrationMembers = Optional[List[Member]]
            type RegistrationEmbeds = Optional[List[Embed]]
            type RegistrationList = Optional[List[str]]
            type RegistrationMessages = Optional[List[Message]]
            members: RegistrationMembers = None
            records: wz.RegistrationsRecords = None
            embeds: RegistrationEmbeds = None
            list: RegistrationList = None
            messages: RegistrationMessages = None

        type RegistrationEmbed = Optional[Embed]
        type RegistrationView = Optional[View]

        stats : Stats = field(default_factory=Stats)
        registrations: Registrations = field(default_factory=Registrations)
        embed: RegistrationEmbed = None
        view: RegistrationView = None
        message: Optional[Message] = None

        @property
        def has_message(self) -> bool:
            return self.message is not None
        
        @property
        def has_messages(self) -> bool:
            return self.registrations.messages is not None and len(self.registrations.messages) > 0

    def __init__(self, guild, services, client):
        super().__init__(guild, services, client)
        self.on_startup = True
        self.discord_member_changed = False
        self.discord_role_changed = False
        self.database_configuration_changed = False
        self.database_registrations_changed = False

        self.configuration = self.Configuration()
        self.registration = self.Registration()
        
    async def create_registrations_list(self) -> bool:
        try:
            if not self.registration.registrations.members:
                return False
            self.registration.registrations.list = []
            configured_roles : Tuple[Role,...] = self.configuration.roles.all 
            i = 0
            for member in self.registration.registrations.members:
                i += 1
                matched_role = next((r for r in configured_roles if r in member.roles), None)
                role_name = matched_role.name if matched_role else "-"
                self.registration.registrations.list.append(f"{i}. {member.display_name} [{role_name}]")
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to create registrations list: {e}")
            return False
            
    async def create_registrations_embeds(self, chunk_size=4095) -> bool:
        try:
            if not self.registration.registrations.list or len(self.registration.registrations.list) == 0:
                return False
            self.registration.registrations.embeds = []
            permanent_registration = f"{Emojis.PERMA_REGISTRATION.value}: {self.registration.stats.permanent}"
            non_permanent_registration = f"{Emojis.NORMAL_REGISTRATION.value}: {self.registration.stats.non_permanent}"
            total_registrations = f"{self.registration.stats.total}"
            temp = ""
            i = 0
            for row in self.registration.registrations.list:
                if len(temp) + len(row) + 1 > chunk_size:
                    i += 1
                    embed = self.BotEmbed(
                        title=f"{i}. Anmeldungen: {total_registrations} ( {permanent_registration} | {non_permanent_registration} )",
                        description=temp,
                        color=self.client_color,
                        client_avatar=self.client_avatar
                    ) 
                    self.registration.registrations.embeds.append(embed)
                    temp = ""
                temp += row + "\n"
            if temp:
                i += 1
                embed = self.BotEmbed(
                    title=f"{i}. Anmeldungen: {total_registrations} ( {permanent_registration} | {non_permanent_registration} )",
                    description=temp,
                    color=self.client_color,
                    client_avatar=self.client_avatar
                )
                self.registration.registrations.embeds.append(embed)
            return len(self.registration.registrations.embeds) > 0
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to create registrations embeds: {e}")
            return False
        

    async def registration_register(self, interaction: Interaction, role: Role):
        try:
            await interaction.response.defer(ephemeral=True)
            records =await self.services.wz.registrations.get(guild=self.guild, member=interaction.user.id)
            registration : wz.RegistrationsRecord = records[0] if records and len(records) > 0 else None
            message = ""
            if registration and registration.role == role.id:
                await self.services.wz.registrations.remove(guild=self.guild, member=interaction.user.id)
                message = f"{Emojis.UNREGISTER.value} Abmeldung von {role.name} erfolgreich."
                await interaction.user.remove_roles(role, reason="WZ Deregistration")
                action = "deregister"
            elif registration and registration.role != role.id:
                await interaction.user.remove_roles(registration.role, reason="WZ Registration Update") 
                await self.services.wz.registrations.add(guild=self.guild, member=interaction.user.id, role=role.id)
                await interaction.user.add_roles(role, reason="WZ Registration")
                message = f"{Emojis.REREGISTER.value} Aktualisierung auf {role.name} erfolgreich."
                action = "update"
            else:       
                await self.services.wz.registrations.add(guild=self.guild, member=interaction.user.id, role=role.id)
                await interaction.user.add_roles(role, reason="WZ Registration")
                message = f"{Emojis.REGISTER.value} Anmeldung mit {role.name} erfolgreich."
                action = "register"

            await interaction.followup.send(message, ephemeral=True)
            await self.sync()
            await self.sleep(self.WAIT_INTERVAL)
            await self.update_registrations()
            logger.debug(f"{self.log_context} {interaction.user} registration action({action}) for role {role.id}.")
        except (HTTPException, Forbidden, NotFound, InteractionResponded, Exception) as e:
            await interaction.followup.send(f"{Emojis.ERROR.value} Fehler bei der Registrierung.", ephemeral=True)
            logger.exception(f"{self.log_context} {interaction.user} failed to register for role {role.name}: {e}")

    async def update_registrations(self) -> bool:
        try:
            if self.configuration.is_valid:
                embeds = self.registration.registrations.embeds or []
                messages = self.registration.registrations.messages or []
                len_embeds = len(embeds)
                len_messages = len(messages)
                updated_messages = []

                for i in range(max(len_embeds, len_messages)):
                    if i < len_embeds and i < len_messages:
                        # Bestehende Nachricht aktualisieren
                        try:
                            await messages[i].edit(embed=embeds[i])
                            await self.services.wz.list.update(
                                guild=self.guild,
                                message=messages[i].id,
                                title=embeds[i].title,
                                text=embeds[i].description
                            )
                            updated_messages.append(messages[i])
                        except Exception as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Failed to update message {messages[i].id}: {e}")
                    elif i < len_embeds:
                        # Neue Nachricht senden
                        try:
                            new_msg = await self.configuration.channel.send(embed=embeds[i])
                            await self.services.wz.list.add(
                                guild=self.guild,
                                channel=self.configuration.channel.id,
                                message=new_msg.id,
                                title=embeds[i].title,
                                text=embeds[i].description
                            )
                            updated_messages.append(new_msg)
                        except NotFound:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Registration channel {self.configuration.channel.id} not found for sending new message.")
                        except Forbidden:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Missing permissions to access registration channel {self.configuration.channel.id} for sending new message.")
                        except HTTPException as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: HTTP error while sending new message in registration channel {self.configuration.channel.id}: {e}")
                        except ValueError as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Failed to add new message to database: {e}")
                    elif i < len_messages:
                        # Überschüssige Nachricht löschen
                        try:
                            await messages[i].delete()
                        except NotFound:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Message {messages[i].id} not found for deletion.")
                        except Forbidden:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Missing permissions to delete message {messages[i].id}.")
                        except HTTPException as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: HTTP error while deleting message {messages[i].id}: {e}")
                        await self.services.wz.list.remove(guild=self.guild, message=messages[i].id)

                # Messages-Liste aktualisieren, damit beim nächsten Aufruf wiederverwendet wird
                self.registration.registrations.messages = updated_messages
                return True
            else:
                logger.debug(f"{self.log_context} Cannot update registrations list overview: Invalid setup.")
                return False
        except Exception as e:
            logger.exception(f"{self.log_context} Registrations List Overview update failed: {e}")
            return False


    def gen_view(self)->View:
        view = View(timeout=None)
        row = 0
        configured_roles = self.configuration.roles.all
        if not configured_roles :
            logger.warning(f"{self.log_context} No configured roles found for registration overview view generation.")
            return view
        for role in configured_roles:
            def gen_callback(r: Role):
                async def callback(interaction: Interaction):
                    await self.registration_register(interaction, r)
                return callback
            
            button = Button(
                label=role.name,
                custom_id=f"wz_reg_{role.id}",
                style=ButtonStyle.primary,
                row=row
            )
            button.callback = gen_callback(role)
            view.add_item(button)
            row += 1
            logger.debug(f"{self.log_context} Added registration role button for role {role.id if role else 'unknown'} to view.")
        return view

    def create_registration_message(self)->bool:
        try:
            self.registration.embed = self.BotEmbed(
                title=self.configuration.record.title or "Anmeldung",
                description=self.configuration.record.description or "Melde dich hier für den nächsten WZ an.",
                color=self.client_color,
                client_avatar=self.client_avatar
            )
            self.registration.view = self.gen_view()
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to create registration message: {e}")
            return False

    def sync_registration_message(self):
        if not self.configuration.record.title:
            self.configuration.title = "Anmeldung"
        else:
            self.configuration.title = self.configuration.record.title
        if not self.configuration.record.description:
            self.configuration.description = "Melde dich hier für den nächsten WZ an."
        else:
            self.configuration.description = self.configuration.record.description

    async def sync_roles_from_db(self) -> bool:
        try:
            self.configuration.roles.records = await self.services.wz.roles.get(guild=self.guild)
            logger.info(f"len {len(self.configuration.roles.records) if self.configuration.roles.records else 0}")
            if not self.configuration.roles.records and len(self.configuration.roles.records) == 0:
                logger.warning(f"{self.log_context} No role records found in database for guild.")
                return False
            
            try:
                self.configuration.roles.permanent = [await fetch_role(self.guild, record.role) for record in self.configuration.roles.records if record.permanent]
            except Exception as e:
                logger.warning(f"{self.log_context} Failed to fetch permanent roles from database records during sync: {e}")
                
            try:
                self.configuration.roles.non_permanent = [await fetch_role(self.guild, record.role) for record in self.configuration.roles.records if not record.permanent]
            except Exception as e:
                logger.warning(f"{self.log_context} Failed to fetch non-permanent roles from database records during sync: {e}")
            
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync roles from registration record: {e}")
            return False

    async def sync_configuration_from_db(self) -> bool:
        try:
            self.configuration.record = await self.services.wz.registration.get(guild=self.guild)
            if not self.configuration.record:
                logger.warning(f"{self.log_context} No registration configuration record found in database for guild.")
                return False
            if not self.configuration.record.channel:
                logger.warning(f"{self.log_context} No registration channel found in configuration record for guild.")
                return False
            self.configuration.channel = await fetch_channel(self.guild, self.configuration.record.channel)
            if self.configuration.channel and isinstance(self.configuration.channel, int):
                logger.warning(f"{self.log_context} Registration channel with ID {self.configuration.record.channel} not found during configuration sync.")
                return False
            
            self.registration.message = await fetch_message(self.configuration.channel, self.configuration.record.message) if self.configuration.record.message else None
            
            self.sync_registration_message()
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync registration configuration from database: {e}")
            return False

    async def sync_registrations_from_db(self) -> bool:
        def normalize_records(records) -> list:
            """Normalisiert Records (None, einzelner Record, Tuple) zu einer Liste."""
            if records is None:
                return []
            if isinstance(records, (list, tuple)):
                return list(records)
            return [records]        
        try:
            raw = await self.services.wz.registrations.get(guild=self.guild)
            self.registration.registrations.records = normalize_records(raw)
            if not self.registration.registrations.records:
                logger.warning(f"{self.log_context} No registration records found in database for guild.")
                return False
            self.registration.registrations.members = [await fetch_member(self.guild, record.member) for record in self.registration.registrations.records]
            if not self.registration.registrations.members:
                logger.warning(f"{self.log_context} Failed to fetch members for registration records during sync.")
                return False
            
            self.registration.stats.permanent = len(self.configuration.roles.permanent) if self.configuration.roles.permanent else 0
            self.registration.stats.non_permanent = len(self.configuration.roles.non_permanent) if self.configuration.roles.non_permanent else 0
            self.registration.stats.total = self.registration.stats.permanent + self.registration.stats.non_permanent

            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync registrations from database: {e}")
            return False

    def check_member_with_registration_role(self, member: Member) -> bool:
        try:
            for role in self.configuration.roles.all:
                if role in member.roles:
                    return True
            return False
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to check user {member.id} for registration roles: {e}")
            return False
        
    async def sync_registrations_from_discord(self) -> bool:
        def normalize_records( records) -> list:
                """Normalisiert Records (None, einzelner Record, Tuple) zu einer Liste."""
                if records is None:
                    return []
                if isinstance(records, (list, tuple)):
                    return list(records)
                return [records]
        try:
            raw_records = await self.services.wz.registrations.get(guild=self.guild)
            records = normalize_records(raw_records)
            for member in self.guild.members:
                has_registration_role = self.check_member_with_registration_role(member)
                registration_record = next((record for record in records if record.member == member.id), None)
                if has_registration_role and not registration_record:
                    await self.services.wz.registrations.add(guild=self.guild, member=member.id, role=next((role for role in self.configuration.roles.all if role in member.roles), None).id)
                    logger.info(f"{self.log_context} Added registration record for member {member.id} with registration role.")
                elif not has_registration_role and registration_record:
                    await self.services.wz.registrations.remove(guild=self.guild, member=member.id)
                    logger.info(f"{self.log_context} Removed registration record for member {member.id} without registration role.")
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync registrations from discord: {e}")
            return False

    async def sync_list_messages_from_db(self) -> bool:
        """Lädt bestehende Registrierungslisten-Nachrichten aus der DB und holt die Discord-Message-Objekte."""
        try:
            list_records = await self.services.wz.list.get(guild=self.guild)
            if not list_records:
                self.registration.registrations.messages = []
                return True
            messages = []
            stale_ids = []
            for record in list_records:
                try:
                    channel = await fetch_channel(self.guild, record.channel)
                    if channel and not isinstance(channel, int):
                        msg = await fetch_message(channel, record.message)
                        if msg and not isinstance(msg, int):
                            messages.append(msg)
                        else:
                            stale_ids.append(record.message)
                    else:
                        stale_ids.append(record.message)
                except Exception:
                    stale_ids.append(record.message)
            # Stale Einträge bereinigen
            for stale_id in stale_ids:
                await self.services.wz.list.remove(guild=self.guild, message=stale_id)
                logger.debug(f"{self.log_context} Removed stale list message {stale_id} from database.")
            self.registration.registrations.messages = messages
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync list messages from database: {e}")
            self.registration.registrations.messages = []
            return False

    async def sync(self) -> bool:
        try:
            await self.wait_while_syncing()
            self.sync_start()
            # Synchronize configuration from database if needed
            self.on_startup = True
            if self.on_startup or self.database_configuration_changed:
                if await self.sync_configuration_from_db():
                    if await self.sync_roles_from_db():
                        self.create_registration_message()
            else:
                return False

            # Synchronize discord members with registration roles to database if needed
            if (self.on_startup and self.configuration.is_valid) or (self.discord_member_changed and self.configuration.is_valid):
                await self.sync_registrations_from_discord()

            # Synchronize list messages from database
            await self.sync_list_messages_from_db()

            # Synchronize registrations from database if needed
            if self.on_startup or self.database_registrations_changed:
                if await self.sync_registrations_from_db():
                    if await self.create_registrations_list():
                        await self.create_registrations_embeds()
                        
                
            logger.info(f"{self.log_context} Registration Overview: synced successfully.")
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync registration overview: {e}")
            return False
        finally:
            self.on_startup = False
            self.discord_member_changed = False
            self.database_registrations_changed = False
            self.database_configuration_changed = False
            await self.sync_stop()

    async def ensure(self) -> bool:
        try:
            if await self.update():
                return True
            for attempt in range(3):
                try:
                    return await self.send()
                except Exception as e:
                    logger.exception(f"{self.log_context} Failed to send registration overview during ensure attempt {attempt+1}: {e}")
                    await self.sleep(300)
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to ensure registration overview: {e}")
            return False

    async def send(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()
            if not self.configuration.is_valid:
                logger.info(f"{self.log_context} Cannot send registration overview: Invalid configuration.")
                return False
            
            if self.registration.has_message:
                await self.delete()

            self.registration.message = await self.configuration.channel.send(embed=self.registration.embed, view=self.registration.view)
            await self.services.wz.registration.setup_registration(
                guild=self.guild,
                message=self.registration.message.id
            )
            
            await self.update_registrations()
            logger.info(f"{self.log_context} Registration overview sent successfully.")
            return True
        except Forbidden:
            logger.warning(f"{self.log_context} Missing permissions to send message in registration channel {self.configuration.channel.id}.")
            return False
        except NotFound:
            logger.warning(f"{self.log_context} Registration channel {self.configuration.channel.id} not found for sending message.")
            return False
        except HTTPException as e:
            logger.warning(f"{self.log_context} HTTP error while sending message in registration channel {self.configuration.channel.id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to send registration overview: {e}")
            return False
        finally:
            await self.work_stop()
    
    async def update(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()   

            if not self.configuration.is_valid:
                logger.info(f"{self.log_context} Cannot update registration overview: Invalid configuration.")
                return False
            
            if not self.registration.has_message:
                logger.info(f"{self.log_context} Cannot update registration overview: No existing message.")
                return False
      
            await self.registration.message.edit(embed=self.registration.embed, view=self.registration.view)
            logger.info(f"{self.log_context} Registration overview updated successfully.")
            return True
        except Forbidden:
            logger.warning(f"{self.log_context} Missing permissions to edit message in registration channel {self.configuration.channel.id}.")
            return False
        except NotFound:
            logger.warning(f"{self.log_context} Registration channel {self.configuration.channel.id} or message not found for updating.")
            return False
        except HTTPException as e:
            logger.warning(f"{self.log_context} HTTP error while updating message in registration channel {self.configuration.channel.id}: {e}")
            return False   
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to update registration overview: {e}")
            return False
        finally:
            await self.work_stop()
        
    async def clean(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()

            if not self.configuration.is_valid:
                return False

            await self.configuration.channel.purge(limit=999, check=lambda m: m.author.id != self.client.user.id and m.pinned == False)
            return True
        except Forbidden:
            logger.warning(f"{self.log_context} Missing permissions to purge messages in registration channel {self.configuration.channel.id}.")
            return False
        except NotFound:
            logger.warning(f"{self.log_context} Registration channel {self.configuration.channel.id} not found for purging messages.")
            return False     
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to clean registration channel: {e}")
            return False
        finally:            
            await self.work_stop()

    async def delete(self) -> bool:
        try:
            await self.wait_while_deleting()
            self.delete_start()

            if not self.configuration.is_valid:
                return False
            
            await self.configuration.channel.purge(limit=999, check=lambda m: m.author.id == self.client.user.id)
            return True
        except Forbidden:
            logger.warning(f"{self.log_context} Missing permissions to delete messages in registration channel {self.configuration.channel.id}.")
            return False
        except HTTPException as e:
            logger.warning(f"{self.log_context} HTTP error while deleting messages in registration channel {self.configuration.channel.id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to delete registration messages: {e}")
            return False
        finally:
            await self.delete_stop()

    async def on_message_delete(self, payload: RawMessageDeleteEvent) -> bool:
        if self.IS_DELETING:
            await self.wait_while_deleting()
            return False
        await self.sync()
        await self.ensure()
        return True