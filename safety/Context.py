from discord.ext import commands
import discord


class Context(commands.Context):
    async def send(self, content=None, *, embed=None, **kwargs):
        if embed is not None:
            if embed.color is None:
                embed.color = discord.Color.blurple()

        return await super().send(content, embed=embed, **kwargs)

    async def yes(self, content=None, *, embed=None, **kwargs):

        return await super().send(
            "<:greenTick:823666563826843649> " + content, embed=embed, **kwargs
        )

    async def no(self, content=None, *, embed=None, **kwargs):

        return await super().send(
            "<:no:823666563462856716> " + content, embed=embed, **kwargs
        )

    async def eh(self, content=None, *, embed=None, **kwargs):

        return await super().send(
            "<:eh:823666563957260299> " + content, embed=embed, **kwargs
        )
