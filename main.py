import aiohttp
from logger import logger
import os
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    ConversationHandler,
    MessageHandler)

import telegram
from dotenv import load_dotenv
import asyncio
from sql import create_db, add_gas_price, check_gas_price

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ETHERSCAN_API = os.getenv('ETHERSCAN_API')
GAS_PRICE_URL = (f'https://api.etherscan.io/api?module=gastracker'
                 f'&action=gasoracle&apikey={ETHERSCAN_API}')
ETHER_PRICE_URL = (f'https://api.etherscan.io/api?'
                   f'module=stats&action=ethprice&apikey={ETHERSCAN_API}')

GWEI_IN_ETH = 1000000000
GAS = 21000
CHOOSING, TYPING_VALUE = range(2)


def check_tokens():
    """CHECK THAT THE ENVIRONMENT VARIABLES ARE AVAILABLE."""
    tokens = ['TELEGRAM_TOKEN', 'ETHERSCAN_API']
    missing_tokens = [key for key in tokens if not globals().get(key)]
    if missing_tokens:
        logger.critical(f'Отсутствует переменная окружения! {missing_tokens}')
        raise SystemExit('Проверь токены!')


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = telegram.ReplyKeyboardMarkup([['/get_gas_price'],
                                             ['/gas_alert']],
                                            resize_keyboard=True)
    await create_db()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Hi!",
                                   reply_markup=keyboard)


async def get_eth_price(session):
    async with session.get(ETHER_PRICE_URL) as resp:
        data = await resp.json()
        eth_price = data['result']['ethusd']
        return eth_price


async def gas_price(context: ContextTypes.DEFAULT_TYPE):

    global ETH_PRICE
    global SLOW_GWEI
    global AVERAGE_GWEI
    global FAST_GWEI
    global SLOW_IN_USD
    global AVERAGE_IN_USD
    global FAST_IN_USD

    async with aiohttp.ClientSession() as session:
        eth_price_task = asyncio.create_task(get_eth_price(session))
        async with session.get(GAS_PRICE_URL) as resp:
            data = await resp.json()
            ETH_PRICE = await eth_price_task
            SLOW_GWEI = int(data['result']['SafeGasPrice'])
            AVERAGE_GWEI = int(data['result']['ProposeGasPrice'])
            FAST_GWEI = int(data['result']['FastGasPrice'])

            SLOW_IN_USD = await gas_price_to_usd(SLOW_GWEI,
                                                 ETH_PRICE)
            AVERAGE_IN_USD = await gas_price_to_usd(AVERAGE_GWEI,
                                                    ETH_PRICE)

            FAST_IN_USD = await gas_price_to_usd(FAST_GWEI,
                                                 ETH_PRICE)


async def send_gas_price(update: telegram.Update,
                         context: ContextTypes.DEFAULT_TYPE):
    try:
        gas_prices_text = (
                    f'Ethereum price {ETH_PRICE}$\n\n'
                    f'Slow: {SLOW_GWEI} gwei {round(SLOW_IN_USD, 2)}$\n\n'
                    f'Average: {AVERAGE_GWEI} '
                    f'gwei {round(AVERAGE_IN_USD, 2)}$\n\n'
                    f'Fast: {FAST_GWEI} gwei {round(FAST_IN_USD, 2)}$\n\n'
                    )
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=gas_prices_text)
    except NameError:
        await update.message.reply_text("repeat pls")


async def gas_price_to_usd(gwei, eth_price):
    eth_price = float(eth_price)
    usd_price = gwei/GWEI_IN_ETH*GAS*eth_price
    return usd_price


async def gas_alert(update: telegram.Update,
                    context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter a value in 'int' format")
    return CHOOSING


async def received_value(update: telegram.Update,
                         context: ContextTypes.DEFAULT_TYPE):
    for i in range(1):
        try:
            alert_gas_price = int(update.message.text)
            chat_id = update.effective_chat.id
            await update.message.reply_text(f"Written: {alert_gas_price}")
            await add_gas_price(alert_gas_price, chat_id)
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("Error.Enter value in 'int'")


async def send_alert(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = await check_gas_price(AVERAGE_GWEI)
    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id[0],
                                       text=f'Gas price is {AVERAGE_GWEI} gwei'
                                       f' or {round(AVERAGE_IN_USD, 2)}$')


def main():
    check_tokens()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_repeating(callback=gas_price, interval=12, first=1)

    job_queue = application.job_queue
    job_queue.run_repeating(callback=send_alert, interval=60, first=2)

    gas_alert_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("gas_alert", gas_alert)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT, received_value)],
        },
        fallbacks=[CommandHandler("cancel", ConversationHandler.END)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("get_gas_price", send_gas_price))
    application.add_handler(gas_alert_conversation_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
