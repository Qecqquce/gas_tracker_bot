import aiohttp
import os
import telegram
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    ConversationHandler,
    MessageHandler
)

from dotenv import load_dotenv
from sql import create_db, add_gas_price

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ETHERSCAN_API = os.getenv('ETHERSCAN_API')
ETHER_PRICE_URL = (f'https://api.etherscan.io/api?module='
                   f'stats&action=ethprice&apikey={ETHERSCAN_API}')

CHOOSING, TYPING_VALUE = range(2)


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = telegram.ReplyKeyboardMarkup([['/eth_alert'],
                                            ['/get_eth_price']],
                                            resize_keyboard=True)
    await create_db()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot!",
                                   reply_markup=keyboard)


async def get_eth_price(update: telegram.Update,
                        context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        async with session.get(ETHER_PRICE_URL) as resp:
            data = await resp.json()
            eth_price = data['result']['ethusd']
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=eth_price)


async def eth_alert(update: telegram.Update,
                    context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter a value in 'int' format:")
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
            await update.message.reply_text("Invalid value.")


def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    eth_alert_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("eth_alert", eth_alert)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT, received_value)],
        },
        fallbacks=[CommandHandler("cancel", ConversationHandler.END)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("get_eth_price", get_eth_price))
    application.add_handler(eth_alert_conversation_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
