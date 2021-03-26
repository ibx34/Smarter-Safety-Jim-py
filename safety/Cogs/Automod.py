import logging
import re
import typing

import discord
from collections import defaultdict
from discord.ext import commands
from unidecode import unidecode

from .. import Plugin
from ..files.badwords import list


log = logging.getLogger(__name__)


class Automod(Plugin):
    def __init__(self, bot):
        self.bot = bot

    @Plugin.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        check = re.search(
            r"((https?:\/\/)?discord\.gg\/)|((https?:\/\/)?discord\.com\/invite\/)|((https?:\/\/)?discordapp\.com\/invite\/)|((https?:\/\/)?staging-invite\.discord\.co\/)([a-zA-Z0-9\-]+)",
            message.content,
        )

        for word in list:
            if word.lower() in message.content.lower():
                await message.delete()
                return await message.channel.send(
                    f"<:no:823666563462856716> {message.author.mention} Do not use that words here. (`{''.join(['*' for _ in range(len(message.content))])}`)"
                )

        if check:
            await message.delete()
            return await message.channel.send(
                f"<:no:823666563462856716> {message.author.mention} You're not allowed to send invites here."
            )

        user_mentions = message.raw_mentions
        role_mentions = message.raw_role_mentions

        if len(user_mentions) > 5:
            await message.delete()
            return await message.channel.send(
                f"<:no:823666563462856716> {message.author.mention} Spamming mentions (users) in a message, is not allowed."
            )

        if len(role_mentions) > 5:
            await message.delete()
            return await message.channel.send(
                f"<:no:823666563462856716> {message.author.mention} Spamming mentions (roles) in a message, is not allowed."
            )
