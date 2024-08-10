#This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
#if accountLive is true your api requests will be sent to a live account
ACCOUNT_LIVE = False
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
API_KEY = "YOUR_API_KEY"
STARTING_BALANCE = 100000.0
#do not write with -, %, or as a decimal (do not write 4% as 0.04)
ALLOWED_MAX_DRAWDOWN_PERCENT = 6.0
#do not write with -, %, or as a decimal
TARGET_PROFIT_PERCENT = 5.0

#---------------DO NOT MESS WITH THE REST OF THE CODE---------------------
if ACCOUNT_LIVE == False:
    OANDA_URL = 'https://api-fxpractice.oanda.com/v3'
else:
    OANDA_URL = 'https://api-fxtrade.oanda.com/v3'

SECURE_HEADER = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}    
