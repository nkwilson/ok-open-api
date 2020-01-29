import okex.account_api as account
import okex.ett_api as ett
import okex.futures_api as future
import okex.lever_api as lever
import okex.spot_api as spot
import json

api_key = "9b8f6039-a5db-4862-95b9-183404b95ac6"
secret_key = "7AFDDC3FB2F9D3693B16BC1D6AB441EE"
IP = "0"
passphrase = 'v3api0'

futureAPI = future.FutureAPI(api_key, secret_key, passphrase, True)

# symbol is like BTC-USD, contract is like quarter/this_week/next_week
def query_instrument_id(symbol, contract):
    result = futureAPI.get_products()
    return list(filter(lambda i: i['alias'] == contract and i['underlying'] == symbol.upper().replace('_', '-'), result))[0]['instrument_id']

def transform_direction(direction):
    new_dirs = {'buy':'long', 'sell':'short'}
    return new_dirs[direction]

def open_order_sell_rate(symbol, contract, amount, price='', lever_rate='10'):
    return futureAPI.take_order(instrument_id=query_instrument_id(symbol, contract), type=2, size=amount, match_price=1)
    #return okcoinFuture.future_trade(symbol, contract, '', amount, '2', '1', '10')

def close_order_sell_rate(symbol, contract, amount, price='', lever_rate='10'):
    return futureAPI.take_order(instrument_id=query_instrument_id(symbol, contract), type=4, size=amount, match_price=1)
    #return okcoinFuture.future_trade(symbol, contract, '', amount, '4',                                     '1', '10')

def open_order_buy_rate(symbol, contract, amount, price='', lever_rate='10'):
    return futureAPI.take_order(instrument_id=query_instrument_id(symbol, contract), type=1, size=amount, match_price=1)
    #return okcoinFuture.future_trade(symbol, contract, '', amount, '1',                                     '1', '10')

def close_order_buy_rate(symbol, contract, amount, price='', lever_rate='10'):
    return futureAPI.take_order(instrument_id=query_instrument_id(symbol, contract), type=3, size=amount, match_price=1)
    #return okcoinFuture.future_trade(symbol, contract, '', amount, '3',                                     '1', '10')

def cancel_order(symbol, contract, order_id):
    return futureAPI.revoke_order(instrument_id=query_instrument_id(symbol, contract), order_id=order_id)
    #return okcoinFuture.future_cancel(symbol, contract, order_id)

def query_orderinfo(symbol, contract, order_id):
    return futureAPI.get_order_info(order_id, query_instrument_id(symbol, contract))
#    return futureAPI.future_orderinfo(symbol,contract, order_id,'0','1','2')

# In [7]: backend.query_kline('bch_usd', '300', 'this_week')
# Out[7]: 
# [['2020-01-28T11:20:00.000Z',
#   '372.63',
#   '372.85',
#   '371.45',
#   '371.52',
#   '8727',
#   '233.17'],

def query_kline(symbol, period, contract, ktype=''):
    return futureAPI.get_kline(query_instrument_id(symbol, contract), granularity=period)
    #return okcoinFuture.future_kline(symbol, period, contract, ktype)

# In [13]: futureAPI.get_specific_position('BTC-USD-200327')
# Out[13]: 
# {'holding': [{'created_at': '2019-12-13T11:59:47.180Z',
#    'instrument_id': 'BTC-USD-200327',
#    'last': '9255.96',
#    'long_avail_qty': '453',
#    'long_avg_cost': '9259.81231406',
#    'long_leverage': '10',
#    'long_liqui_price': '8464.52',
#    'long_maint_margin_ratio': '0.005',
#    'long_margin': '0.5002992',
#    'long_margin_ratio': '0.09960771',
#    'long_pnl': '-0.00174529',
#    'long_pnl_ratio': '-0.0035676',
#    'long_qty': '453',
#    'long_settled_pnl': '0.01108841',
#    'long_settlement_price': '9280.8482067',
#    'long_unrealised_pnl': '-0.0128337',
#    'margin_mode': 'fixed',
#    'realised_pnl': '-0.00103693',
#    'short_avail_qty': '203',
#    'short_avg_cost': '9258.91',
#    'short_leverage': '10',
#    'short_liqui_price': '10231.48',
#    'short_maint_margin_ratio': '0.005',
#    'short_margin': '0.21924827',
#    'short_margin_ratio': '0.10023329',
#    'short_pnl': '5.6846E-4',
#    'short_pnl_ratio': '0.0025928',
#    'short_qty': '203',
#    'short_settled_pnl': '0',
#    'short_settlement_price': '9258.91',
#    'short_unrealised_pnl': '5.6846E-4',
#    'updated_at': '2020-01-28T09:01:14.380Z'}],
#  'margin_mode': 'fixed',
#  'result': True}
    
def check_holdings_profit(symbol, contract, direction):
    nn = (0, 0, 0) # (loss, amount, bond)
    loops = 3
    instrument_id = query_instrument_id(symbol, contract)
    while loops > 0:
        loops -= 1
        try:
            holding=futureAPI.get_specific_position(instrument_id)
            if holding['result'] == False:
                return nn
            break
        except Exception as ex:
            time.sleep(1)
    if loops == 0 or len(holding['holding']) == 0:
        return nn
    data = holding['holding'][0]
    new_dir=transform_direction(direction)
    loss = float(data['%s_pnl_ratio' % new_dir])
    amount = float(data['%s_qty' % new_dir])
    margin = float(data['%s_margin' % new_dir])
    if (amount == 0):
        return nn
    else:
        return (loss, amount, margin / amount)

# Figure out current holding's open price, zero means no holding
def real_open_price_and_cost(symbol, contract, direction):
    instrument_id = query_instrument_id(symbol, contract)
    holding=futureAPI.get_specific_position(instrument_id)
    if holding['result'] != True:
        return 0
    if len(holding['holding']) == 0:
        return 0
    # print (holding['holding'])
    l_dir=transform_direction(direction)
    data=holding['holding'][0]
    if data['%s_qty' % l_dir] != 0:
        avg = float(data['%s_avg_cost' % l_dir])
        real = float(data['%s_pnl_ratio' % l_dir])/float(data['%s_leverage' % l_dir])
        return (avg, avg*real)
    return 0

def query_bond(symbol, contract, direction):
    instrument_id = query_instrument_id(symbol, contract)
    holding=futureAPI.get_specific_position(instrument_id)
    if holding['result'] != True:
        return 0.0 # 0 means failed
    if len(holding['holding']) == 0:
        return 0.0
    l_dir=transform_direction(direction)
    data=holding['holding'][0]
    if data['%s_qty' % l_dir] != 0:
        return float(data['%s_margin' % l_dir])/float(data['%s_qty' % l_dir])
    return 0.0

# In [25]: futureAPI.get_coin_account('BTC-USD')
# Out[25]: 
# {'auto_margin': '1',
#  'can_withdraw': '3.59490925',
#  'contracts': [{'available_qty': '3.59490925',
#    'fixed_balance': '0.7205844',
#    'instrument_id': 'BTC-USD-200327',
#    'margin_for_unfilled': '0',
#    'margin_frozen': '0.71954747',
#    'realized_pnl': '-0.00103693',
#    'unrealized_pnl': '-0.0053'}],
#  'currency': 'BTC',
#  'equity': '4.309263',
#  'liqui_mode': 'tier',
#  'margin_mode': 'fixed',
#  'total_avail_balance': '3.59490925'}

def query_balance(symbol):
    try:
        result=futureAPI.get_coin_account(symbol.replace('_', '-').upper())
        return float(result['equity'])
    except Exception as ex:
        return 0.0

if __name__ == '__main__':

    # account api test
    # param use_server_time's value is False if is True will use server timestamp
    #accountAPI = account.AccountAPI(api_key, seceret_key, passphrase, True)
    #result = accountAPI.get_currencies()
    #result = accountAPI.get_wallet()
    #result = accountAPI.get_currency('btc')
    #result = accountAPI.get_currency('btc')
    #result = accountAPI.get_coin_fee('btc')
    #result = accountAPI.get_coin_fee('btc')
    #result = accountAPI.get_coins_withdraw_record()
    #result = accountAPI.get_coin_withdraw_record('BTC')
    #result = accountAPI.get_ledger_record_v3()
    #result = accountAPI.get_top_up_address('BTC')
    #result = accountAPI.get_top_up_address('BTC')
    #result = accountAPI.get_top_up_records()
    #result = accountAPI.get_top_up_record('BTC')

    # spot api test
    #spotAPI = spot.SpotAPI(api_key, seceret_key, passphrase, True)
    #result = spotAPI.get_account_info()
    #result = spotAPI.get_coin_account_info('BTC')
    #result = spotAPI.get_coin_info()
    #result = spotAPI.get_depth('LTC-USDT')
    #result = spotAPI.get_ticker()
    #result = spotAPI.get_orders_list('all', 'Btc-usdT', limit=100)
    #result = spotAPI.get_ledger_record('BTC', limit=1)
    #result = spotAPI.get_specific_ticker('LTC-USDT')
    #result = spotAPI.get_deal_v3('LTC-USDT', 1, 3, 10)
    #result = spotAPI.get_kline('LTC-USDT', '2018-09-12T07:59:45.977Z', '2018-09-13T07:59:45.977Z', 60)

    # future api test
    futureAPI = future.FutureAPI(api_key, secret_key, passphrase, True)
    #result = futureAPI.get_position()
    #result = futureAPI.get_coin_account('btc')
    #result = futureAPI.get_leverage('btc')
    #result = futureAPI.set_leverage(symbol='BTC', instrument_id='BCH-USD-181026', direction=1, leverage=10)

    # orders = []
    # order1 = {"client_oid": "f379a96206fa4b778e1554c6dc969687", "type": "2", "price": "1800.0", "size": "1", "match_price": "0"}
    # order2 = {"client_oid": "f379a96206fa4b778e1554c6dc969687", "type": "2", "price": "1800.0", "size": "1", "match_price": "0"}
    # orders.append(order1)
    # orders.append(order2)
    # orders_data = json.dumps(orders)
    # print(orders_data)
    # result = futureAPI.take_orders('BCH-USD-181019', orders_data=orders_data, leverage=10)

    #result = futureAPI.get_ledger('btc')
    #result = futureAPI.get_products()
    #result = futureAPI.get_depth('BTC-USD-181019', 1)
    #result = futureAPI.get_ticker()
    #result = futureAPI.get_specific_ticker('ETC-USD-181026')
    #result = futureAPI.get_specific_ticker('ETC-USD-181026')
    #result = futureAPI.get_trades('ETC-USD-181026', 1, 3, 10)
    #result = futureAPI.get_kline('ETC-USD-181026','2018-10-14T03:48:04.081Z', '2018-10-15T03:48:04.081Z')
    #result = futureAPI.get_index('EOS-USD-181019')
    #result = futureAPI.take_order("ccbce5bb7f7344288f32585cd3adf357", 'BCH-USD-181019','2','10000.1','1','0','10')
    #result = futureAPI.take_order("ccbce5bb7f7344288f32585cd3adf351",'BCH-USD-181019',2,10000.1,1,0,10)
    #result = futureAPI.get_trades('BCH-USD-181019')
    #result = futureAPI.get_rate()
    #result = futureAPI.get_estimated_price('BTC-USD-181019')
    #result = futureAPI.get_holds('BTC-USD-181019')
    #result = futureAPI.get_limit('BTC-USD-181019')
    #result = futureAPI.get_liquidation('BTC-USD-181019', 0)
    #result = futureAPI.get_holds_amount('BCH-USD-181019')
    #result = futureAPI.get_currencies()
    #result = futureAPI.get_order_info(order-id, instrument_id)

    # level api test
    #levelAPI = lever.LeverAPI(api_key, seceret_key, passphrase, True)
    #result = levelAPI.get_account_info()
    #result = levelAPI.get_specific_account('btc-usdt')
    #result = levelAPI.get_ledger_record_v3('btc-usdt', '1', '4', '2')
    #result = levelAPI.get_config_info()
    #result = levelAPI.get_specific_config_info('btc-usdt')
    #result = levelAPI.get_borrow_coin_v3(0, 1, 2, 1)

    # ett api test
    #ettAPI = ett.EttAPI(api_key, seceret_key, passphrase, True)
    #result = ettAPI.get_accounts()
    #result = ettAPI.get_account('usdt')
    #result = ettAPI.get_ledger('usdt')
    #result = ettAPI.get_constituents('ok06ett')
    #result = ettAPI.get_define_price('ok06ett')

    print(json.dumps(result))
