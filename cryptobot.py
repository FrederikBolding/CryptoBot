import configparser
import os
import requests

import discord
from discord.ext import commands
import random


def getTicker(crypto, currency):
    if currency == "":
        currency = "USD"
    crypto_list = requests.get(
        "https://api.coinmarketcap.com/v1/ticker/?convert=" + currency.upper()).json()
    crypto_dict = {}
    for c in crypto_list:
        crypto_dict[c["symbol"].upper()] = c
    return crypto_dict[crypto.upper()]


config = configparser.ConfigParser()
print("Reading config..")
config.read('config.ini')

if config["DEFAULT"]:
    token = config["DEFAULT"]["token"]
elif os.environ.get("token", None):
    token = os.environ["token"]
else:
    print("No config file found :(")
    raise ValueError("Missing config/token")


description = '''A bot that helps you keep track of the latest in crypto.'''
bot = commands.Bot(command_prefix='.', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.group(pass_context=True)
async def crypto(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say('Oops, thats an invalid command!')


@crypto.command()
async def ticker(*, args: str):
    """Posts a ticker message with details about the crypto"""
    a = args.split(" ")
    currency = "USD"
    if len(a) > 1:
        currency = a[1]
        info = getTicker(a[0], a[1])
    elif len(a) == 1:
        info = getTicker(a[0], currency)
    await bot.say(info["name"] + " (" + info["symbol"] + ") is currently priced at " + info["price_" + currency.lower()] + " " + currency.upper() + ".")


@crypto.command()
async def source():
    """Posts a link to the bot GitHub page."""
    await bot.say("The source can be found here: https://github.com/FrederikBolding/CryptoBot")

bot.run(token)
