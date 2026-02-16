from discord.app_commands import Group, checks
from . import Reset, Csv


__all__ = ["RegistrationGroup"]
checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
class RegistrationGroup(Group):
    def __init__(self):
        super().__init__(
            name="registration",
            description="Befehle für die WZ-Registrierung"
        )
        
        self.add_command(Reset.reset)
        self.add_command(Csv.csv)