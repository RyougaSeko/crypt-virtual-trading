import os
import sys
from locale import currency
from pickle import FALSE
import profile
from symtable import Symbol
from unicodedata import name
import requests
import json
import pprint
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import schedule
import time
import asyncio


app = Flask(__name__)
# app.config['SECRET_KEY'] = os.urandom(24)

db = 'crypt_trading.db'
# login_manager = LoginManager()
# login_manager.init_app(app)

user_id = 1
symbol = 'btc_jpy'

pairs = ['btc_jpy', 'xrp_jpy', 'ltc_jpy', 'eth_jpy', 'mona_jpy', 'bcc_jpy', 'xlm_jpy', 'qtum_jpy', 'bat_jpy', 'omg_jpy', 'xym_jpy', 'link_jpy', 'mkr_jpy', 'boba_jpy', 'enj_jpy', 'matic_jpy', 'dot_jpy', 'doge_jpy']

def bubble_sort(user_li):
    for i in range(len(user_li)):
        for j in range(len(user_li) - i -1):
            if user_li[j]["profit"] > user_li[j+1]["profit"]: #左の方が大きい場合
                user_li[j], user_li[j+1] = user_li[j+1], user_li[j] #前後入れ替え

    return user_li

def calc_profit(user_id):

    con = sqlite3.connect(db, check_same_thread=False)
    cur = con.cursor()
    cash = cur.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
    cash = cash.fetchall()[0][0]
    user_own_crypt_li = fetch_user_own_crypt(user_id=user_id)

    con.commit()

    #profitを計算
    principal = 100000000
    valuation = 0
    for user_own_crypt in user_own_crypt_li:
        valuation += user_own_crypt["total"]

    profit = (valuation + cash) - principal

    return profit


def can_buy_amount(symbol):

    con = sqlite3.connect(db, check_same_thread=False)
    cur = con.cursor()
    cash = cur.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
    cash = cash.fetchall()[0][0]

    unit_price = int(fetch_recent_crypt_info(symbol))

    amount = str(cash / unit_price).split(".")
    fraction = amount[1]

    if len(fraction) > 4:
        fraction = fraction[0:4]
        amount =  amount[0]+'.'+fraction
        con.commit()
        con.close()

        return amount
    else:
        con.commit()
        con.close()

        return amount


    con.commit()
    con.close()

    return amount



#symbol(btc_jpy)などからname(BTC)を取得
def convert_name_symbol(word):
    if word.isupper() == False:
        name = word.split("_")[0].upper()
        return name
    elif word.isupper() == True:
        word = word.lower()
        return word+"_jpy"
    else:
        return "couldn't invert symbol to name"


#buyに表示させる通貨リスト
#アイコンと通貨名と現在価格をsymbolから取得
def return_currency_info(symbol):

    #symbol(btc_jpyなど)をBTCに変換
    name = convert_name_symbol(symbol)
    price = float(fetch_recent_crypt_info(symbol))

    currency_info = {"icon_path":f"../static/crypt-img/{name}.png", "name": name, "price": price}

    return currency_info

# user_lit_factoryの定義 これを適用することで辞書型で返ってくる
def user_lit_factory(cursor, row):
   d = {}
   for idx, col in enumerate(cursor.description):
       d[col[0]] = row[idx]
   return d

#ユーザーが保有するcryptの情報を取得
def fetch_user_own_crypt(user_id):
    con = sqlite3.connect(db, check_same_thread=False)
    cur = con.cursor()
    crypt_info_li = cur.execute("SELECT * FROM holding_crypt WHERE user_id = ?", (user_id,))
    con.commit()

    if crypt_info_li == None:
        return None
    user_own_crypt_li = []

    for user_own_crypt_info in crypt_info_li:
        symbol = user_own_crypt_info[1]
        shares = user_own_crypt_info[2]
        name = user_own_crypt_info[3]
        unit_price = fetch_recent_crypt_info(symbol)

        total =  float(unit_price)*float(shares)
        #ex user_own_crypt_info = {user_id: INTEGER, symbol: TEXT, shares: INTEGER}
        user_own_crypt_li.append({"name": name, "shares": shares, "total": total})

    con.close()

    return user_own_crypt_li


def fetch_recent_crypt_info(symbol):
        #通貨の最新情報を取得
        URL = f'https://public.bitbank.cc/{symbol}/ticker'
        
        try: 
            currency_info = requests.get(URL).json() 
        except:
            print("coudn't fetch crypt-price with bitbank_api")

        #currency_infoから購入するsymbolの現在価格を取得

        unit_price = currency_info["data"]["last"]

        return unit_price



@app.route('/', methods=['GET', 'POST'])
def index():

        #ループの実行
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(load_profit(user_id=user_id))
        profit_li = load_profit(user_id=user_id)
        # return profit_li
        con = sqlite3.connect(db, check_same_thread=False)
        cur = con.cursor()
        cash = cur.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
        cash = cash.fetchall()[0][0]
        # データベースから保有情報をfetch
        user_own_crypt_li = fetch_user_own_crypt(user_id=user_id)

        profit = calc_profit(user_id=user_id)

        if user_own_crypt_li != None:
        
            return render_template('index.html', user_own_crypt_li = user_own_crypt_li, cash = cash, profit = profit, profit_li = profit_li)

        else:
            return render_template('index.html', cash = cash, profit_li = profit_li)


@app.route("/buy", methods=["GET", "POST"])
def buy():

    #機能
    #通貨を購入してDBへ保存
    #保存情報=symbopl, username, price
    #入力情報をチェックするライブラリ
    
    if request.method == 'POST':
        name = request.form['name']
        shares = request.form.get("shares")
        symbol = convert_name_symbol(name)

        #入力情報をチェックする機能を実装
        #シンボルが正しく入力された場合塗装でない場合
        try:
            unit_price = float(fetch_recent_crypt_info(symbol))
        except:
            return "coudn't fetch_recent_crypt_info"
        
        try:
            shares = float(shares)
        except:

            return "invalid input"

        if shares < 0 or shares == "" :

            return "invalid input_2"
        
        else:

            #購入分金額
            buy_price = unit_price*shares

            #所持金>=購入金額の判定
            con = sqlite3.connect(db, check_same_thread=False)
            cur = con.cursor()

            cash = cur.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
            cash = cash.fetchall()[0][0]

            # return cash

            #購入できるかどうか判定
            if cash >= buy_price:
                # if symbo == "" or shares.is_integer() == False or shares == "" or shares <= 0:
                #トランザクションテーブルに追加
                # db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, company, date) VALUES(?, ?, ?, ?, ?, ?, ?)", session["user_id"], symbol, shares, price, 'buy', name, datetime.now())
            
                #保有銘柄テーブルに追加

                #保有銘柄を取得
                holding_crypt = cur.execute("SELECT * FROM holding_crypt WHERE user_id = ?", (user_id,)).fetchall()
                #既に銘柄を保有している場合、保有していない場合で分岐
                for holding_info in holding_crypt:
                    #もし保有している銘柄と一致する場合
                    if symbol == holding_info[1]:

                        #保有している場合はsharesにappend
                        holding_shares = float(holding_info[2]) + shares
                        #保有テーブルに追加
                        cur.execute("UPDATE holding_crypt SET shares = ?  WHERE symbol = ?", (holding_shares, symbol,))
                        #トランザクションテーブルに追加
                        cur.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, company, date, name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (user_id, symbol, shares, unit_price, 'buy', symbol, datetime.now(), name,))
                        #Cashから購入金額分を引く
                        cur.execute("UPDATE users SET cash = ? WHERE id = ?", ((cash - buy_price), user_id,))
                        con.commit()
                        con.close()        
                        return redirect("/")
                    else:
                        pass
                else: 
                        #保有していない銘柄の場合

                        #保有していない場合
                        cur.execute("INSERT INTO holding_crypt (user_id, symbol, shares, name) VALUES(?, ?, ?, ?)", (user_id, symbol, shares, name))
                        #トランザクションテーブルに追加
                        cur.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, company, date, name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (user_id, symbol, shares, unit_price, 'buy', symbol, datetime.now(), name,))
                        #Cashから購入金額分を引く
                        cur.execute("UPDATE users SET cash = ? WHERE id = ?", ((cash - buy_price), user_id,))
                
                        con.commit()
                        con.close()
                        return redirect("/")
        # cur.execute("UPDATE holding_stock SET shares = ? WHERE symbol = ?", holding_shares, symbol)

            else:
                #十分なキャッシュを持っていない場合
                return "十分なcashを持っていません"

    #GETの場合
    else:
        #cryptのnameのリストを作成
        crypt_name_li = []
        for symbol in pairs:
            symbol = convert_name_symbol(symbol)
            crypt_name_li.append(symbol)

        #購入できる数量を把握
        # amount = can_buy_amount(symbol = symbol)
        currency_info_li = []
        #通貨のアイコン、名前、現在価格を取得して、リスト形式で格納
        for symbol in pairs:
            currency_info_li.append(return_currency_info(symbol = symbol))
        # return render_template('buy.html', currency_li=currency_li, amount = amount)
        return render_template('buy.html', currency_info_li=currency_info_li, crypt_name_li = crypt_name_li)
        # currency_li = [{"icon_path":"../static/bitcoin.png", "name": name, "price": price}, {}, {}]

@app.route("/sell", methods=["GET", "POST"])
# @login_required
def sell():
    """Sell shares of stock"""

    if request.method == 'POST':
        name = request.form['name']
        shares = request.form.get("shares")
        symbol = convert_name_symbol(name)

        #入力情報をチェックする機能を実装
        #シンボルが正しく入力された場合塗装でない場合
        try:
            unit_price = float(fetch_recent_crypt_info(symbol))
        except:
            return "coudn't fetch_recent_crypt_info"
        
        try:
            shares = float(shares)
        except:

            return "invalid input"

        if shares < 0 or shares == "" :

            return "invalid input_2"
        
        else:

            #売却分金額
            sell_price = unit_price*shares

            #所持金>=購入金額の判定
            con = sqlite3.connect(db, check_same_thread=False)
            cur = con.cursor()

            cash = cur.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
            cash = cash.fetchall()[0][0]

            # return cash

            shares = float(shares)

            #保有銘柄数を取得
            portfolio_li = cur.execute("SELECT * FROM holding_crypt WHERE user_id = ?", (user_id,)).fetchall()

            #symbolを所有している場合と所有していない場合で場合分け
            for holding_info in portfolio_li:
                #sharesをname(BTC)に変換
                name = convert_name_symbol(holding_info[1])
                if symbol == holding_info[1]:
                #symbolを所有していた場合
                    #保有数量と比較
                    if shares < holding_info[2]:
                        #保有数量から売る
                        holding_shares = (holding_info[2] - shares)
                        #保有テーブルのsharesを訂正
                        cur.execute("UPDATE holding_crypt SET shares = ? WHERE symbol = ? AND user_id = ?", (holding_shares, symbol, user_id,))
                        #トランザクションテーブルに追加
                        cur.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, company, date, name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (user_id, symbol, shares, unit_price, 'sell', symbol, datetime.now(), name,))
                        #Cashに売買金額を足す
                        cur.execute("UPDATE users SET cash = ? WHERE id = ?", ((cash + sell_price), user_id,))
                        
                        con.commit()
                        con.close()
                        return redirect("/")


                    elif shares == holding_info[2]:
                        #保有数量と販売数量が同じ場合、保有テーブルから削除
                        cur.execute("DELETE FROM  holding_crypt WHERE symbol = ? AND user_id = ?", (symbol, user_id, ))
                        #トランザクションテーブルに追加
                        cur.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, company, date, name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (user_id, symbol, shares, unit_price, 'sell', symbol, datetime.now(), name,))
                        #Cashに売買金額を足す
                        cur.execute("UPDATE users SET cash = ? WHERE id = ?", ((cash + sell_price), user_id,))
                        con.commit()
                        con.close()
                        return redirect("/")
                    else:
                        pass
            else:
                #symbolを所有していない場合
                con.commit()
                con.close()
                return "販売数量を保持していません"

    else:

        #リクエストがGETの場合

        user_own_crypt_li = fetch_user_own_crypt(user_id=user_id)

        return render_template("sell.html", portfolio_li = user_own_crypt_li)


@app.route("/history")
# @login_required
def history():
    """Show history of transactions"""
    #tansaction_listsに、symbol, shares, price, transacted(日付)をリスト[辞書]形式で格納
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = user_lit_factory
    cur = con.cursor()

    #ユーザーのトランザクションをfetch
    tansaction_lists =  cur.execute("SELECT symbol, shares, price, transaction_type, date FROM transactions WHERE user_id = ?", (user_id,)).fetchall()
    if tansaction_lists != None:

        con.commit()
        con.close()
        return render_template("history.html", tansaction_lists = tansaction_lists)
    else:
        return render_template("history.html")

@app.route("/ranking")
def ranking():
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = user_lit_factory
    cur = con.cursor()

    #全ユーザーのprofitを取得

    user_li = []

    username_cash_li = cur.execute("SELECT id, username, cash FROM users").fetchall()
    # username_cash_li = [{}, {}]
    # return username_cash_li
    li = []
    for i, user_info in enumerate(username_cash_li):
        id = user_info["id"]
        user_name = user_info["username"]
        #profitを計算
        profit = calc_profit(user_id=id)

        # return str(profit)
        #profitはOK
        user_li.append({"user_id": id, "profit": profit, "user_name": user_name})
    # return user_li
    user_li = reversed(bubble_sort(user_li = user_li))
    return render_template("ranking.html", user_li = user_li)

# async def load_profit(user_id):
#     while True:
def load_profit(user_id):
        # await asyncio.sleep(15)
        #ユーザーのprofitを計算
        profit = calc_profit(user_id)

        #profit, id, dateをprofitテーブルに追加
        con = sqlite3.connect(db, check_same_thread=False)
        #出力結果を辞書形式のリストで扱えるように
        con.row_factory = user_lit_factory

        cur = con.cursor()
        cur.execute("INSERT INTO profit (id, date, profit) VALUES(?, ?, ?)", (user_id, datetime.now(), profit,))
        con.commit()
        
        profit_li = cur.execute("SELECT profit, date FROM profit WHERE id = ?", (user_id,)).fetchall()

        con.commit()

        # print(type(profit_li))
        # profit_liはリスト
        
        return profit_li

@app.route("/chart")
def chart():
    profit_li = load_profit(user_id=user_id)
    # return profit_li
    return render_template("chart.html", profit_li = profit_li) 

@app.route("/buy2")
def buy2():
    return render_template("buy2.html")

## おまじない
if __name__ == "__main__":
    app.run(debug=True)
    #並列処理




