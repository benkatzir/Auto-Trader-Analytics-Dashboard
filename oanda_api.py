#This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
import requests
import defs
import json

class OandaAPI():

    def __init__(self):
        self.session = requests.Session()    

    def make_request(self, url, params={}, added_headers=None, verb='get', data=None, code_ok=200):
        headers = defs.SECURE_HEADER
        if added_headers is not None:   
            for k in added_headers.keys():
                headers[k] = added_headers[k]                
        try:
            response = None
            if verb == 'post':
                response = self.session.post(url,params=params,headers=headers,data=data)
            elif verb == 'put':
                response = self.session.put(url,params=params,headers=headers,data=data)
            else:
                response = self.session.get(url,params=params,headers=headers,data=data)
            status_code = response.status_code
            if status_code == code_ok:
                json_response = response.json()
                return status_code, json_response
            else:
                return status_code, None   
        except:
            print("ERROR")
            return 400, None
    
    def get_position_size(self, risk, mintick_value, direction, trade_entry_price, trade_stop_price, conversion_currency_rate):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/summary"
        status_code, data = self.make_request(url)
        if status_code == 200:
            balance = float(data["account"]["NAV"])
            stop_loss_size = abs((trade_entry_price - trade_stop_price)/mintick_value/10)
            risk_amount = (balance * (risk/100)) * conversion_currency_rate  #Takes amount of money being risked in your accounts currency and converts it to the ammount being risked in the symbols counter currency
            risk_per_pip = risk_amount/stop_loss_size
            if mintick_value==0.001:
                position_size_multiplier = 100
            else:
                position_size_multiplier = 10000
            position_size = risk_per_pip *position_size_multiplier
            return round(position_size)*direction
        else:
            return status_code, None

    def set_sl_tp(self, price, order_type, trade_id):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/orders"
        data = {
            "order": {
                "timeInForce": "GTC",
                "price": str(price), 
                "type": order_type,
                "tradeID": str(trade_id)
            }
        }
        status_code, json_data = self.make_request(url, verb='post', data=json.dumps(data), code_ok=201)
        if status_code != 201:
            return False
        
        return True

    def place_trade(self, pair, units, take_profit=None, stop_loss=None):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/orders"
        data = {
            "order": {
                "units": units,
                "instrument": pair,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
        status_code, json_data = self.make_request(url, verb='post', data=json.dumps(data), code_ok=201)
        if status_code != 201:
            return None
        trade_id = None
        ok = True
        if "orderFillTransaction" in json_data and "tradeOpened" in json_data["orderFillTransaction"]:
            trade_id = int(json_data["orderFillTransaction"]["tradeOpened"]["tradeID"])
            if take_profit is not None:
                if(self.set_sl_tp(take_profit, "TAKE_PROFIT", trade_id) == False):
                    ok = False
            if stop_loss is not None:
                if(self.set_sl_tp(stop_loss, "STOP_LOSS", trade_id) == False):
                    ok = False

        return trade_id, ok, status_code

    def get_dashboard_info(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/summary"
        status_code, data = self.make_request(url)
        current_balance = float(json.loads(data["account"]["NAV"]))
        target_balance = defs.STARTING_BALANCE*(1+(defs.TARGET_PROFIT_PERCENT/100))
        target_profit_percent = defs.TARGET_PROFIT_PERCENT
        allowed_max_drawdown_percent = -defs.ALLOWED_MAX_DRAWDOWN_PERCENT
        gain_loss_percent = (current_balance - defs.STARTING_BALANCE)/current_balance*100
        margin_closeout_percent = float(json.loads(str(data["account"]["marginCloseoutPercent"])))*100
        reached_target_profit = gain_loss_percent >= target_profit_percent
        hit_allowed_max_drawdown = gain_loss_percent <= allowed_max_drawdown_percent
        open_trades = int(json.loads(str(data["account"]["openTradeCount"])))
        open_positions = int(json.loads(str(data["account"]["openPositionCount"])))
        lastTransactionID = (data["lastTransactionID"])
        return status_code, data, current_balance, target_balance, target_profit_percent, allowed_max_drawdown_percent, gain_loss_percent, margin_closeout_percent, reached_target_profit, hit_allowed_max_drawdown, open_positions, open_trades, lastTransactionID

    def can_i_continue_trading(self, reached_target_profit, hit_allowed_max_drawdown, open_trades, open_positions):
        can_i_trade = True
        involved_in_trade = False
        if reached_target_profit==True or hit_allowed_max_drawdown==True:
            can_i_trade = False
        if open_trades != 0 or open_positions != 0:
            involved_in_trade = True
        return can_i_trade, involved_in_trade

if __name__ == "__main__":
    api = OandaAPI()