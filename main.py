import aiohttp
import logging
import os
import time
import asyncio
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram import Update
import telegram
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ETHERSCAN_API = os.getenv('ETHERSCAN_API')
GAS_PRICE_URL = (f'https://api.etherscan.io/api?module=gastracker'
                 f'&action=gasoracle&apikey={ETHERSCAN_API}')
ETHER_PRICE = (f'https://api.etherscan.io/api?module=stats&action=ethprice&apikey={ETHERSCAN_API}')
GWEI = 1000000000
GAS = 21000

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s -'
                              '%(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(filename="logger.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def check_tokens():
    """CHECK THAT THE ENVIRONMENT VARIABLES ARE AVAILABLE."""
    tokens = ['TELEGRAM_TOKEN']
    missing_tokens = [key for key in tokens if not globals().get(key)]
    if missing_tokens:
        logger.critical(f'Отсутствует переменная окружения! {missing_tokens}')
        raise SystemExit('Проверь токены!')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = telegram.ReplyKeyboardMarkup([['/get_gas_price'],
                                             ['/get_eth_price']])
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot!",
                                   reply_markup=keyboard)


async def get_eth_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        async with session.get(ETHER_PRICE) as resp:
            data = await resp.json()
            eth_price = data['result']['ethusd']
            eth_price_text = f'{eth_price} $'
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=eth_price_text)


async def get_gas_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        async with session.get(GAS_PRICE_URL) as resp:
            data = await resp.json()
            slowgasprice = int(data['result']['SafeGasPrice'])
            averagegasprice = int(data['result']['ProposeGasPrice'])
            fastgasprice = int(data['result']['FastGasPrice'])
            slow_usd_price = gas_price_to_usd(slowgasprice,  1800)
            average_usd_price = gas_price_to_usd(averagegasprice,  1800)
            fast_usd_price = gas_price_to_usd(fastgasprice,  1800)

            gas_prices_text = (f"Slow: {slowgasprice} gwei {round(slow_usd_price, 2)}$\n\n"
                               f"Average: {averagegasprice} gwei {round(average_usd_price, 2)}$\n\n"
                               f"Fast: {fastgasprice} gwei {round(fast_usd_price, 2)}$")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=gas_prices_text)


def gas_price_to_usd(gwei, eth_price):
    usd_price = gwei/GWEI*GAS*eth_price
    return usd_price


def main():
    check_tokens()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("get_gas_price", get_gas_price))
    application.add_handler(CommandHandler("get_eth_price", get_eth_price))
    application.run_polling()


if __name__ == '__main__':
    main()
