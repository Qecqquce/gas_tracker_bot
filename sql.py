import sqlite3
import asyncio


async def create_db():
    with sqlite3.connect('gas_db.sqlite') as conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users_gas_alert'
                    '(id INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'alert_gas_price INTEGER,'
                    'chat_id INTEGER)')
        conn.commit()


async def add_gas_price(alert_gas_price, chat_id):
    with sqlite3.connect('gas_db.sqlite') as conn:
        cur = conn.cursor()

        cur.execute("SELECT chat_id FROM users_gas_alert WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()

        if row:
            cur.execute("UPDATE users_gas_alert SET alert_gas_price = ?"
                        "WHERE chat_id = ?", (alert_gas_price, chat_id))
            conn.commit()
        else:
            cur.execute("INSERT INTO users_gas_alert (alert_gas_price,"
                        "chat_id) VALUES (?, ?)", (alert_gas_price, chat_id))
            conn.commit()


async def check_gas_price(average_gas_price):
    with sqlite3.connect('gas_db.sqlite') as conn:
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users_gas_alert WHERE alert_gas_price >= ?", (average_gas_price,))
        rows = cur.fetchall()
        print(rows)
        return rows
