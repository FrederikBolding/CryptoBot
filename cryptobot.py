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
    if value:
        output = ""
        if float(value) > 0:
            output += "+"
        return output + value + "%"
    return "null"


def roundValue(value):
    value = float(value)
    if value >= 1:
        return round(value, 2)
    else:
        return value


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
    print("I am a member of " + str(len(bot.servers)) + " server(s)")
    print('------')


@bot.command()
async def ticker(*, args: str):
    """Posts a ticker message with details about the crypto"""
    bot.type()
    a = args.split(" ")
    currency = "USD"
    if len(a) > 1:
        currency = a[1]
        info = getTicker(a[0], a[1])
    elif len(a) == 1:
        info = getTicker(a[0], currency)

    currency = currency.upper()

    if info:
        if currency in info["prices"]:
            em = discord.Embed(title='{} ({}-{})'.format(info["name"], info["symbol"], currency),
                               description="""
                               **Ranked:** #{}
                               \n**Current price:** {} {}
                               \n**Price changes**:\n{} in the past hour\n{} in the past 24 hours\n{} in the past 7 days""".format(info["rank"],
                                                                                                                                   str(roundValue(
                                                                                                                                       info["prices"][currency])),
                                                                                                                                   currency, info[
                                                                                                                                       "percent_change_1h"],
                                                                                                                                   info["percent_change_24h"], info["percent_change_7d"]), colour=0x00FF00, timestamp=datetime.fromtimestamp(int(info["last_updated"])))
            await bot.say(embed=em)
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
    bot.type()
    a = args.split(" ")
    value = float(a[0])
    price_from = getPriceValue(a[1].upper())
    price_to = getPriceValue(a[2].upper())
    if value is not None and price_from is not None and price_to is not None:
        if price_to[0] == 0:
            total = value * (price_from[1] / price_to[1])
        else:
            total = value * (price_from[1] * price_to[1])
        await bot.say("{} {} is the same as {} {}".format(roundValue(value), a[1].upper(), roundValue(total), a[2].upper()))


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
