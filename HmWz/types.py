from dataclasses import dataclass, field
from typing import Union, Optional, Sequence, Tuple, List, Callable
from discord import Guild, Member, Role, TextChannel, Message

__all__ = ("dataclass", "Union", "Optional", "Sequence", "Tuple", "List", "Guild", "Member", "Role", "TextChannel", "Message")

type Id = int
"""
Type-Alias für die id von Discord-Objekten 

:type id: int
"""
type Ids = Tuple[Id, ...]

type DiscordMember = Union[Member, int]
"""Representiert ein Discord-Mitglied, entweder als Member-Objekt oder als ID (int). Kann auch None sein, wenn kein Mitglied vorhanden ist."""
type DiscordRole = Union[Role, int]
"""Representiert eine Discord-Rolle, entweder als Role-Objekt oder als ID (int). Kann auch None sein, wenn keine Rolle vorhanden ist."""
type DiscordChannel = Union[TextChannel, int]
"""Representiert einen Discord-Kanal, entweder als TextChannel-Objekt oder als ID (int). Kann auch None sein, wenn kein Kanal vorhanden ist."""
type DiscordMessage = Union[Message, int]
"""Representiert eine Discord-Nachricht, entweder als Message-Objekt oder als ID (int). Kann auch None sein, wenn keine Nachricht vorhanden ist."""
