import ast
import asyncio
import collections
import aioredis
import datetime as date
import json
import logging
import pathlib
from datetime import timedelta

import aiohttp
import discord
from discord.ext import commands

from . import config
from .Context import Context

#from .database import init_db
#from .Database import Connector as DatabaseConnector
# from .Utils import Infractions, Logging
# from discord_slash import SlashCommand, SlashContext

log = logging.getLogger("NotABot")

async def get_extensions():

    found = ["jishaku","safety.Cogs"]

    return found

def mentions():

    return discord.AllowedMentions(everyone=False, roles=False, users=False)


def intents():

    needed = [
        "messages",
        "guilds",
        "members",
        "guild_messages",
        "reactions",
        "dm_messages",
        "dm_reactions",
        "voice_states",
        "presences",
        "bans",
    ]

    intents = discord.Intents.none()

    for name in needed:
        setattr(intents, name, True)

    return intents



async def get_pre(bot, message):

    return commands.when_mentioned_or(config.PREFIX)(bot, message)
    # ^^ Enable if anything goes wrong with per-server prefixes.


    # if not message.guild:
    #     return commands.when_mentioned_or(config.PREFIX)(bot, message)
    # try:
    #     guild_prefix = bot.configs[message.guild.id]['prefixes']
    #     if guild_prefix:
    #         return commands.when_mentioned_or(*guild_prefix)(bot, message)
    # except KeyError:
    #     return commands.when_mentioned_or(config.PREFIX)(bot, message)


def start_session(bot):

    return aiohttp.ClientSession(loop=bot.loop)

class SafetyJim(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=get_pre,
            case_insensitive=True,
            reconnect=True,
            status=discord.Status.online,
            intents=intents(),
            allowed_mentions=mentions(),
            shard_id=0,
            shard_count=1,
        )

        self.pool = None
        self.session = None
        self.redis = None
        self.config = config
        self.configs = {}
        self.cases = collections.defaultdict(lambda: 0)
        self.prefixes = {}
        self._batch_lock = asyncio.Lock(loop=self.loop)
        self._data_batch = []
        self.messages_seen = 0
        self.bot_messages_seen = 0
        self.self_messages = 0
        self.commands_used = 0
        self.started_at = date.datetime.utcnow()
        self.bot_config = dict()
        self.backup_cache = dict()
        self.active_cache = dict()
        self.acting_on_active = False
        self.locked_channels = dict()
        self.next_ban_wave = date.datetime.utcnow() + timedelta(hours=1)
        # self.slash = SlashCommand(self, override_type=True, sync_on_cog_reload=True, sync_commands=True)
    
    async def start(self):
        self.session = start_session(self)

        await super().start(config.TOKEN)

    async def on_ready(self):
        self.redis = await aioredis.create_redis_pool("redis://localhost", loop=self.loop)
        self.guild = self.get_guild(config.MAIN_SERVER)
        self.global_ban_logs = self.guild.get_channel(config.GLOBAL_BAN_LOGS)
        
        for name in await get_extensions():
            self.load_extension(name)

        print("Online....................")

    async def process_commands(self, message):

        ctx = await self.get_context(message, cls=Context)
        if ctx.command is None:
            return
        
        self.commands_used += 1
        await self.invoke(ctx)

    async def get_or_fetch_member(self, guild, member_id):
        member = guild.get_member(member_id)
        if member is not None:
            return member

        shard = self.get_shard(guild.shard_id)
        if shard.is_ws_ratelimited():
            try:
                member = await guild.fetch_member(member_id)
            except discord.HTTPException:
                return None
            else:
                return member

        members = await guild.query_members(limit=1, user_ids=[member_id], cache=True)
        if not members:
            return None
        return members[0]


if __name__ == "__main__":
    SafetyJim().run()
