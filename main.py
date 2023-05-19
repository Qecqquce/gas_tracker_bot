import aiohttp
import logging
import os
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram import Update
import telegram
from dotenv import load_dotenv
import time
import asyncio


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ETHERSCAN_API = os.getenv('ETHERSCAN_API')
GAS_PRICE_URL = (f'https://api.etherscan.io/api?module=gastracker'
                 f'&action=gasoracle&apikey={ETHERSCAN_API}')
ETHER_PRICE_URL = (f'https://api.etherscan.io/api?'
                   f'module=stats&action=ethprice&apikey={ETHERSCAN_API}')
GWEI_IN_ETH = 1000000000
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
    keyboard = telegram.ReplyKeyboardMarkup([['/get_gas_price']],
                                            resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot!",
                                   reply_markup=keyboard)


async def get_eth_price(session):
    logger.info('start get_eth_price')
    async with session.get(ETHER_PRICE_URL) as resp:
        logger.info('2 get_eth_price')
        data = await resp.json()
        logger.info('3 get_eth_price')
        eth_price = data['result']['ethusd']
        logger.info('end get_eth_price')
        return eth_price


async def get_gas_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info('start get_gas_price')
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        eth_price_task = asyncio.create_task(get_eth_price(session))
        logger.info('1 get_gas_price')
        async with session.get(GAS_PRICE_URL) as resp:
            logger.info('2 get_gas_price')
            data = await resp.json()
            logger.info('3 get_gas_price')
            logger.info('4 get_gas_price')
            slow_gwei_price = int(data['result']['SafeGasPrice'])
            average_gwei_price = int(data['result']['ProposeGasPrice'])
            fast_gwei_price = int(data['result']['FastGasPrice'])

            slow_usd_price = await gas_price_to_usd(slow_gwei_price,
                                                    eth_price_task.result())
            logger.info('5 get_gas_price')
            average_usd_price = await gas_price_to_usd(average_gwei_price,
                                                       eth_price_task.result())

            fast_usd_price = await gas_price_to_usd(fast_gwei_price,
                                                    eth_price_task.result())
            elapsed_time = time.time() - start_time
            gas_prices_text = (
                f'Ethereum price {eth_price_task.result()}$\n\n'
                f'Slow: {slow_gwei_price} gwei {round(slow_usd_price, 2)}$\n\n'
                f'Average: {average_gwei_price} '
                f'gwei {round(average_usd_price, 2)}$\n\n'
                f'Fast: {fast_gwei_price} gwei {round(fast_usd_price, 2)}$\n\n'
                f'Elapsed time: {elapsed_time} seconds'
                )
            logger.info('end get_gas_price')
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=gas_prices_text)


async def gas_price_to_usd(gwei, eth_price):
    logger.info('start gas_price_to_usd')
    eth_price = float(eth_price)
    usd_price = gwei/GWEI_IN_ETH*GAS*eth_price
    logger.info('end gas_price_to_usd')
    return usd_price


def main():
    check_tokens()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("get_gas_price", get_gas_price))
    application.run_polling()


if __name__ == '__main__':
    main()
