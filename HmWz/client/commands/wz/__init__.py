from discord.app_commands import Group, checks, command
from discord import Interaction
from . import setup, registration
from ..registry import register

__all__ = [
    "WzGroup"
]
@checks.bot_has_permissions(manage_roles=True, manage_channels=True, view_channel=True, send_messages=True, read_message_history=True, attach_files=True)
@checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
class WzGroup(Group):
    def __init__(self, bot):
        super().__init__(
            name="wz", 
            description="Alle Befehle rund um die WZ-Registrierung"
        )

        self.bot = bot

        self.add_command(setup.SetupGroup())
        self.add_command(registration.RegistrationGroup())


    @command(name="about-bot", description="Informationen über den Bot und seine Funktionen")    
    async def about_bot(self, interaction : Interaction, ephemeral: bool = True):
        MESSAGES = """
### {Botname}
- Ich bin ein in Python geschriebener Discord-Bot, der speziell für die Verwaltung von WZ-Registrierungen entwickelt wurde.
- Meine Aufgabe ist es Anmeldungen kompfortabel zu gestalten, indem ich automatisierte Prozesse, Übersichten und Ausdrücke bereitstelle.
- Ich stehe unter der MIT-Lizenz, was bedeutet, dass du mich kostenlos nutzen, modifizieren und weiterverbreiten kannst, solange du die ursprünglichen Urheberrechtsvermerke und Lizenzhinweise beibehältst.
- Meine Github-Seite ist öffentlich zugänglich, und ich lade alle ein, die interessiert sind, den Code zu überprüfen, Fehler zu melden oder sogar zum Projekt beizutragen.
  - [HmWZ GitHub Repository](https://github.com/Ps394/HsBot)
            """
        await interaction.response.send_message(f"{MESSAGES.format(Botname=self.bot.user.name)}", ephemeral=ephemeral)




