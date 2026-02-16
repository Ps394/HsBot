from discord.app_commands import Group, checks, default_permissions

from . import Configure, Roles, Message

__all__ = ["SetupGroup"]

@checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
@default_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
class SetupGroup(Group):
    def __init__(self):
        super().__init__(
            name="setup",
            description="Setup-Befehle für die WZ-Registrierung"
        )
        
        self.add_command(Configure.configure)
        self.add_command(Message.message)
        self.add_command(Roles.add)
        self.add_command(Roles.remove)
        