from Logger import logger
from typing import Optional, Union
from discord import Guild, TextChannel, Message, Member, Role, NotFound, Forbidden, HTTPException

__all__ = [
    "NotFound",
    "Forbidden",
    "HTTPException",
    "fetch_channel",
    "fetch_message",
    "fetch_member",
    "fetch_role"
]

async def fetch_channel(guild: Guild, channel_id: int, classname: Optional[str]=None) -> Union[Optional[TextChannel], Exception]:
    try:
        if classname:
            classname = f"{classname} - "
        else:
            classname = ""
        if channel_id is None:
            logger.debug(f"{classname}{guild.name} ({guild.id}) - Channel ID is None, cannot fetch.")
            return None
        channel = await guild.fetch_channel(channel_id)
        if isinstance(channel, TextChannel):
            return channel
        else:
            logger.debug(f"{classname}{guild.name} ({guild.id}) - Channel {channel_id} is not a text channel.")
            return None
    except (TypeError, NotFound) as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Channel {channel_id} fetched failure: Not a text channel or channel not found.")
        return e
    except Forbidden as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Channel {channel_id} fetched failure: Forbidden")
        return e
    except HTTPException as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Channel {channel_id} fetched failure: {e}")
        return e
    
async def fetch_message(channel: TextChannel, message_id: int, classname: Optional[str]=None) -> Union[Optional[Message], Exception]:
    try:
        if classname:
            classname = f"{classname} - "
        else:
            classname = ""
        if message_id is None:
            logger.debug(f"{classname}{channel.guild.name} ({channel.guild.id}) - Message ID is None, cannot fetch.")
            return None
        return await channel.fetch_message(message_id)
    except NotFound as e:
        logger.debug(f"{classname}{channel.guild.name} ({channel.guild.id}) - Message {message_id} fetched failure: Not found")
        return e
    except Forbidden as e:
        logger.debug(f"{classname}{channel.guild.name} ({channel.guild.id}) - Message {message_id} fetched failure: Forbidden")
        return e
    except HTTPException as e:
        logger.debug(f"{classname}{channel.guild.name} ({channel.guild.id}) - Message {message_id} fetched failure: {e}")
        return e
    
async def fetch_member(guild: Guild, member_id: int, classname: Optional[str]=None) -> Union[Optional[Member], Exception]:
    try:
        if classname:
            classname = f"{classname} - "
        else:
            classname = ""
        if member_id is None:
            logger.debug(f"{classname}{guild.name} ({guild.id}) - Member ID is None, cannot fetch.")
            return None
        return await guild.fetch_member(member_id)
    except NotFound as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Member {member_id} fetched failure: Not found")
        return e
    except Forbidden as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Member {member_id} fetched failure: Forbidden")
        return e
    except HTTPException as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Member {member_id} fetched failure: {e}")
        return e
    
async def fetch_role(guild: Guild, role_id: int, classname: Optional[str]=None) -> Union[Optional[Role], Exception]:
    try:
        if classname:
            classname = f"{classname} - "
        else:
            classname = ""
        if role_id is None:
            logger.debug(f"{classname}{guild.name} ({guild.id}) - Role ID is None, cannot fetch.")
            return None
        return guild.get_role(role_id)
    except NotFound as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Role {role_id} fetched failure: Not found")
        return e
    except Forbidden as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Role {role_id} fetched failure: Forbidden")
        return e
    except HTTPException as e:
        logger.debug(f"{classname}{guild.name} ({guild.id}) - Role {role_id} fetched failure: {e}")
        return e