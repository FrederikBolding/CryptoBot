import configparser
import os
import datetime
from datetime import datetime
from datetime import timedelta
import requests

import discord
from discord.ext import commands
from forex_python.converter import CurrencyRates


def getTicker(crypto, currency):
    now = datetime.now()
    global last_crypto_update
    diff = now - last_crypto_update
    minutes = diff / timedelta(minutes=1)
    if minutes > minutesBetweenUpdates:
        print("Information was too old, getting new info..")
        if currency == "":
            currency = "USD"
        crypto_list = requests.get(
            "https://api.coinmarketcap.com/v1/ticker/").json()
        last_crypto_update = datetime.now()
        for c in crypto_list:
            prices = {"USD": c["price_usd"]}
            for rate in rates:
                prices[rate] = float(c["price_usd"]) * rates[rate]
            c["prices"] = prices
            crypto_dict[c["symbol"].upper()] = c
    return crypto_dict[crypto.upper()]


def formatPercentage(value):
    output = ""
    if float(value) > 0:
        output += "+"
    return output + value + "%"


config = configparser.ConfigParser()
print("Reading config..")
config.read('config.ini')

if config["DEFAULT"]:
    token = config["DEFAULT"]["token"]
elif os.environ.get("token", None):
    token = os.environ["token"]
else:
    print("No config/token found :(")
    raise ValueError("Missing config/token")

crypto_dict = {}
currency_rates = CurrencyRates()
print("Getting currency rates..")
rates = currency_rates.get_rates("USD")
minutesBetweenUpdates = 5
last_crypto_update = datetime.min


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
    await bot.say(info["name"] + " (" + info["symbol"] + ") is currently priced at " + str(info["prices"][currency.upper()]) + " " + currency.upper() + ".\n\nThe price has changed with: " + formatPercentage(info["percent_change_1h"]) + " in the last hour, " + formatPercentage(info["percent_change_24h"]) + " in the last 24 hours, and " + formatPercentage(info["percent_change_7d"]) + " in the last 7 days.\n\nData from: <https://coinmarketcap.com/> - Last Updated: " + datetime.fromtimestamp(int(info["last_updated"])).strftime('%Y-%m-%d %H:%M:%S'))


@crypto.command()
async def source():
    """Posts a link to the bot GitHub page."""
    await bot.say("The source can be found here: https://github.com/FrederikBolding/CryptoBot")

bot.run(token)
