import logging
import io
from discord import app_commands, Interaction, File
from ....overviews import Manager
from .....emojis import Emojis
from .....services import Services, wz

logger = logging.getLogger(__name__)

@app_commands.checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@app_commands.default_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@app_commands.checks.bot_has_permissions(attach_files=True)
@app_commands.command(name="csv", description="gibt die Registrierungen als CSV-Datei aus")
@app_commands.checks.cooldown(1, 120, key=lambda i: (i.guild_id))
async def csv(interaction: Interaction, ephemeral: bool = True):
    MESSAGES = {
        "SUCCESS": f"{Emojis.SUCCESS.value} Die Registrierungen wurden als CSV-Datei exportiert.",
        "ERROR": f"{Emojis.ERROR.value} Fehler beim Exportieren der Registrierungen als CSV-Datei.",
        "NOT_CONFIGURED": f"{Emojis.WARNING.value} Die WZ-Registrierung ist nicht konfiguriert. Bitte richte zuerst einen Registrierungskanal und Rollen ein.",
        "NO_REGISTRATIONS": f"{Emojis.WARNING.value} Es sind keine Registrierungen zum Exportieren vorhanden."
    }
    LOG_CONTEXT = f"{interaction.guild.name}({interaction.guild.id}) - {interaction.user} - WZ Registration CSV : "
    LOGS = {
        "EXCEPTION": f"{LOG_CONTEXT}",
        "NO_SERVICES_OR_OVERVIEW": f"{LOG_CONTEXT} Required services or overview manager not found on client.",
        "NO_REGISTRATIONS": f"{LOG_CONTEXT} No registrations found to export."
    }
    try:
        await interaction.response.defer(ephemeral=ephemeral)
        services: Services = getattr(interaction.client, "services")
        overview_manager: Manager = getattr(interaction.client, "overview_manager", None)
        if not services or not overview_manager:
            raise TypeError(LOGS["NO_SERVICES_OR_OVERVIEW"])
        
        configuration : wz.RegistrationRecord = await services.wz.registration.get(guild=interaction.guild)
        configured_roles : wz.RolesRecords = await services.wz.roles.get(guild=interaction.guild)
        
        if not configuration or not configured_roles or not configuration.channel:
            await interaction.followup.send(MESSAGES["NOT_CONFIGURED"], ephemeral=True)
            return
        
        role_ids = [role_record.role.id for role_record in configured_roles] if configured_roles else []
        registrations: wz.RegistrationsRecords = await services.wz.registrations.get(guild=interaction.guild, roles=role_ids)
        
        if not registrations:
            await interaction.followup.send(MESSAGES["NO_REGISTRATIONS"], ephemeral=True)
            logger.warning(LOGS["NO_REGISTRATIONS"])
            return
        
        csv_content = "NR; User_Name; Member_Name; Role; Timestamp; Score; Comment\n"
        record : wz.RegistrationsRecord
        for idx, record in enumerate(registrations, start=1):
            user_name = record.member.name if record.member and record.member.name else "null"
            member_name = record.member.display_name if record.member and record.member.display_name else "null"
            role_name = record.role.name if record.role else "Unknown Role"
            score = ""
            comment = ""
            timestamp = record.timestamp if record.timestamp else "Unknown Timestamp"
            csv_content += f"{idx}; {user_name}; {member_name}; {role_name}; {timestamp}; {score}; {comment}\n"
        try:
            bio = io.BytesIO(csv_content.encode('utf-8-sig'))
            bio.seek(0)
            csv_file = File(fp=bio, filename=f"wz_registrations_{interaction.guild.id}.csv")
            await interaction.followup.send(content=MESSAGES["SUCCESS"], file=csv_file, ephemeral=True)
        finally:
            try:
                bio.close()
            except Exception:
                pass
    except Exception as e:
        await interaction.followup.send(MESSAGES["ERROR"], ephemeral=True)
        logger.exception(f"{LOGS['EXCEPTION']} {e}")
