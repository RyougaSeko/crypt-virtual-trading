from app import calc_profit, user_id, user_lit_factory, db
import sqlite3
from datetime import datetime
import schedule
import time
import asyncio

async def load_profit(user_id):
    while True:
        #ユーザーのprofitを計算
        profit = calc_profit(user_id)

        #profit, id, dateをprofitテーブルに追加
        con = sqlite3.connect(db, check_same_thread=False)
        #出力結果を辞書形式のリストで扱えるように
        con.row_factory = user_lit_factory

        cur = con.cursor()
        cur.execute("INSERT INTO profit (id, date, profit) VALUES(?, ?, ?)", (user_id, datetime.now(), profit,))
        
        con.commit()
        print(profit)

        await asyncio.sleep(10)

#ループの実行
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(load_profit(user_id=user_id))