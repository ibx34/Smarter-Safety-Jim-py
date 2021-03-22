from discord.ext import commands


class Plugin(commands.Cog):
    def __init__(self, notabot):
        self.notabot = notabot