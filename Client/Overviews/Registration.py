import asyncio
import Emojis
from Logger import logger
from typing import Sequence, Optional
from discord import Embed, Interaction, Role, ButtonStyle, utils, RawMessageDeleteEvent, InteractionResponded, TextChannel, Message
from discord.ui import View, Button
from Database import Wz
from Database.Wz.Utils import NotFound, Forbidden, HTTPException
from .Registry import register
from .BaseOverview import BaseOverview

@register
class RegistrationOverview(BaseOverview):
    registration: Wz.RegistrationRecord
    configured_roles: Wz.RolesRecords
    registrations: Wz.RegistrationsRecords
    list_records: Wz.ListRecords

    type RegistrationsEmbeds = Optional[tuple[Embed]]
    type RegistrationsList = Optional[tuple[str]]

    registration_embed : Optional[Embed] = None
    registrations_embeds : Optional[RegistrationsEmbeds] = None
    registrations_lists : Optional[RegistrationsList] = None

    registrations_total : int = 0
    registrations_permanent : int = 0
    registrations_non_permanent : int = 0

    registrations_max_per_list : int = 40


    total_registrations: int
    permanent_registrations: int
    non_permanent_registrations: int

    MAX_REGISTRATIONS_PER_LIST = 40
    
    @property
    def is_valid_setup(self) -> bool:
        registration = self.registration
        configured_roles = self.configured_roles
        if not registration or not configured_roles:
            return False
        if not isinstance(registration.channel, TextChannel):
            return False
        return True 

    async def create_registrations_embed(self, title: str, description: str) -> Embed:
        try:
            embed = Embed(title=title, description=description, color=self.client_color)
            embed.set_footer(text=f"|", icon_url=self.client_avatar.url if self.client_avatar else None)
            embed.timestamp = utils.utcnow()
            logger.debug(f"{self.log_context} Generated registrations list embed")
            return embed
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to generate registration embed: {e}")
            return Embed(title=title, description=description, color=self.client_color)
        
    async def create_registrations_list(self, registrations: Sequence[Wz.Registrations.Record], chunk_size=4095) -> RegistrationsList:
        if not registrations:
            return None
        registration_list = ""
        i = 0
        for record in registrations:
            if i >= self.registrations_max_per_list:
                break
            i += 1
            registration_list += f"{i}. {record.member.display_name} [{record.role.name}]\n"
        return tuple(registration_list[i:i+chunk_size] for i in range(0, len(registration_list), chunk_size)) if registration_list else None
    
    async def create_registrations_embeds(self, chunk_size=4095) -> RegistrationsEmbeds:
        registrations = self.registrations
        configured_roles = self.configured_roles
        if not registrations:
            return None
        registration_list = await self.create_registrations_list(registrations, chunk_size)
        if not registration_list:
            return None
        permanent_ids = {record.role.id for record in configured_roles if record.permanent} if configured_roles else set()
        non_permanent_ids = {record.role.id for record in configured_roles if not record.permanent} if configured_roles else set()

        permanent_registration = f"{Emojis.PERMA_REGISTRATION}: {sum(1 for record in registrations if record.role.id in permanent_ids)}"
        non_permanent_registration = f"{Emojis.NORMAL_REGISTRATION}: {sum(1 for record in registrations if record.role.id in non_permanent_ids)}"
        total_registrations = f"{len(registrations)}"
      
        embeds = []
        for i, chunk in enumerate(registration_list):
            title = f"Anmeldungen: {total_registrations} ( {permanent_registration} | {non_permanent_registration} )"
            embed = await self.create_registrations_embed(title=title, description=chunk)
            embeds.append(embed)
        return tuple(embeds) if embeds else None

    async def create_registration_embed(self) -> Embed:
        title = "Anmeldung"
        description = "Melde dich hier für den nächsten WZ an."
        registration = self.registration
        try:
            isDefaultTitle = True
            isDefaultDescription = True
            if registration.title:
                title = registration.title
                isDefaultTitle = False
            if registration.description:
                description = registration.description
                isDefaultDescription = False
            embed = Embed(title=title, description=description, color=self.client_color)
            embed.set_footer(text=f"|", icon_url=self.client_avatar.url if self.client_avatar else None)
            embed.timestamp = utils.utcnow()
            logger.debug(f"{self.log_context} Generated registration embed (Default Title: {isDefaultTitle}, Default Description: {isDefaultDescription})")
            return embed
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to generate registration embed: {e}")
            return Embed(title=title, description=description, color=self.client_color)
        
    async def create_registration_view(self) -> View :
        try:
            configured_roles = self.configured_roles
            view = View(timeout = None)
            row = 0
            
            if not configured_roles:
                return view
            
            for record in configured_roles:
                if not record.role: continue

                def gen_callback(r: Role):
                    async def callback(interaction: Interaction):
                        await self.registration_register(interaction, r)
                    return callback
            
                button = Button(
                    label=record.role.name,
                    custom_id=f"wz_reg_{record.role.id}",
                    style=ButtonStyle.primary,
                    row=row
                )
                button.callback = gen_callback(record.role)
                view.add_item(button)
                row += 1
                logger.debug(f"{self.log_context} Added registration role button for role {record.role.id if record.role else 'unknown'} to view.")

            return view
        except Exception as e:
            logger.exception(f"{self.log_context} View Error: {e}")
            return View(timeout=None)
        
    async def registration_register(self, interaction: Interaction, role: Role):
        try:
            await interaction.response.defer(ephemeral=True)
            registration : Wz.RegistrationsRecord = await self.services.wz.registrations.get(guild=self.guild, member=interaction.user.id)
            message = ""
            if registration and registration.role.id == role.id:
                await self.services.wz.registrations.remove(guild=self.guild, member=interaction.user.id)
                message = f"{Emojis.UNREGISTER} Abmeldung von {role.name} erfolgreich."
                await interaction.user.remove_roles(role, reason="WZ Deregistration")
                action = "deregister"
            elif registration and registration.role.id != role.id:
                await interaction.user.remove_roles(registration.role, reason="WZ Registration Update") 
                await self.services.wz.registrations.add(guild=self.guild, member=interaction.user.id, role=role.id)
                await interaction.user.add_roles(role, reason="WZ Registration")
                message = f"{Emojis.REREGISTER} Aktualisierung auf {role.name} erfolgreich."
                action = "update"
            else:       
                await self.services.wz.registrations.add(guild=self.guild, member=interaction.user.id, role=role.id)
                await interaction.user.add_roles(role, reason="WZ Registration")
                message = f"{Emojis.REGISTER} Anmeldung mit {role.name} erfolgreich."
                action = "register"

            await interaction.followup.send(message, ephemeral=True)
            await self.sync()
            await self.update_registrations()
            logger.debug(f"{self.log_context} {interaction.user} registration action({action}) for role {role.id}.")
        except (HTTPException, Forbidden, NotFound, InteractionResponded, Exception) as e:
            await interaction.followup.send(f"{Emojis.ERROR} Fehler bei der Registrierung.", ephemeral=True)
            logger.exception(f"{self.log_context} {interaction.user} failed to register for role {role.name}: {e}")

    async def update_registrations(self) -> bool:
        try:
            if self.is_valid_setup:
                registrations_embeds = await self.create_registrations_embeds()
        
                list_records = self.list_records
                len_embeds = len(registrations_embeds) if registrations_embeds else 0
                len_records = len(list_records) if list_records else 0

                for i in range(max(len_embeds, len_records)):
                    await self.sleep()
                    if i < len_embeds and i < len_records:
                        try:
                            await list_records[i].message.edit(embed=registrations_embeds[i])
                            await self.services.wz.list.update(
                                guild=self.guild,
                                message=list_records[i].message.id,
                                title=registrations_embeds[i].title,
                                text=registrations_embeds[i].description
                            )
                        except Exception as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Failed to update message {list_records[i].message.id}: {e}")
                    elif i < len_embeds:
                        try:
                            message = await self.registration.channel.send(embed=registrations_embeds[i])
                            await self.services.wz.list.add(
                                guild=self.guild,
                                channel=self.registration.channel.id,
                                message=message.id,
                                title=registrations_embeds[i].title,
                                text=registrations_embeds[i].description
                            ) 
                        except NotFound:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Registration channel {self.registration.channel.id} not found for sending new message.")
                        except Forbidden:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Missing permissions to access registration channel {self.registration.channel.id} for sending new message.")
                        except HTTPException as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: HTTP error while sending new message in registration channel {self.registration.channel.id}: {e}")
                        except ValueError as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Failed to add new message to database: {e}")
                    elif i < len_records:
                        try:
                            await list_records[i].message.delete()
                        except NotFound:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Message {list_records[i].message.id} not found for deletion.")
                        except Forbidden:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: Missing permissions to delete message {list_records[i].message.id}.")
                        except HTTPException as e:
                            logger.warning(f"{self.log_context} Registrations List Overview update warning: HTTP error while deleting message {list_records[i].message.id}: {e}")
                        await self.services.wz.list.remove(guild=self.guild, message=list_records[i].message.id)

                return True
            else:
                logger.debug(f"{self.log_context} Cannot update registrations list overview: Invalid setup.")
                return False
        except Exception as e:
            logger.exception(f"{self.log_context} Registrations List Overview update failed: {e}")
            return False

    async def sync(self) -> bool:
        try:
            await self.wait_while_syncing()
            self.sync_start()

            self.registration = await self.services.wz.registration.get(guild=self.guild)
            self.configured_roles = await self.services.wz.roles.get(guild=self.guild)
            self.registrations = await self.services.wz.registrations.get(guild=self.guild)
            self.list_records = await self.services.wz.list.get(guild=self.guild)
            logger.info(f"{self.log_context} Registration Overview: synced successfully.")
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to sync registration overview: {e}")
            return False
        finally:
            await self.sync_stop()

    async def ensure(self) -> bool:
        try:
            if await self.update():
                return True
            for i in range(3):
                try:
                    if await self.send():
                        return True
                    await self.sleep(300)
                except Exception as e:
                    logger.exception(f"{self.log_context} Failed to send registration overview during ensure attempt {i+1}: {e}")
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to ensure registration overview: {e}")
            return False

    async def repair(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()
            configured_roles = self.configured_roles
            registrations = self.registrations
            
            if self.is_valid_setup:
                for role in self.guild.roles:
                    try:
                        if role.id in {record.role.id for record in configured_roles if record.role}:
                            for member in role.members:
                                try:
                                    if not member.id in {record.member.id for record in registrations}:
                                        await self.services.wz.registrations.add(guild=self.guild, member=member.id, role=role.id)
                                        logger.info(f"{self.log_context} Synced registration for member {member.id} with role {role.id}.")                        
                                except (HTTPException, Forbidden, NotFound, InteractionResponded) as e:
                                    logger.warning(f"{self.log_context} Failed to sync registration for member {member.id}: {e}")
                    except Forbidden:
                        logger.warning(f"{self.log_context} Missing permissions to manage roles during registration sync.")
                    except NotFound:
                        logger.warning(f"{self.log_context} Role not found during registration sync.")
                    except HTTPException as e:
                        logger.warning(f"{self.log_context} HTTP error during registration sync: {e}")
            logger.info(f"{self.log_context} Registration overview repaired successfully.")
            return True
        except Exception as e:
            logger.exception(f"{self.log_context} Failed to repair registration overview: {e}")
            return False
        finally:
            await self.work_stop()
            await self.sync()

    async def send(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()
            if self.is_valid_setup:
                registration = self.registration
                try:
                    if isinstance(registration.channel, (NotFound, Forbidden, HTTPException, TypeError, Exception)):
                        raise registration.channel
                    # Try to delete existing message if it exists
                    if registration.message is not None and isinstance(registration.message, Message):
                        await registration.message.delete()
                    elif isinstance(registration.message, (NotFound, Forbidden, HTTPException, TypeError, Exception)):
                        raise registration.message

                    await registration.message.delete()

                except (NotFound, Forbidden, HTTPException, TypeError, Exception) as e:
                    logger.warning(f"{self.log_context} Failed to delete existing registration overview message during send: {e}")
                try:
                    await self.services.wz.registration.setup_registration(
                        guild=self.guild,
                        message=None
                    )
                    logger.debug(f"{self.log_context} Cleared registration overview message reference in database after failed deletion.")
                except Exception as e:
                    logger.exception(f"{self.log_context} Failed to clear registration overview message reference in database after failed deletion: {e}")
                embed = await self.create_registration_embed()
                view = await self.create_registration_view()
                try:
                    message = await registration.channel.send(embed=embed, view=view)
                    
                    return await self.services.wz.registration.setup_registration(guild=self.guild, message=message.id ) and await self.update_registrations()

                except (NotFound, Forbidden, HTTPException, TypeError, ValueError, Exception) as e:
                    logger.warning(f"{self.log_context} Failed to send registration overview message during send: {e}")
                    return False
            return False
        finally:
            await self.work_stop()
    
    async def update(self) -> bool:
        try:
            await self.wait_while_busy()
            self.work_start()   
            if not self.is_valid_setup:
                await self.delete()
                raise ValueError("Invalid setup for registration overview. Cannot update.")
            registration = self.registration
            if isinstance(registration.channel, (NotFound, Forbidden, HTTPException, TypeError, Exception)):
                raise registration.channel
            if registration.message is None:
                raise ValueError("No message exists for registration overview. Use send() first.")
            if isinstance(registration.message, (NotFound, Forbidden, HTTPException, TypeError, Exception)):
                raise registration.message
            try:
                embed = await self.create_registration_embed()
                view = await self.create_registration_view()
                await registration.message.edit(embed=embed, view=view)
                return await self.update_registrations()
            except (NotFound, Forbidden, HTTPException, Exception) as e:
                logger.warning(f"{self.log_context} Failed to update registration overview message: {e}")
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
            if self.is_valid_setup:
                registration = self.registration
                try:
                    async for msg in registration.channel.history(limit=999):
                        if msg.author.id != self.client.user.id:
                            try:
                                await msg.delete()
                            except Forbidden:
                                logger.warning(f"{self.log_context} Missing permissions to delete messages in registration channel {registration.channel.id}.")
                                return False
                            except NotFound:
                                logger.warning(f"{self.log_context} Registration channel {registration.channel.id} not found for deleting messages.")
                                return False
                            except HTTPException as e:
                                logger.warning(f"{self.log_context} HTTP error while deleting messages in registration channel {registration.channel.id}: {e}")
                                return False
                except Exception as e:
                    logger.exception(f"{self.log_context} Failed to clean registration channel: {e}")
                    return False
                return True
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
                
            if self.is_valid_setup:
                registration = self.registration
    
                async for msg in registration.channel.history(limit=999):
                    if msg.author.id == self.client.user.id:
                        try:
                            await msg.delete()
                        except Forbidden:
                            logger.warning(f"{self.log_context} Missing permissions to delete messages in registration channel {registration.channel.id}.")
                        except NotFound:
                            logger.warning(f"{self.log_context} Registration channel {registration.channel.id} not found for deleting messages.")
                        except HTTPException as e:
                            logger.warning(f"{self.log_context} HTTP error while deleting messages in registration channel {registration.channel.id}: {e}")
        
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