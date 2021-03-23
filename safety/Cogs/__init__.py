
from . import Misc, Moderator

def setup(bot):
    for cls in (Misc.Misc,Moderator.Moderator):
        bot.add_cog(cls(bot))