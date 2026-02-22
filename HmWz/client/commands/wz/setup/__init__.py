from discord.app_commands import Group, checks, default_permissions

from . import configure, message, roles

__all__ = ["SetupGroup"]

@checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@default_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
class SetupGroup(Group):
    def __init__(self):
        super().__init__(
            name="setup",
            description="Setup-Befehle für die WZ-Registrierung"
        )
        
        self.add_command(configure.configure)
        self.add_command(message.message)
        self.add_command(roles.add.add)
        self.add_command(roles.remove.remove)
        