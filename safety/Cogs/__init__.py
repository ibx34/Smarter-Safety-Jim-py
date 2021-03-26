from . import Misc, Moderator, Automod


def setup(bot):
    for cls in (Misc.Misc, Moderator.Moderator, Automod.Automod):
        bot.add_cog(cls(bot))
