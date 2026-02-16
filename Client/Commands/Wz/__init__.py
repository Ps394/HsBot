from discord.app_commands import Group, checks
from . import Setup, Registration
from ..Registry import register

__all__ = [
    "WzGroup"
]

@register
@checks.bot_has_permissions(manage_roles=True, manage_channels=True, view_channel=True, send_messages=True, read_message_history=True, attach_files=True)
class WzGroup(Group):
    def __init__(self, bot):
        super().__init__(
            name="wz", 
            description="Alle Befehle rund um die WZ-Registrierung"
        )

        self.bot = bot

        self.add_command(Setup.SetupGroup())
        self.add_command(Registration.RegistrationGroup())    





