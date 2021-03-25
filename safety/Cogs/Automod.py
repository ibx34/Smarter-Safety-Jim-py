import logging
import re
import typing

import discord
from collections import defaultdict
from discord.ext import commands
from unidecode import unidecode

from .. import Plugin\

    
log = logging.getLogger(__name__)

class Automod(Plugin):
    def __init__(self,bot):
        self.bot = bot
