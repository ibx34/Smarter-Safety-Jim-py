import logging
import re
import typing
from textwrap import dedent

import discord
from discord.ext import commands
from unidecode import unidecode

from .. import Plugin
from ..Util.Formats import prompt
from ..Util.Time import human_timedelta

log = logging.getLogger(__name__)


def can_execute_action(ctx, user, target):
    return (
        user.id == ctx.bot.owner_id
        or user == ctx.guild.owner
        or user.top_role > target.top_role
    )


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)
        if entity is None:
            raise commands.BadArgument(
                f"{ctx.author.mention} -> That user wasn't previously banned..."
            )
        return entity


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(
                    f"{argument} is not a valid member or member ID."
                ) from None
            else:
                m = await ctx.bot.get_or_fetch_member(ctx.guild, member_id)
                if m is None:
                    # hackban case
                    return type(
                        "_Hackban",
                        (),
                        {"id": member_id, "__str__": lambda s: f"Member ID {s.id}"},
                    )()

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument(
                "You cannot do this action on this user due to role hierarchy."
            )
        return m


class Reason(commands.Converter):
    async def convert(self, ctx, argument):
        reason = f"[{ctx.author}] {argument}"
        if len(reason) > 520:
            raise Exception(f"Your reason is too long. ({len(reason)}/512)")
        return reason


class Moderator(Plugin):
    @commands.command(name="lock", aliases=["cease", "killchat", "stop", "pause"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """
        Stop people from chatting in a channel. Useful for getting people's ids for punishments, or just getting people to stop talking.
        """
        channel = ctx.channel if channel is None else channel

        if self.bot.locked_channels.get(f"{ctx.guild.id}-{channel.id}"):
            return await ctx.no(
                f"There is already saved perms for {channel.mention}. Please run `%unlock {channel.id}` to remove it."
            )

        self.bot.locked_channels[
            f"{ctx.guild.id}-{channel.id}"
        ] = channel.overwrites_for(ctx.guild.default_role)
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=False, add_reactions=True
        )

        await ctx.yes(f"Locked {channel.mention}.")

    @commands.command(
        name="unlocK", aliases=["uncease", "unkillchat", "start", "continue"]
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """
        Reverts a previous channel lock. If you get "No saved permissions found for <channel>" this means the bot has no record of the channel being locked, and it cant be unlocked.
        """

        channel = ctx.channel if channel is None else channel

        perms = self.bot.locked_channels.get(f"{ctx.guild.id}-{channel.id}")
        if perms is None:
            return await ctx.no(f"No saved permissions found for {channel.mention}.")

        await channel.set_permissions(ctx.guild.default_role, overwrite=perms)

        await ctx.yes(f"Unlocked {channel.mention}.")
        del perms

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: MemberID, *, reason: Reason = None):
        """
        Ban a user who is in or not in your server. If the user is not in your server, use their id to ban them.
        """

        await ctx.guild.ban(user=user, delete_message_days=7, reason=reason)
        await ctx.yes(f"""Banned **{user}**""")

    @commands.command(name="unban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: BannedMember, *, reason: Reason = None):
        """
        Revokes a previous ban on a member. This will not unban the user on other servers, unlike globalunban.
        """

        await ctx.guild.unban(user.user, reason=reason)
        await ctx.yes(f"""Unbanned **{user.user.name}**#{user.user.discriminator}""")

    @commands.command(name="globalban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def globalban(self, ctx, user: discord.Member, *, reason: Reason = None):
        """
        Bans a user across all servers. If your reason is troll like, or a meme you will be banned from using the bot. This feature is meant to be serious, and only used for pretty severe circumstances.
        """

        confirm = await prompt(
            self=ctx,
            message=dedent(
                f"""{user} will be banned in {"over" if len(self.bot.guilds) > 1 else ""} {len(self.bot.guilds)} guilds."""
            ),
            author_id=ctx.author.id,
            reacquire=False,
        )

        if not confirm:
            return await ctx.send(
                f"Alright, **{user}** hasn't been banned. If you would like to ban them **in this server** use the normal ban command."
            )

        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.set_author(icon_url=ctx.guild.icon_url, name=f"New global ban:")
        embed.add_field(
            name="Moderator",
            value=f"**{ctx.author}** (`{ctx.author.id}`)\n<@{ctx.author.id}>",
        )
        embed.add_field(name="User", value=f"**{user}** (`{user.id}`)\n<@{user.id}>")
        embed.add_field(
            name="Server", value=f"**{ctx.guild}** (`{ctx.guild.id}`)", inline=False
        )
        embed.add_field(name="Reason", value=f"{reason}", inline=False)

        await self.bot.global_ban_logs.send(embed=embed)
        async with ctx.channel.typing():
            for x in self.bot.guilds:
                try:
                    await x.ban(
                        user, delete_message_days=7, reason=f"[GLOBAL BAN]: {reason}"
                    )
                except:
                    pass
        await ctx.yes(
            dedent(
                f"""**User**: {user} has been banned in {"over" if len(self.bot.guilds) > 1 else ""} {len(self.bot.guilds)} guilds."""
            )
        )
