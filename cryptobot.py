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
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=USD&order=market_cap_desc&price_change_percentage=1h%2C24h%2C7d").json()
        last_crypto_update = datetime.now()
        for c in crypto_list:
            prices = {"USD": c["current_price"]}
            for rate in rates:
                prices[rate] = float(c["current_price"]) * rates[rate]
            c["rank"] = crypto_list.index(c) + 1
            c["prices"] = prices
            c["percent_change_1h"] = formatPercentage(c["price_change_percentage_1h_in_currency"])
            c["percent_change_24h"] = formatPercentage(c["price_change_percentage_24h_in_currency"])
            c["percent_change_7d"] = formatPercentage(c["price_change_percentage_7d_in_currency"])
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
        if value > 0:
            output += "+"
        return output + "{:.2f}".format(value) + "%"
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
    print('------')


@bot.command()
async def ticker(ctx, crypto: str, currency="USD"):
    """Posts a ticker message with details about the crypto"""
    info = getTicker(crypto, currency.lower())
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
                                                                                                                                   info["percent_change_24h"], info["percent_change_7d"]), colour=0x00FF00, timestamp=datetime.strptime(info["last_updated"], "%Y-%m-%dT%H:%M:%S.%fZ"))
            await ctx.send(embed=em)
        else:
            await ctx.send("I couldn't find a currency called: {}".format(currency))
    else:
        await ctx.send("I couldn't find a crypto called: {}".format(crypto))


@ticker.error
async def ticker_error(ctx, error):
    """Posts an error message in case of an error with the ticker method."""
    print(error)
    if isinstance(error, commands.UserInputError):
        await ctx.send("Invalid input.")
    else:
        await ctx.send("Oops, something bad happened..")


@bot.command()
async def convert(ctx, value: float, _from: str, _to: str):
    """Converts a crypto to a crypto or a currency"""
    price_from = getPriceValue(_from.upper())
    price_to = getPriceValue(_to.upper())
    if value is not None and price_from is not None and price_to is not None:
        if price_to[0] == 0:
            total = value * (price_from[1] / price_to[1])
        else:
            total = value * (price_from[1] * price_to[1])
        await ctx.send("{} {} is the same as {} {}".format(roundValue(value), _from.upper(), roundValue(total), _to.upper()))


@convert.error
async def convert_error(ctx, error):
    """Posts an error message in case of an error with the convert method."""
    print(error)
    if isinstance(error, commands.UserInputError):
        await ctx.send("Invalid input.")
    else:
        await ctx.send("Oops, something bad happened..")


@bot.command()
async def source(ctx):
    """Posts a link to the bot GitHub page."""
    await ctx.send("The source can be found here: " +
                   "https://github.com/FrederikBolding/CryptoBot")

bot.run(token)
