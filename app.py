#This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
from flask import Flask, render_template, request
import defs
import json
import requests
from oanda_api import OandaAPI

api = OandaAPI()

app = Flask(__name__)

trade_id_log = []
can_i_trade_log = [True]
fill_tp_sl_exicuted_log = [True]

#to activate the app enter flask run in command console
@app.route('/')
def dashboard():
    
    def truncate(num, decimals=2):
        multiplier = 10 ** decimals
        return int(num * multiplier) / multiplier
    
    status_code, data, current_balance, target_balance, target_profit_percent, allowed_max_drawdown_percent, gain_loss_percent, margin_closeout_percent, reached_target_profit, hit_allowed_max_drawdown, open_positions, open_trades, lastTransactionID = api.get_dashboard_info()
    can_i_trade, involved_in_trade = api.can_i_continue_trading(reached_target_profit, hit_allowed_max_drawdown, open_trades, open_positions)
    if (can_i_trade == False and involved_in_trade == True) or (fill_tp_sl_exicuted_log[-1]==False):
            requests.put(url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/trades/{str(trade_id_log[-1])}/close", headers= defs.SECURE_HEADER)
    
    can_i_trade_log.append(can_i_trade)

    return render_template("dashboard.html", status_code = status_code, starting_balance = defs.STARTING_BALANCE, current_balance = current_balance, target_balance = target_balance, target_profit_percent = target_profit_percent, allowed_max_drawdown_percent = allowed_max_drawdown_percent, gain_loss_percent = truncate(gain_loss_percent, 2), margin_closeout_percent = truncate(margin_closeout_percent, 2), reached_target_profit = reached_target_profit, hit_allowed_max_drawdown = hit_allowed_max_drawdown, open_positions = open_positions, open_trades = open_trades, can_i_trade = can_i_trade, involved_in_trade = involved_in_trade, lastTransactionID = lastTransactionID)

@app.route('/webhook', methods=['POST'])
def webhook():

    webhook_message = request.data
    webhook_message = json.loads(request.data)
    can_continue_trades = can_i_trade_log[-1]

    mintick_value = float(webhook_message['strategy']['mintickValue'])
    conversion_rate = float(webhook_message['strategy']['conversionRate'])
    symbol = str(webhook_message['strategy']['symbol'])
    direction = int(webhook_message['strategy']['direction'])
    risk = float(webhook_message['strategy']['risk'])
    trade_entry_price = float(webhook_message['strategy']['tradeEntryPrice'])
    trade_stop_price = float(webhook_message['strategy']['tradeStopPrice'])
    trade_target_price = float(webhook_message['strategy']['tradeTargetPrice'])

    if can_continue_trades == True:
        position_size = api.get_position_size(risk, mintick_value, direction, trade_entry_price,trade_stop_price, conversion_rate)
        trade_id, ok, status_code = api.place_trade(symbol, position_size, trade_target_price, trade_stop_price)
        trade_id_log.append(trade_id)
        fill_tp_sl_exicuted_log.append(ok)
        return f"{str(trade_id)}, {str(ok)}, {str(status_code)}, {str(trade_id_log[-1])}"
    else:
        return "not allowed to trade because you either reached your target profit or hit your allowed max drawdown"

if __name__ == '__main__':
    app.run(debug=True)