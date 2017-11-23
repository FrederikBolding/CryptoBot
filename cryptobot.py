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
            c["percent_change_1h"] = formatPercentage(c["percent_change_1h"])
            c["percent_change_24h"] = formatPercentage(c["percent_change_24h"])
            c["percent_change_7d"] = formatPercentage(c["percent_change_7d"])
            crypto_dict[c["symbol"].upper()] = c
    if crypto.upper() in crypto_dict:
        return crypto_dict[crypto.upper()]
    else:
        return None


def getPriceValue(name):
    ticker = getTicker(name, "USD")
    if ticker:
        return (0, float(ticker["prices"]["USD"]))
    elif name in rates:
        return (1, float(rates[name]))
    return None


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
bot = commands.Bot(command_prefix='.crypto ', description=description)


@bot.event
async def on_ready():
    """Event called when the bot is ready"""
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def ticker(*, args: str):
    """Posts a ticker message with details about the crypto"""
    a = args.split(" ")
    currency = "USD"
    if len(a) > 1:
        currency = a[1]
        info = getTicker(a[0], a[1])
    elif len(a) == 1:
        info = getTicker(a[0], currency)

    if info:
        if currency.upper() in info["prices"]:
            await bot.say("""{} ({}) is currently priced at {} {}.\n\nThe price has changed by: {} in the past hour, {} in the past 24 hours, and {} in the past 7 days.\n\nData from: <https://coinmarketcap.com/> - Last updated at: {}"""
                          .format(info["name"], info["symbol"],
                                  str(info["prices"][currency.upper()]),
                                  currency.upper(), info["percent_change_1h"],
                                  info["percent_change_24h"], info["percent_change_7d"],
                                  datetime.fromtimestamp(int(info["last_updated"])).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            await bot.say("I couldn't find a currency called: {}".format(currency))
    else:
        await bot.say("I couldn't find a crypto called: {}".format(a[0]))


@ticker.error
async def ticker_error(error, ctx):
    """Posts an error message in case of an error with the ticker method."""
    print(error)
    if isinstance(error, commands.UserInputError):
        await bot.say("Invalid input.")
    else:
        await bot.say("Oops, something bad happened..")


@bot.command()
async def convert(*, args: str):
    """Converts a crypto to a crypto or a currency"""
    a = args.split(" ")
    value = float(a[0])
    price_from = getPriceValue(a[1].upper())
    price_to = getPriceValue(a[2].upper())
    if value is not None and price_from is not None and price_to is not None:
        if price_to[0] == 0:
            total = value * (price_from[1] / price_to[1])
        else:
            total = value * (price_from[1] * price_to[1])
        await bot.say("{} {} is the same as {} {}".format(value, a[1].upper(), total, a[2].upper()))


@convert.error
async def convert_error(error, ctx):
    """Posts an error message in case of an error with the convert method."""
    print(error)
    if isinstance(error, commands.UserInputError):
        await bot.say("Invalid input.")
    else:
        await bot.say("Oops, something bad happened..")


@bot.command()
async def source():
    """Posts a link to the bot GitHub page."""
    await bot.say("The source can be found here: " +
                  "https://github.com/FrederikBolding/CryptoBot")

bot.run(token)
