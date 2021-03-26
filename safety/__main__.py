import discord

from . import SafetyJim, setup_logging

discord.VoiceClient.warn_nacl = False

with setup_logging():
    SafetyJim().run()
