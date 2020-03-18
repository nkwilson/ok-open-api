# -*- coding: utf-8 -*-

# import okex.account_api as account
import okex.futures_api as future
# import okex.lever_api as lever
# import okex.spot_api as spot
import okex.swap_api as swap
# import okex.index_api as index
# import okex.option_api as option

import datetime
import logging
import json

import time

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='order_exceptions.json', filemode='a', format=log_format, level=logging.INFO)

api_key = "9b8f6039-a5db-4862-95b9-183404b95ac6"
secret_key = "7AFDDC3FB2F9D3693B16BC1D6AB441EE"
IP = "0"
passphrase = 'v3api0'

# In [3]: backend.futureAPI.get_products()
# Out[3]:
# [{'alias': 'this_week',
#   'base_currency': 'XRP',
#   'contract_val': '10',
#   'contract_val_currency': 'USD',
#   'delivery': '2020-01-31',
#   'instrument_id': 'XRP-USD-200131',
#   'is_inverse': 'true',
#   'listing': '2020-01-17',
#   'quote_currency': 'USD',
#   'settlement_currency': 'XRP',
#   'tick_size': '0.0001',
#   'trade_increment': '1',
#   'underlying': 'XRP-USD',
#   'underlying_index': 'XRP'},
# {'alias': 'quarter',
#   'base_currency': 'TRX',
#   'contract_val': '10',
#   'contract_val_currency': 'USD',
#   'delivery': '2020-03-27',
#   'instrument_id': 'TRX-USD-200327',
#   'is_inverse': 'true',
#   'listing': '2019-12-13',
#   'quote_currency': 'USD',
#   'settlement_currency': 'TRX',
#   'tick_size': '0.00001',
#   'trade_increment': '1',
#   'underlying': 'TRX-USD',
#   'underlying_index': 'TRX'}]

# symbol is like BTC-USD, contract is like quarter/this_week/next_week
expire_day = ''
instrument_id = ''
which_api = ''


def query_instrument_id(symbol, contract):
    global expire_day, instrument_id, which_api
    # print (expire_day)
    if which_api == '':
        if contract == 'swap':
            which_api = swap.SwapAPI(api_key, secret_key, passphrase, False)
        else:
            which_api = future.FutureAPI(api_key, secret_key, passphrase, False)
    if contract == 'swap':  # specific case
        return symbol.upper().replace('_', '-') + '-SWAP'
        pass
    if True or expire_day <= datetime.datetime.strftime(datetime.datetime.utcnow(), '%Y-%m-%d'):  # need update
        # print ('query_instrument_id fresh')
        new_contracts = {'quarter': 'quarter', 'thisweek': 'this_week', 'nextweek': 'next_week'}
        result = which_api.get_products()
        product = list(
            filter(
                lambda i: i['alias'] == new_contracts[contract] and i['underlying'] == symbol.upper().replace('_', '-'),
                result))[0]
        instrument_id = product['instrument_id']
        expire_day = product['delivery']
    else:  # check whether it is valid
        # print ('query_instrument_id cached', instrument_id)
        pass
    # print (instrument_id)
    return instrument_id


def transform_direction(direction):
    new_dirs = {'buy': 'long', 'sell': 'short'}
    return new_dirs[direction]


# {'instrument_id': 'XRP-USD-200207', 'highest': '0.2504', 'lowest': '0.2359', 'timestamp': '2020-01-31T07:08:31.394Z'}


def query_limit(instrument_id):
    cached_limit = dict()
    try:
        cached_limit = which_api.get_limit(instrument_id)
    except Exception as ex:
        logging.info(instrument_id, ex)
    # print (cached_limit)
    return cached_limit


# In [6]: backend.which_api.get_specific_ticker('EOS-USD-SWAP')
# Out[6]:
# {'best_ask': '4.958',
#  'best_bid': '4.957',
#  'high_24h': '5.05',
#  'instrument_id': 'EOS-USD-SWAP',
#  'last': '4.956',
#  'low_24h': '4.735',
#  'timestamp': '2020-02-09T09:38:15.941Z',
#  'volume_24h': '8156913'}


def query_ticker(instrument_id):
    ticker = dict()
    try:
        ticker = which_api.get_specific_ticker(instrument_id)
    except Exception as ex:
        logging.info(instrument_id, ex)
        logging.info(ex)
    # print (ticker)
    return ticker


# In [12]: order_datas=[]
# In [13]: order_datas.append({'order_type':"1",'price':"386",'size':"1",'type':"2",'match_price':"0"})
# In [14]: order_datas.append({'order_type':"1",'price':"386",'size':"1",'type':"1",'match_price':"0"})
# In [15]: baskend.futureAPI.take_orders('BCH-USD-200131', order_datas)
# Out[15]:
# {'order_info': [{'error_code': '0',
#    'error_message': '',
#    'order_id': '4297413100522497'},
#   {'error_code': '0', 'error_message': '', 'order_id': '4297413100522499'}],
#  'result': True}

# In [2]: backend.open_order_sell_rate('bch_usd', 'thisweek', 1)
# url: https://www.okex.com/api/futures/v3/instruments
# body:
# url: https://www.okex.com/api/futures/v3/order
# body: {"client_oid": "", "instrument_id": "BCH-USD-200131", "type": 2, "order_type": "0", "price": "", "size": 1, "match_price": 1}
# Out[2]:
# {'error_code': '0',
#  'error_message': '',
#  'order_id': '4295822327387137',
#  'result': True}


def issue_order(instrument_id, otype, price, size, match_price, order_type):
    try:
        result = which_api.take_order(instrument_id=instrument_id,
                                      type=otype,
                                      price=price,
                                      size=size,
                                      match_price=match_price,
                                      order_type=order_type)
        # print (instrument_id, otype, price, size, match_price, order_type)
        # print (result)
    except Exception as ex:
        result = {'error_code': ex.code, 'result': False}
        print(ex)
        logging.info('%s %s %s %s %s %s' % (instrument_id, otype, price, size, match_price, order_type))
        logging.info(ex)
    # API Request Error(code=32014): Positions that you are closing exceeded the total qty of contracts allowed to close
    # API Request Error(code=35014): Order price is not within limit
    # API Request Error(code=35008): Risk ratio too high
    # API Request Error(code=32016): Risk rate lower than 100% after opening position
    # API Request Error(code=32015): Risk rate lower than 100% before opening positio
    if not result['result'] or result['error_code'] != '0':  # something is wrong
        if result['error_code'] == '35014':  # try again with zero price
            print('(code=35014): Order price is not within limit, try again')
            return issue_order(instrument_id, otype, '', size, match_price='1', order_type='0')
        logging.info('%s %s %s %s %s %s' % (instrument_id, otype, price, size, match_price, order_type))
        logging.info("result:" + json.dumps(result))
    return result


def open_order_sell_rate(symbol, contract, amount, price='', lever_rate='10'):
    inst_id = query_instrument_id(symbol, contract)
    otype = '0'  # not 2 FOK
    if (price == '' or price == 0):  # use optimized price
        ticker = query_ticker(inst_id)
        price = float(ticker['best_bid']) * 0.99  # sell with lower price
        otype = '2'  # FOK
    # print (symbol, contract, amount, price)
    return issue_order(inst_id, 2, price, int(amount), match_price='0', order_type=otype)
    # return okcoinFuture.future_trade(symbol, contract, '', amount, '2', '1', '10')


def close_order_sell_rate(symbol, contract, amount, price='', lever_rate='10'):
    inst_id = query_instrument_id(symbol, contract)
    otype = '0'  # not FOK
    if price == '' or price == 0:  # use optimized price
        ticker = query_ticker(inst_id)
        price = float(ticker['best_ask']) * 1.01  # buy with higher price
        otype = '2'  # FOK
    # print (symbol, contract, amount, price)
    return issue_order(inst_id, 4, price, int(amount), match_price='0', order_type=otype)
    # return okcoinFuture.future_trade(symbol, contract, '', amount, '4',                                     '1', '10')


def open_order_buy_rate(symbol, contract, amount, price='', lever_rate='10'):
    inst_id = query_instrument_id(symbol, contract)
    otype = '0'  # not FOK
    if price == '' or price == 0:  # use optimized price
        ticker = query_ticker(inst_id)
        price = float(ticker['best_ask']) * 1.01
        otype = '2'  # FOK
    # print (symbol, contract, amount, price)
    return issue_order(inst_id, 1, price, int(amount), match_price='0', order_type=otype)
    # return okcoinFuture.future_trade(symbol, contract, '', amount, '1',                                     '1', '10')


def close_order_buy_rate(symbol, contract, amount, price='', lever_rate='10'):
    inst_id = query_instrument_id(symbol, contract)
    otype = '0'  # not FOK
    if price == '' or price == 0:  # use optimized price
        ticker = query_ticker(inst_id)
        price = float(ticker['best_bid']) * 0.99
        otype = '2'  # FOK
    # print (symbol, contract, amount, price)
    return issue_order(inst_id, 3, price, int(amount), match_price='0', order_type=otype)
    # return okcoinFuture.future_trade(symbol, contract, '', amount, '3',                                     '1', '10')


def cancel_order(symbol, contract, orderid):
    try:
        inst_id = query_instrument_id(symbol, contract)
        return which_api.revoke_order(inst_id, orderid)
    except Exception as ex:
        logging.info(symbol, contract, ex)
    # return okcoinFuture.future_cancel(symbol, contract, order_id)


# In [2]: backend.query_orderinfo('bch_usd', 'thisweek', 4295822327387137)
# Out[2]:
# {'client_oid': '',
#  'contract_val': '10',
#  'fee': '-0.00001276',
#  'filled_qty': '1',
#  'instrument_id': 'BCH-USD-200131',
#  'leverage': '10',
#  'order_id': '4295822327387137',
#  'order_type': '0',
#  'pnl': '0',
#  'price': '391.96',
#  'price_avg': '391.96',
#  'size': '1',
#  'state': '2',
#  'status': '2',
#  'timestamp': '2020-01-29T08:04:06.760Z',
#  'type': '2'}

# state字段标记订单查询结果
# state	String	订单状态
# -2：失败
# -1：撤单成功
# 0：等待成交
# 1：部分成交
# 2：完全成交
# 3：下单中
# 4：撤单中


def query_orderinfo(symbol, contract, orderid):
    result = dict()
    try:
        inst_id = query_instrument_id(symbol, contract)
        result = which_api.get_order_info(inst_id, orderid)
    except Exception as ex:
        logging.info(symbol, contract, ex)

    # print (result)
    return result


#    return futureAPI.future_orderinfo(symbol,contract, order_id,'0','1','2')


def query_orderinfo_wait(symbol, contract, orderid):
    try:
        state = 0
        loops = 10
        while state >= 0 and loops > 0:
            result = query_orderinfo(symbol, contract, orderid)
            # print (result)
            state = int(result['state'])
            if state == 2:  # yes, full
                return result
            time.sleep(1)  # wait 1 second
            loops -= 1
            continue
        return result
    except Exception as ex:
        logging.info(symbol, contract, ex)
        print(ex)
        return ex


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
    inst_id = query_instrument_id(symbol, contract)
    kline = which_api.get_kline(inst_id, granularity=period)
    last = kline[-1]
    last[0] = str(datetime.datetime.strptime(last[0], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
    return [last]
    # return okcoinFuture.future_kline(symbol, period, contract, ktype)


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


# for swap position, result is as such:
# In [47]: swapAPI.get_specific_position('EOS-USD-SWAP')
# Out[47]:
# {'holding': [{'avail_position': '1',
#    'avg_cost': '4.184',
#    'instrument_id': 'EOS-USD-SWAP',
#    'last': '4.182',
#    'leverage': '10.00',
#    'liquidation_price': '1.076',
#    'maint_margin_ratio': '0.0100',
#    'margin': '0.2391',
#    'position': '1',
#    'realized_pnl': '-0.0011',
#    'settled_pnl': '0.0000',
#    'settlement_price': '4.184',
#    'side': 'long',
#    'timestamp': '2020-02-02T08:17:25.532Z',
#    'unrealized_pnl': '-0.0015'}],
#  'margin_mode': 'crossed',
#  'timestamp': '2020-02-02T08:17:25.532Z'}
def get_loss_amount_from_swap(holding, direction):
    try:
        result = list(filter(lambda i: i['side'] == direction, holding))
        data = result[0]
        loss = (float(data['unrealized_pnl']) + float(data['settled_pnl'])) * 100 / float(data['margin'])
        amount = float(data['avail_position'])
        leverage = float(data['leverage'])
        return (loss, amount, leverage)
    except Exception as ex:
        logging.info(ex)
        return (0, 0, 0)


# get it through api get_specific_position
def get_margin_mode(symbol, contract):
    try:
        holding = which_api.get_specific_position(symbol, contract)
        return holding['margin_mode']
    except Exception as ex:
        logging.info(ex)
        return ''


def check_holdings_profit(symbol, contract, direction):
    try:
        inst_id = query_instrument_id(symbol, contract)
        holding = which_api.get_specific_position(inst_id)
        new_dir = transform_direction(direction)
        if contract == 'swap':
            return get_loss_amount_from_swap(holding['holding'], new_dir)
        # future orders
        data = holding['holding'][0]
        loss = float(data['%s_pnl_ratio' % new_dir]) * 100  # loss is float value less than 100
        amount = float(data['%s_avail_qty' % new_dir])
        if 'leverage' in data.keys():
            leverage = float(data['leverage'])
        else:
            leverage = float(data['%s_leverage' % new_dir])
        return (loss, amount, leverage)
    except Exception as ex:
        logging.info(symbol, contract, ex)
        return (0, 0, 0)


def get_real_open_price_and_cost_from_swap(holding, direction):
    try:
        result = list(filter(lambda i: i['side'] == direction, holding))
        data = result[0]
        avg = float(data['avg_cost'])
        real = abs(float(data['realized_pnl'])) / float(data['margin'])
        return (avg, avg * real)
    except Exception as ex:
        logging.info(ex)
        return (0, 0)


# Figure out current holding's open price, zero means no holding
def real_open_price_and_cost(symbol, contract, direction):
    inst_id = query_instrument_id(symbol, contract)
    holding = which_api.get_specific_position(inst_id)
    # print (holding['holding'])
    l_dir = transform_direction(direction)
    if contract == 'swap':
        return get_real_open_price_and_cost_from_swap(holding['holding'], l_dir)
    try:
        # future orders
        data = holding['holding'][0]
        avg = float(data['%s_avg_cost' % l_dir])
        real = float(data['%s_pnl_ratio' % l_dir]) / float(data['%s_leverage' % l_dir])
        return (avg, avg * real)
    except Exception as ex:
        logging.info(symbol, contract, ex)
        return (0, 0)


def get_bond_from_swap(holding, direction):
    result = list(filter(lambda i: i['side'] == direction, holding))
    try:
        data = result[0]
        return float(data['margin']) / float(data['position'])
    except Exception as ex:
        logging.info(ex)
        return 0.0


def query_bond(symbol, contract, direction):
    inst_id = query_instrument_id(symbol, contract)
    holding = which_api.get_specific_position(inst_id)
    l_dir = transform_direction(direction)
    if contract == 'swap':
        return get_bond_from_swap(holding['holding'], l_dir)
    try:
        data = holding['holding'][0]
        return float(data['%s_margin' % l_dir]) / float(data['%s_qty' % l_dir])
    except Exception as ex:
        logging.info(symbol, contract, ex)
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

# In [4]: backend.swapAPI.get_coin_account('EOS-USD-SWAP')
# Out[4]:
# {'info': {'equity': '7.0415',
#   'fixed_balance': '0.0000',
#   'instrument_id': 'EOS-USD-SWAP',
#   'maint_margin_ratio': '0.0100',
#   'margin': '0.2347',
#   'margin_frozen': '0.0000',
#   'margin_mode': 'crossed',
#   'margin_ratio': '2.9996',
#   'max_withdraw': '6.8067',
#   'realized_pnl': '-0.0011',
#   'timestamp': '2020-02-02T08:17:25.532Z',
#   'total_avail_balance': '7.0000',
#   'unrealized_pnl': '0.0426'}}


def query_balance(symbol, contract=''):
    if contract == 'swap':
        suffix = '-SWAP'
        result = which_api.get_coin_account(symbol.replace('_', '-').upper() + suffix)['info']
    else:
        result = which_api.get_coin_account(symbol.replace('_', '-').upper())
    return float(result['equity'])


if __name__ == '__main__':
    pass
    # api_key = ""
    # seceret_key = ""
    # passphrase = ""

    # 资金账户API
    # account api test
    # param use_server_time's value is False if is True will use server timestamp
#    accountAPI = account.AccountAPI(api_key, seceret_key, passphrase, True)
# 获取资金账户信息 （20次/2s）
# result = accountAPI.get_wallet()
# 获取单一币种账户信息 （20次/2s）
# result = accountAPI.get_currency('usdt')
# 资金划转  1次/2s（每个币种）
# result = accountAPI.coin_transfer('ltc', '0.17', '1', '3', to_instrument_id='')
# 提币 （20次/2s）
# result = accountAPI.coin_withdraw('XRP', 1, 4, '17DKe3kkkkiiiiTvAKKi2vMPbm1Bz3CMKw', "123456", 0.0005)
# 账单流水查询 （可查询最近一个月）（20次/2s）
# result = accountAPI.get_ledger_record('okb')
# 获取充值地址 （20次/2s）
# result = accountAPI.get_top_up_address('xrp')
# 获取账户资产估值 （1次/20s）
# result = accountAPI.get_asset_valuation()
# 获取子账户余额信息 （1次/20s）
# result = accountAPI.get_sub_account('')
# 查询所有币种的提币记录 （最近100条记录）（20次/2s）
# result = accountAPI.get_coins_withdraw_record()
# 查询单个币种提币记录 （20次/2s）
# result = accountAPI.get_coin_withdraw_record('xrp')
# 获取所有币种充值记录 （最近100条数据）（20次/2s）
# result = accountAPI.get_top_up_records()
# 获取单个币种充值记录 （最近100条数据）（20次/2s）
# result = accountAPI.get_top_up_record('OKB')
# 获取币种列表 （20次/2s）
# result = accountAPI.get_currencies()
# 查询提币手续费 （20次/2s）
# result = accountAPI.get_coin_fee('EOS')

# print(time + json.dumps(result))
# logging.info("result:" + json.dumps(result))

# 币币API
# spot api test
#    spotAPI = spot.SpotAPI(api_key, seceret_key, passphrase, True)
# 获取币币账户信息 （20次/2s）
# result = spotAPI.get_account_info()
# 获取单一币种账户信息 （20次/2s）
# result = spotAPI.get_coin_account_info('usdt')
# 账单流水查询 最近3个月 （最近3个月的数据）（20次/2s）
# result = spotAPI.get_ledger_record('XRP')
# 下单 （100次/2s）
# result = spotAPI.take_order('xrp-usdt', 'sell', client_oid='', type='market', price='0.2266', notional='', size='5')

# take orders
# params = [
#   {"instrument_id": "XRP-USDT", "side": "sell", "type": "market", "size": "1"},
#   {"instrument_id": "XRP-USDT", "side": "buy", "type": "market", "notional": "0.3"}
# ]
# 批量下单 （每次只能下最多4个币对且每个币对可批量下10个单）（50次/2s）
# result = spotAPI.take_orders(params)
# 撤消指定订单 （100次/2s）
# result = spotAPI.revoke_order('XRP-USDT', order_id='3926884573645824')

# revoke orders
# 批量撤消订单 （每次只能下最多4个币对且每个币对可批量下10个单）（50次/2s）
# params = [
#     {'instrument_id': 'xrp-usdt', 'order_ids': ['3956994307262464']
#      }
# ]
# result = spotAPI.revoke_orders(params)
# 获取订单列表 （最近3个月的订单信息）（20次/2s）
# result = spotAPI.get_orders_list('XRP-USDT', '0')
# 获取所有未成交订单 （20次/2s）
# result = spotAPI.get_orders_pending('XRP-USDT')
# 获取订单信息 （最近3个月的订单信息）（已撤销的未成交单只保留2个小时）（20次/2s）
# result = spotAPI.get_order_info('XRP-USDT', 3937857243189248)
# 获取成交明细 （最近3个月的数据）（20次/2s）
# result = spotAPI.get_fills('btc-usdt')
# 委托策略下单 （40次/2s）
# result = spotAPI.take_order_algo('XRP-USDT', '1', '1', '1', 'buy', trigger_price='0.2893', algo_price='0.2894')
# 委托策略撤单 （每次最多可撤6（冰山/时间）/10（计划/跟踪）个）（20 次/2s）
# result = spotAPI.cancel_algos('XRP-USDT', ['377553'], '1')
# 获取当前账户费率 （1次/10s）
# result = spotAPI.get_trade_fee()
# 获取委托单列表 （20次/2s）
# result = spotAPI.get_order_algos('XRP-USDT', '1', status='3')
# 公共-获取币对信息 （20次/2s）
# result = spotAPI.get_coin_info()
# 公共-获取深度数据 （20次/2s）
# result = spotAPI.get_depth('XRP-USDT')
# 公共-获取全部ticker信息 （50次/2s）
# result = spotAPI.get_ticker()
# 公共-获取某个ticker信息 （20次/2s）
# result = spotAPI.get_specific_ticker('ETH-USDT')
# 公共-获取成交数据 （最近60条数据）（20次/2s）
# result = spotAPI.get_deal('XRP-USDT')
# 公共-获取K线数据（最多可获取最近2000条）（20次/2s）
# result = spotAPI.get_kline('XRP-USDT', 60)
# print(len(result))

# print(time + json.dumps(result))
# logging.info("result:" + json.dumps(result))

# 币币杠杆API
# level api test
#    levelAPI = lever.LeverAPI(api_key, seceret_key, passphrase, True)
# 币币杠杆账户信息 （20次/2s）
# result = levelAPI.get_account_info()
# 单一币对账户信息 （20次/2s）
# result = levelAPI.get_specific_account('XRP-USDT')
# 账单流水查询 （最近3个月的数据）（20次/2s）
# result = levelAPI.get_ledger_record('XRP-USDT')
# 杠杆配置信息 （20次/2s）
# result = levelAPI.get_config_info()
# 某个杠杆配置信息 （20次/2s）
# result = levelAPI.get_specific_config_info('XRP-USDT')
# 获取借币记录 （20次/2s）
# result = levelAPI.get_borrow_coin()
# 某币对借币记录 （20次/2s）
# result = levelAPI.get_specific_borrow_coin('BTC-USDT')
# 借币 （100次/2s）
# result = levelAPI.borrow_coin('BTC-USDT', 'usdt', '0.1')
# 还币 （100次/2s）
# result = levelAPI.repayment_coin('BTC-USDT', 'usdt', '0.1')
# 下单 （100次/2s）
# result = levelAPI.take_order('xrp-usdt', 'buy', '2', price='0.2806', size='2')

# take orders
# params = [
#   {"instrument_id": "xrp-usdt", "side": "buy", "type": "market", "notional": "2", "margin_trading": "2"},
#   {"instrument_id": "xrp-usdt", "side": "sell", 'price': '0.2806', "size": "5", "margin_trading": "2"}
# ]
# 批量下单 （每次只能下最多4个币对且每个币对可批量下10个单）（50次/2s）
# result = levelAPI.take_orders(params)
# 撤销指定订单 （100次/2s）
# result = levelAPI.revoke_order('xrp-usdt', order_id='')

# revoke orders
# params = [
#   {"instrument_id": "xrp-usdt", "order_ids": ['23464', '23465']},
#   {"instrument_id": "xrp-usdt", "client_oids": ['243464', '234465']}
# ]
# 批量撤销订单 （每个币对可批量撤10个单）（50次/2s）
# result = levelAPI.revoke_orders(params)

# 获取订单列表 （最近100条订单信息）（20次/2s）
# result = levelAPI.get_order_list('xrp-usdt', state='0')
# 获取订单信息 （已撤销的未成交单只保留2个小时）（20次/2s）
# result = levelAPI.get_order_info('xrp-usdt', client_oid='2244927451729920')
# 获取所有未成交订单 （20次/2s）
# result = levelAPI.get_order_pending('xrp-usdt')
# 获取成交明细 （最近3个月的数据）（20次/2s）
# result = levelAPI.get_fills('XRP-USDT')
# 获取杠杆倍数 （5次/2s）
# result = levelAPI.get_leverage('BTC-USDT')
# 设置杠杆倍数 （5次/2s）
# result = levelAPI.set_leverage('BTC-USDT', '7')

# print(time + json.dumps(result))
# logging.info("result:" + json.dumps(result))

# 交割合约API
# future api test
#    futureAPI = future.FutureAPI(api_key, seceret_key, passphrase, True)
# 所有合约持仓信息 （5次/2s）（根据userid限速）
# result = futureAPI.get_position()
# 单个合约持仓信息 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_specific_position('LTC-USD-191213')
# 所有币种合约账户信息 （1次/10s）（根据userid限速）
# result = futureAPI.get_accounts()
# 单个币种合约账户信息（币本位保证金合约的传参值为BTC-USD，USDT保证金合约的传参值为BTC-USDT）（20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_coin_account('LTC-USD')
# 获取合约币种杠杆倍数 （5次/2s）（根据underlying，分别限速）
# result = futureAPI.get_leverage('xrp-usd')
# 设定合约币种杠杆倍数 （5次/2s）（根据underlying，分别限速）
# 全仓
# result = futureAPI.set_leverage('XRP-USD', '30')
# 逐仓
# result = futureAPI.set_leverage('XRP-USD', '30', 'XRP-USD-191213', 'short')
# 账单流水查询 （最近2天的数据）（5次/2s）（根据underlying，分别限速）
# result = futureAPI.get_ledger('XRP-USD')
# 下单 （40次/2s）（根据underlying，分别限速）
# result = futureAPI.take_order('LTC-USD-191213', '1', '0.2243', '1', match_price='0')

# take orders
# 批量下单 （每个合约可批量下10个单）（20次/2s）（根据underlying，分别限速）
# orders = [
#           {"type": "1", "price": "0.2750", "size": "1"},
#           {"type": "2", "price": "0.2760", "size": "1"}
#           ]
# orders_data = json.dumps(orders)
# result = futureAPI.take_orders('XRP-USD-191227', orders_data=orders_data)
# 撤销指定订单 （40次/2s）（根据underlying，分别限速）
# result = futureAPI.revoke_order('XRP-USD-191227', '3995388789797889')
# 批量撤销订单 （每次最多可撤10个单）（20 次/2s）（根据underlying，分别限速）
# result = futureAPI.revoke_orders('XRP-USD-191227', order_ids=["3853889302246401", "3853889302246403"])
# 获取订单列表 （最近7天的数据）（20 次/2s）（根据underlying，分别限速）
# result = futureAPI.get_order_list('XRP-USD-191227', '0')
# 获取订单信息 （已撤销的未成交单只保留2个小时）（40次/2s）（根据underlying，分别限速）
# result = futureAPI.get_order_info('XRP-USD-191227', '3995388789797889')
# 获取成交明细 （最近7天的数据）（20 次/2s）（根据underlying，分别限速）
# result = futureAPI.get_fills('XRP-USD-191227')
# 设置合约币种账户模式 （5次/2s）（根据underlying，分别限速）
# result = futureAPI.set_margin_mode('LTC-USD', 'crossed')
# 市价全平 （5次/2s）（根据underlying，分别限速）
# result = futureAPI.close_position('XRP-USD-191227', 'long')
# 撤销所有平仓挂单 （5次/2s）（根据underlying，分别限速）
# result = futureAPI.cancel_all('XRP-USD-191227', 'long')
# 获取合约挂单冻结数量 （5次/2s）（根据underlying，分别限速）
# result = futureAPI.get_holds_amount('XRP-USD-191227')
# 委托策略下单 （40次/2s）（根据underlying，分别限速）
# result = futureAPI.take_order_algo('XRP-USD-191227', '1', '1', '1', trigger_price='0.2094', algo_price='0.2092')
# 委托策略撤单 （每次最多可撤6（冰山/时间）/10（计划/跟踪）个）（20 次/2s）（根据underlying，分别限速）
# result = futureAPI.cancel_algos('XRP-USD-191227', ['1907026'], '1')
# 获取委托单列表 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_order_algos('XRP-USD-191227', '1', status='2')
# 获取当前手续费费率 （1次/10s）
# result = futureAPI.get_trade_fee()
# 公共-获取合约信息 （20次/2s）（根据ip限速）
# result = futureAPI.get_products()
# 公共-获取深度数据 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_depth('XRP-USD-191227')
# 公共-获取全部ticker信息 （20次/2s）（根据ip限速）
# result = futureAPI.get_ticker()
# 公共-获取某个ticker信息 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_specific_ticker('XRP-USD-191227')
# 公共-获取成交数据 （最新300条成交列表）（20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_trades('XRP-USD-191227')
# 公共-获取K线数据 （最多可获取最近1440条）（20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_kline('BTC-USD-191227', '60')
# print(len(result))
# 公共-获取指数信息 （20次/2s）（根据ip限速）
# result = futureAPI.get_index('XRP-USD-191227')
# 公共-获取法币汇率 （20次/2s）（根据ip限速）
# result = futureAPI.get_rate()
# 公共-获取预估交割价 （交割预估价只有交割前一小时才有返回值）（20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_estimated_price('XRP-USD-191227')
# 公共-获取平台总持仓量 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_holds('XRP-USD-191227')
# 公共-获取当前限价 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_limit('XRP-USD-191227')
# 公共-获取标记价格 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_mark_price('XRP-USD-191227')
# 公共-获取强平单 （20次/2s）（根据underlying，分别限速）
# result = futureAPI.get_liquidation('XRP-USD-191227', 1)

# print(time + json.dumps(result))
# logging.info("result:" + json.dumps(result))

# 永续合约API
# swap api test
#    swapAPI = swap.SwapAPI(api_key, seceret_key, passphrase, True)
# 所有合约持仓信息 （1次/10s）
# result = swapAPI.get_position()
# 单个合约持仓信息 （20次/2s）
# result = swapAPI.get_specific_position('XRP-USD-SWAP')
# 所有币种合约账户信息 （当用户没有持仓时，保证金率为10000）（1次/10s）
# result = swapAPI.get_accounts()
# 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
# result = swapAPI.get_coin_account('XRP-USD-SWAP')
# 获取某个合约的用户配置 （5次/2s）
# result = swapAPI.get_settings('XRP-USD-SWAP')
# 设定某个合约的杠杆 （5次/2s）
# result = swapAPI.set_leverage('XRP-USD-SWAP', 10, 1)
# 账单流水查询 （流水会分页，每页100条数据，并且按照时间倒序排序和存储，最新的排在最前面）（可查询最近7天的数据）（5次/2s）
# result = swapAPI.get_ledger('XRP-USD-SWAP')
# 下单 （40次/2s）
# result = swapAPI.take_order('BTC-USDT-SWAP', '1', '3', '0.2608', match_price='0')
# 批量下单 （每个合约可批量下10个单）（20次/2s）
# result = swapAPI.take_orders('XRP-USD-SWAP', [
#         {"type": "1", "price": "0.2600", "size": "1"},
#         {"type": "2", "price": "0.2608", "size": "1"}
#     ])
# 撤单 （40次/2s）
# result = swapAPI.revoke_order('XRP-USD-SWAP', '369874940524453888')
# 批量撤单 （每个币对可批量撤10个单）（20次/2s）
# result = swapAPI.revoke_orders('XRP-USD-SWAP', ids=["3698749403525888", "369874940532842496"])
# 获取所有订单列表 （可查询最近7天20000条数据，支持分页，分页返回结果最大为100条）（20次/2s）
# result = swapAPI.get_order_list('XRP-USD-SWAP', '0')
# 获取订单信息 （只能查询最近3个月的已成交和已撤销订单信息，已撤销的未成交单只保留2个小时）（40次/2s）
# result = swapAPI.get_order_info('XRP-USD-SWAP', '369856427972321280')
# 获取成交明细 （能查询最近7天的数据）（20次/2s）
# result = swapAPI.get_fills('XRP-USD-SWAP')
# 获取合约挂单冻结数量 （5次/2s）
# result = swapAPI.get_holds_amount('XRP-USD-SWAP')
# 委托策略下单 （40次/2s）
# result = swapAPI.take_order_algo('XRP-USD-SWAP', '1', '1', '1', trigger_price='0.2640', algo_price='0.2641')
# 委托策略撤单 （每次最多可撤6（冰山/时间）/10（计划/跟踪）个）（20 次/2s）
# result = swapAPI.cancel_algos('XRP-USD-SWAP', ['367645536490315776'], '1')
# 获取委托单列表 （20次/2s）
# result = swapAPI.get_order_algos('XRP-USD-SWAP', '1', algo_id='', status='2')
# 获取账户手续费费率 （母账户下的子账户的费率和母账户一致。每天凌晨0点更新一次）（1次/10s）
# result = swapAPI.get_trade_fee()
# 公共-获取合约信息 （20次/2s）
# result = swapAPI.get_instruments()
# 公共-获取深度数据 （20次/2s）
# result = swapAPI.get_depth('BTC-USD-SWAP', '3', '1')
# 公共-获取全部ticker信息 （20次/2s）
# result = swapAPI.get_ticker()
# 公共-获取某个ticker信息 （20次/2s）
# result = swapAPI.get_specific_ticker('XRP-USD-SWAP')
# 公共-获取成交数据 （能查询最近300条数据）（20次/2s）
# result = swapAPI.get_trades('XRP-USD-SWAP')
# 公共-获取K线数据 （最多可获取最近1440条）（20次/2s）
# result = swapAPI.get_kline('XRP-USD-SWAP', '2019-09-29T07:59:45.977Z', '2019-09-29T16:59:45.977Z', 60)
# 公共-获取指数信息 （20次/2s）
# result = swapAPI.get_index('XRP-USD-SWAP')
# 公共-获取法币汇率 （20次/2s）
# result = swapAPI.get_rate()
# 公共-获取平台总持仓量 （20次/2s）
# result = swapAPI.get_holds('XRP-USD-SWAP')
# 公共-获取当前限价 （20次/2s）
# result = swapAPI.get_limit('XRP-USD-SWAP')
# 公共-获取强平单 （20次/2s）
# result = swapAPI.get_liquidation('XRP-USD-SWAP', '1')
# 公共-获取合约资金费率 （20次/2s）
# result = swapAPI.get_funding_time('XRP-USD-SWAP')
# 公共-获取合约标记价格 （20次/2s）
# result = swapAPI.get_mark_price('XRP-USD-SWAP')
# 公共-获取合约历史资金费率 （能查询最近7天的数据）（20次/2s）
# result = swapAPI.get_historical_funding_rate('XRP-USD-SWAP')

# 指数API
# index api test
#    indexAPI = index.IndexAPI(api_key, seceret_key, passphrase, True)
# 公共-获取指数成分 （20次/2s）
# result = indexAPI.get_index_constituents('BTC-USD')

# 期权合约API
# option api test
#    optionAPI = option.OptionAPI(api_key, seceret_key, passphrase, True)
# 单个标的指数持仓信息 （20次/2s）
# result = optionAPI.get_specific_position('TBTC-USD')
# 单个标的物账户信息 （20次/2s）
# result = optionAPI.get_underlying_account('TBTC-USD')
# 下单 （40次/2s）
# result = optionAPI.take_order('TBTC-USD-191213-7000-C', 'buy', '', '1', match_price='1')
# 批量下单 （每个标的指数最多可批量下10个单）（20次/2s）
# result = optionAPI.take_orders('TBTC-USD', [
#         {"instrument_id": "TBTC-USD-191213-6000-C", "side": "buy", "price": "0.1835", "size": "1", "order_type": "0", "match_price": "0"},
#         {"instrument_id": "TBTC-USD-191213-7000-P", "side": "buy", "price": "0.0126", "size": "1", "order_type": "0", "match_price": "0"}
#     ])
# 撤单 （40次/2s）
# result = optionAPI.revoke_order('TBTC-USD', order_id='125259570520055808')
# 批量撤单 （每个标的指数最多可批量撤10个单）（20次/2s）
# result = optionAPI.revoke_orders('TBTC-USD', order_ids=["155801767097874432", "155803099442657280"])
# 修改订单 （每个标的指数最多可批量修改10个单）（40次/2s）
# result = optionAPI.amend_order('TBTC-USD', order_id='155801767097874432', new_price='0.0311', new_size='5')
# 批量修改订单 （20次/2s）
# result = optionAPI.amend_batch_orders('BTC-USD', [
#         {"order_id": "oktoption12", "new_size": "2"},
#         {"client_oid": "oktoption14", "request_id": "okoptionBTCUSDmod002", "new_size": "1"}
#     ])
# 获取单个订单状态 （已撤销的未成交单只保留2个小时）（40次/2s）
# result = optionAPI.get_order_info('TBTC-USD', order_id='158641967489658880')
# 获取订单列表 （可查询7天内数据）（20次/2s）
# result = optionAPI.get_order_list('TBTC-USD', '0')
# 获取成交明细 （可查询7天内数据）（20次/2s）
# result = optionAPI.get_fills('TBTC-USD')
# 获取账单流水 （可查询7天内数据）（5次/2s）
# result = optionAPI.get_ledger('TBTC-USD')
# 获取手续费费率 （1次/10s）
# result = optionAPI.get_trade_fee()
# 公共-获取标的指数 （20次/2s）
# result = optionAPI.get_index()
# 公共-获取期权合约 （20次/2s）
# result = optionAPI.get_instruments('TBTC-USD')
# 公共-获取期权合约详细定价 （20次/2s）
# result = optionAPI.get_instruments_summary('TBTC-USD')
# 公共-获取单个期权合约详细定价 （20次/2s）
# result = optionAPI.get_option_instruments_summary('TBTC-USD', 'TBTC-USD-191213-7500-C')
# 公共-获取深度数据 （20次/2s）
# result = optionAPI.get_depth('TBTC-USD-191213-7500-C')
# 公共-获取成交数据 （20次/2s）
# result = optionAPI.get_trades('TBTC-USD-191213-7500-C')
# 公共-获取某个Ticker信息 （20次/2s）
# result = optionAPI.get_specific_ticker('TBTC-USD-191213-7500-C')
# 公共-获取K线数据 （20次/2s）
# result = optionAPI.get_kline('TBTC-USD-191213-7500-C')

#    print(time + json.dumps(result))
#    logging.info("result:" + json.dumps(result))
