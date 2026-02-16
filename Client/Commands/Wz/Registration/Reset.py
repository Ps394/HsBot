import Emojis
from Database import Services, Wz
from Logger import logger
from discord import app_commands, Interaction, HTTPException, Forbidden, NotFound, InteractionResponded
from ....Overviews import Manager

@app_commands.checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@app_commands.default_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@app_commands.command(name="reset", description="Registrierung zurücksetzen")
@app_commands.checks.cooldown(1, 120, key=lambda i: (i.guild_id))
async def reset(interaction: Interaction, ephemeral: bool = True):
    MESSAGES = {
        "SUCCESS": f"{Emojis.SUCCESS} Alle nicht permanenten Registrierungen wurden zurückgesetzt.",
        "ERROR": f"{Emojis.ERROR} Beim Zurücksetzen der Registrierungen ist ein Fehler aufgetreten.",
        "NOT_CONFIGURED": f"{Emojis.WARNING} Die WZ-Registrierung ist nicht konfiguriert. Bitte richte zuerst einen Registrierungskanal und Rollen ein.",
        "NO_REGISTRATIONS": f"{Emojis.WARNING} Es sind keine Registrierungen zum Entfernen vorhanden. Permaente Rollen werden nicht entfernt."
    }
    LOG_CONTEXT = f"{interaction.guild.name}({interaction.guild.id}) - {interaction.user} - WZ Registration Reset : "
    LOGS = {
        "EXCEPTION": f"{LOG_CONTEXT}",
        "NO_SERVICES_OR_OVERVIEW": f"{LOG_CONTEXT} Required services or overview manager not found on client.",
        "NOT_CONFIGURED": f"{LOG_CONTEXT} No registration channel configured.",
        "NO_REGISTRATIONS": f"{LOG_CONTEXT} No removable registrations found."
    }
    try:
        await interaction.response.defer(ephemeral=ephemeral)
        services: Services = getattr(interaction.client, "services")
        overview_manager: Manager = getattr(interaction.client, "overview_manager", None)
        if not services or not overview_manager:
            raise TypeError(LOGS["NO_SERVICES_OR_OVERVIEW"])
        
        configuration : Wz.RegistrationRecord = await services.wz.registration.get(guild=interaction.guild)
        configured_roles : Wz.RolesRecords = await services.wz.roles.get(guild=interaction.guild)
        
        if not configuration or not configured_roles or not configuration.channel:
            await interaction.followup.send(MESSAGES["NOT_CONFIGURED"], ephemeral=True)
            raise ValueError(LOGS["NOT_CONFIGURED"])
        
        none_permanent_roles = [role_record.role.id for role_record in configured_roles if not role_record.permanent] if configured_roles else [] 

        registrations: Wz.RegistrationsRecords = await services.wz.registrations.get(guild=interaction.guild, roles=none_permanent_roles)
        if not registrations:
            await interaction.followup.send(MESSAGES["NO_REGISTRATIONS"], ephemeral=True)
            logger.warning(LOGS["NO_REGISTRATIONS"])
            return
        
        for record in registrations:
            try: 
                if record.member and record.role:
                    await record.member.remove_roles(record.role, reason="WZ Registration Reset")
            except (HTTPException, Forbidden, NotFound) as e:
                logger.warning(f"{LOG_CONTEXT} Failed to remove role {record.role.id} from member {record.member.id} during WZ reset: {e}")

        success = await services.wz.registrations.remove(guild=interaction.guild, roles=none_permanent_roles)
        if success:
            await overview_manager.clean(interaction.guild)
            await overview_manager.sync(guild=interaction.guild)
            await overview_manager.update(interaction.guild)
            await interaction.followup.send(MESSAGES["SUCCESS"], ephemeral=ephemeral)
        else:
            await interaction.followup.send(MESSAGES["ERROR"], ephemeral=ephemeral)
    except (ValueError, HTTPException, Forbidden, NotFound, InteractionResponded, Exception) as e:
        await interaction.followup.send(MESSAGES["ERROR"], ephemeral=ephemeral)
        logger.exception(f"{LOGS['EXCEPTION']} {e}")
        return