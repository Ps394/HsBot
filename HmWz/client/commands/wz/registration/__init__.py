from discord.app_commands import Group, checks, locale_str
from . import reset, csv
from .....i18n import CommandLocalizations


__all__ = ["RegistrationGroup"]
checks.has_permissions(manage_roles=True, manage_messages=True, manage_channels=True)
class RegistrationGroup(Group):
    def __init__(self):
        super().__init__(
            name="registration",
            description=locale_str(
                CommandLocalizations.get("en", {}).get("wz.registration.group.description", "Registration Commands"),
                key="wz.registration.group.description"
            )
        )
        
        self.add_command(reset.reset)
        self.add_command(csv.csv)