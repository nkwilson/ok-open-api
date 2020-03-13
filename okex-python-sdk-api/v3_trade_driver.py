# -*- coding: utf-8 -*-

import sys
import traceback

import datetime

import os
import time
import random
import math
from datetime import datetime as dt

import subprocess
from subprocess import PIPE

import logging

import locale

# import trade_elite
import json

from optparse import OptionParser

# backend = __import__('%s_trade_backend' % options.api_version)
import v3_trade_backend as backend

default_encoding = locale.getpreferredencoding(False)

startup_notify = ''
shutdown_notify = ''

limit_direction = ''  # 'buy'/'sell'


def check_limit_direction(direction):
    return limit_direction == '' or limit_direction == direction


limit_price = 0
limit_symbol = ''
limit_amount = 0

parser = OptionParser()
parser.add_option("", "--signal_notify", dest="signal_notify", help="specify signal notifier")
parser.add_option("", "--startup_notify", dest="startup_notify", help="specify startup notifier")
parser.add_option("", "--shutdown_notify", dest="shutdown_notify", help="specify shutdown notifier")
parser.add_option('',
                  '--emulate',
                  dest='emulate',
                  action="store_true",
                  default=False,
                  help="try to emulate trade notify")
parser.add_option('',
                  '--skip_gate_check',
                  dest='skip_gate_check',
                  action="store_false",
                  default=True,
                  help="Should skip checking gate when open trade")
parser.add_option('', '--cmp_scale', dest='cmp_scale', default='1', help='Should multple it before do compare')
parser.add_option('', '--which_ema', dest='which_ema', default=0, help='using with one of ema')
parser.add_option('', '--order_num', dest='order_num', help='how much orders')
parser.add_option('', '--fee_amount', dest='fee_amount', help='take amount int account with fee')
parser.add_option('',
                  '--signal',
                  dest='signals',
                  default=['tit2tat'],
                  action='append',
                  help='use wich signal to generate trade notify and also as prefix, boll, simple, tit2tat')
parser.add_option('', '--latest', dest='latest_to_read', default='1000', help='only keep that much old values')
parser.add_option('', '--dir', dest='dirs', default=[], action='append', help='target dir should processing')
parser.add_option('', '--bins', dest='bins', default=0, help='wait how many reverse, 0=once, 1=twice')
parser.add_option('', '--nolog', dest='nolog', action='store_true', default=False, help='Do not log to file')
parser.add_option('', '--ratio', dest='amount_ratio', default=9, help='default trade ratio of total amount')
parser.add_option('', '--previous_close', dest='previous_close', help='init previous_close')
parser.add_option('',
                  '--restore_status',
                  dest='restore_status',
                  action='store_false',
                  default=True,
                  help='restore status from status_file')
parser.add_option('',
                  '--one_shot',
                  dest='one_shot',
                  action='store_true',
                  default=False,
                  help='just run once, save status and quit')
parser.add_option('',
                  '--self_trigger',
                  dest='do_self_trigger',
                  action='store_false',
                  default=True,
                  help='read price by myself and do following trade')
parser.add_option('',
                  '--noaction',
                  dest='noaction',
                  action='store_true',
                  default=False,
                  help='dry run, no real buy/sell action')
parser.add_option('', '--api', dest='api_version', default='v3', help='use specified api version[v1|v3], default is v3')

(options, args) = parser.parse_args()
print(type(options), options, args)


# demo: ok_sub_futureusd_btc_kline_quarter_4hou


def figure_out_symbol_info(path):
    path = os.path.splitext(path)[0]
    start_pattern = 'ok_sub_future'
    end_pattern = '_kline_'
    start = path.index(start_pattern) + len(start_pattern)
    end = path.index(end_pattern)
    # print('symbol is %s' % (path[start:end]))
    return path[start:end]


def figure_out_contract_info(path):
    path = os.path.splitext(path)[0]
    start_pattern = 'kline_'
    end_pattern = '_'
    start = path.index(start_pattern) + len(start_pattern)
    end = path.rindex(end_pattern)
    # print('contract is %s' % (path[start:end]))
    return path[start:end]


def figure_out_period_info(path):
    path = os.path.splitext(path)[0]
    start_pattern = '_'
    start = path.rindex(start_pattern) + len(start_pattern)
    # print('period is %s' % (path[start:]))
    return path[start:]


order_infos = {
    'usd_btc': 'btc_usd',
    'usd_ltc': 'ltc_usd',
    'usd_eth': 'eth_usd',
    'usd_eos': 'eos_usd',
    'usd_bch': 'bch_usd',
    'usd_xrp': 'xrp_usd',
    'sell': {
        'open': backend.open_order_sell_rate,
        'close': backend.close_order_sell_rate
    },
    'buy': {
        'open': backend.open_order_buy_rate,
        'close': backend.close_order_buy_rate
    }
}

fast_issue = 1  # use optimized price to finish order as fast as possible

reissuing_order = 0
wait_for_completion = 1  # default is no wait


def issue_order_now(symbol, contract, direction, amount, action, price=''):
    global reissuing_order, wait_for_completion
    # print(symbol, direction, amount, action)
    raw_result = order_infos[direction][action](symbol, contract, amount, price)
    if type(raw_result) == dict:
        result = raw_result
    else:
        result = json.loads(raw_result)
    # print(result)
    if not result['result'] or result['result'] == 'false':
        print(result)
        reissuing_order += 1
        if amount < 2:
            return (False, 0, 0)
        return issue_order_now(symbol, contract, direction, amount / 2, action, price)
    order_id = str(result['order_id'])  # no exceptions, means successed
    # print(order_id)
    if wait_for_completion > 0:  # only valid if positive
        time.sleep(wait_for_completion)
    if not price:  # if empty, must wait for complete
        order_info = backend.query_orderinfo_wait(symbol, contract, order_id)
    else:
        order_info = backend.query_orderinfo(symbol, contract, order_id)
    try:  # in case amount too much
        price = float(order_info['price_avg'])
        if price == 0 and globals()['fast_issue']:
            price = float(globals()['request_price'])  # use last saved price in request_price
        if price == 0:
            price = float(globals()['current_close'])
        # print(order_info, 'current_close = %.4f' % (globals()['current_close']))
        # print(order_info)
        if order_info['filled_qty'] != order_info['size']:
            if wait_for_completion == 0:  # it's ok
                # no update for last_fee
                return (True, price, float(order_info['size']))
            else:  # should wait
                amount -= int(order_info['filled_qty'])
                reissuing_order += 1
        else:
            globals()['last_fee'] = abs(float(order_info['fee']))
            return (True, price, float(order_info['size']))
    except Exception as ex:
        print(ex)
        if amount < 2:  # no balance now
            return (False, 0, 0)
        reissuing_order += 1
        amount = amount / 2
    if contract == 'swap':  # temp logic
        return (False, 0, 0)
    if reissuing_order > 60:  # more than 60 , quit
        reissuing_order = 0
        return (False, 0, 0)
    print('try to cancel pending order and reissue', ' amount = %d' % amount)
    try:
        backend.cancel_order(symbol, contract, order_id)
    except Exception as ex:
        print(ex)
        # API Request Error(code=35065): This type of order cannot be canceled
        # API Request Error(code=35014): Order price is not within limit
        return (False, 0, 0)
    return issue_order_now(symbol, contract, direction, amount, action, price)


def adjust_with_delta(old_price, delta_price, direction):
    if direction == 'sell':
        return old_price + delta_price
    else:  # buy
        return old_price - delta_price


# orders need to close, sorted by price
orders_holding = {'sell': {'reverse': False, 'holding': list()}, 'buy': {'reverse': True, 'holding': list()}}

# cleanup holdings, only when holding of quarter_amount, simplifiy logic, just cleanup all of holdings


def cleanup_holdings_atopen(symbol, contract, direction, amount, price):  # only keep amount around price
    holding = orders_holding[direction]['holding']
    if len(holding) < int(globals()['greedy_count_max']) + 2:  # it's ok to keep some as unbalanced
        return
    (loss, t_amount, leverage) = backend.check_holdings_profit(symbol, contract, direction)
    total_amounts = sum([float(x[1]) for x in holding])
    total_ticks = sum([float(x[1]) * float(x[0]) for x in holding])

    globals()['amount_ratio'] = leverage

    orders_holding[direction]['holding'].clear()

    # get real start price
    adj_price = total_ticks / total_amounts

    orders_holding[direction]['holding'].append((adj_price, t_amount))
    print(trade_timestamp(),
          '    atopen price adjust to %.4f, cleanup %d, left %d' % (adj_price, total_amounts - t_amount, t_amount))


def cleanup_holdings_atclose(symbol, contract, direction, amount, price):  # only keep amount around price
    holding = orders_holding[direction]['holding']
    if len(holding) != 1:  # only when single
        return
    (loss, t_amount, leverage) = backend.check_holdings_profit(symbol, contract, direction)
    total_amounts = holding[0][1]

    # get real start price
    if direction == 'buy':
        origin_price = price * 100 / (100 + loss / leverage)
    else:
        origin_price = price * 100 / (100 - loss / leverage)
    globals()['amount_ratio'] = leverage

    orders_holding[direction]['holding'][0] = (origin_price, t_amount)
    print(trade_timestamp(),
          '    atclose price adjust to %.4f, cleanup %d, left %d' % (origin_price, total_amounts - t_amount, t_amount))


# for both open and close


def issue_order_now_conditional(symbol, contract, direction, amount, action, must_positive=True):
    if action == 'open':
        return issue_order_now(symbol, contract, direction, amount, action,
                               '' if globals()['fast_issue'] else globals()['request_price'])
    (loss, t_amount, leverage) = backend.check_holdings_profit(symbol, contract, direction)
    if t_amount == 0:
        return (False, 0, 0)  # no operation (ret, price, amount)
    holding = orders_holding[direction]['holding']
    l_reverse = orders_holding[direction]['reverse']
    # print(holding)
    if len(holding) > 1:
        orders_holding[direction]['holding'] = [(float(x[0]), float(x[1])) for x in holding]
        holding = orders_holding[direction]['holding']
        holding.sort(reverse=l_reverse)
    if not must_positive:
        if amount == 0:
            holding.clear()
            amount = t_amount
        else:
            amount = min(t_amount, amount)  # get little one
            total_amount = 0
            while len(holding) > 0:
                (price, l_amount) = holding.pop()
                total_amount += l_amount
                if amount > 0 and total_amount > amount:
                    holding.append((price, total_amount - amount))
                    break
        (ret, price, amount) = issue_order_now(symbol, contract, direction, amount, action,
                                               '' if globals()['fast_issue'] else globals()['request_price'])
        print('loss ratio=%f%%, %s, closed %d' % (loss, 'yeap' if loss > 0 else 'tough', amount))
        orders_holding[direction]['holding'] = holding
        return (ret, price, amount)
    total_amount = 0
    addon = ''
    saved_amount = amount
    amount = min(t_amount, amount)  # get little on
    price = 0
    ret = False
    while len(holding) > 0:
        (price, l_amount) = holding.pop()
        if globals()['positive_greedy_profit'](price, direction):
            # print('(%s, %s) selected' % (price, l_amount))
            total_amount += l_amount
            if amount > 0 and total_amount > amount:
                holding.append((price, total_amount - amount))
                total_amount = amount
                break
        else:  # not positive
            holding.append((price, l_amount))  # put it back
            break
    if len(holding) == 0 and total_amount == 0:  # just use input amount
        total_amount = amount
    if total_amount > 0:  # yes, has positive holdings
        (ret, price, amount) = issue_order_now(symbol, contract, direction, total_amount, action,
                                               '' if globals()['fast_issue'] else globals()['request_price'])
        addon = ' (%d required, %d closed, %d left)' % (saved_amount, total_amount, (t_amount - total_amount))
        total_amount = amount
    orders_holding[direction]['holding'] = holding
    print('loss ratio=%f%%, keep holding%s' % (loss, addon))
    return (ret, price, total_amount)


def issue_quarter_order_now_conditional(symbol, direction, amount, action, must_positive=True):
    print('EMUL ' if options.noaction else '', 'issue quarter order%s: ' % (' conditional' if must_positive else ''),
          action, symbol, direction, amount)
    if options.noaction:
        return 0
    (ret, price, amount) = issue_order_now_conditional(symbol,
                                                       globals()['contract'], direction, amount, action, must_positive)
    if ret and action == 'open':
        orders_holding[direction]['holding'].append((price, amount))
    return (ret, price, amount)


def issue_quarter_order_now(symbol, direction, amount, action):
    return issue_quarter_order_now_conditional(symbol, direction, amount, action, must_positive=False)


old_open_price = 0
old_close_mean = 0
trade_file = ''
levage_rate = 20

symbols_mapping = {
    'usd_btc': 'btc_usd',
    'usd_ltc': 'ltc_usd',
    'usd_eth': 'eth_usd',
    'usd_eos': 'eos_usd',
    'usd_xrp': 'xrp_usd',
    'usd_bch': 'bch_usd'
}


def trade_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# open sell order now


def signal_open_order_with_sell(l_index, filename, close, multiple=False):
    if not options.emulate and os.path.isfile(filename):  # already ordered
        return
    mode = 'w' if not multiple else 'a'
    append = '' if not multiple else '\n'
    line = '%s sell at %0.7f%s' % (l_index, close, append)
    with open(filename, mode) as f:
        f.write(line)
        f.close()
    print(trade_timestamp(), line.rstrip('\n'))
    global trade_notify
    with open(trade_notify, 'w') as f:
        f.write('%s.open' % filename)
        f.close()


# close sell order now


def signal_close_order_with_buy(l_index, filename, close):
    if not os.path.isfile(filename):  # no order opened
        return
    line = ' closed at %s with %0.7f\n' % (l_index, close)
    with open(filename, 'a') as f:
        f.write(line)
        f.close()
    print(trade_timestamp(), line.rstrip('\n'), flush9=True)
    global trade_notify
    with open(trade_notify, 'w') as f:
        f.write('%s.close' % filename)
        f.close()


# open buy order now


def signal_open_order_with_buy(l_index, filename, close, multiple=False):
    if not options.emulate and os.path.isfile(filename):  # already ordered
        return
    mode = 'w' if not multiple else 'a'
    append = '' if not multiple else '\n'
    line = '%s buy at %0.7f%s' % (l_index, close, append)
    with open(filename, mode) as f:
        f.write(line)
        f.close()
    print(trade_timestamp(), line.rstrip('\n'))
    global trade_notify
    with open(trade_notify, 'w') as f:
        f.write('%s.open' % filename)
        f.close()


# close buy order now


def signal_close_order_with_sell(l_index, filename, close):
    if not os.path.isfile(filename):  # no order opened
        return
    line = ' closed at %s with %0.7f\n' % (l_index, close)
    with open(filename, 'a') as f:
        f.write(line)
        f.close()
    print(trade_timestamp(), line.rstrip('\n'), flush=True)
    global trade_notify
    with open(trade_notify, 'w') as f:
        f.write('%s.close' % filename)
        f.close()


def generate_trade_filename_new(dir, l_index, order_type, prefix=''):
    fname = '%s-%strade.%s' % (l_index, prefix, order_type)
    return os.path.join(dir, fname)


def generate_trade_filename(dir, l_index, order_type):
    global l_prefix
    global new_trade_file
    return generate_trade_filename_new(dir, l_index, order_type, l_prefix)


# open, high, low, close == 4 prices


def read_4prices(filename):
    prices = None
    # drop suffix
    filename = os.path.splitext(filename)[0]
    # print(filename)
    if not os.path.isfile(filename):  # in case not exist
        return prices
    try:
        with open(filename, 'r') as f:
            line = f.readline().rstrip('\n')
            # print(line, eval(line))
            prices = [float(x) for x in eval(line)]
            # print(prices)
            f.close()
            # close = eval(f.readline())[3]
    except Exception as ex:
        print(ex)
        print('read_4prices: %s' % filename)
    # print(close)
    return prices


# previou is calcuated ema with period , re


def get_ema(previous, new_data, period):
    return (previous * (period - 1) + 2 * new_data) / (period + 1)


open_price = 0
previous_close = 0
current_close = 0
last_bond = 0  # means uninitialized
last_balance = 0
last_decision_logic = ''

ID_OPEN = 0
ID_HIGH = 1
ID_LOW = 2
ID_CLOSE = 3


def try_loadsave_with_names(status, names, load):
    if not load:
        globals()[status].clear()
    for name in globals()[names]:
        if load:  # from status to individual names
            if name in globals()[status].keys():  # in case name not exist
                globals()[name] = globals()[status][name]
        else:  # collect individual names to status
            globals()[status][name] = globals()[name]


def loadsave_status(signal, load):
    if load:  # load from file
        mode = 'r'
    else:  # save to file
        mode = 'w'
    # process file
    with open(globals()['status_file'], mode) as f:
        if load:
            globals()['trade_status'] = json.load(f)
            try_loadsave_with_names('trade_status', 'names_%s' % signal, load)
        else:
            try_loadsave_with_names('trade_status', 'names_%s' % signal, load)
            json.dump(globals()['trade_status'], f)
        f.close()


names_tit2tat = [
    'trade_file', 'previous_close', 'open_price', 'open_cost', 'open_cost_rate', 'open_greedy', 'quarter_amount',
    'thisweek_amount_pending', 'quarter_amount_multiplier', 'greedy_count', 'greedy_count_max', 'greedy_whole_balance',
    'greedy_same_amount', 'last_balance', 'last_bond', 'update_quarter_amount_forward',
    'update_quarter_amount_backward', 'profit_cost_multiplier', 'greedy_cost_multiplier', 'last_fee', 'amount_ratio',
    'amount_ratio_plus', 'amount_real', 'orders_holding', 'ema_1', 'ema_1_up', 'ema_1_lo', 'ema_period_1', 'ema_2',
    'ema_2_up', 'ema_2_lo', 'ema_period_2', 'forward_greedy', 'backward_greedy', 'fast_issue', 'open_cost_rate',
    'request_price', 'wait_for_completion', 'reverse_amount_rate'
]


def save_status_tit2tat(subpath=''):
    loadsave_status('tit2tat', load=False)
    with open(globals()['status_file'], 'r') as r:
        with open('%s.trade_status' % (subpath), 'w') as w:
            w.write(r.read())  # read whole file and write all
            w.close()
        r.close()


def load_status_tit2tat(subpath=''):
    loadsave_status('tit2tat', load=True)


def get_greedy_tiny_delta(price):
    # print('greedy delta', globals()['previous_close'], price)
    return 10 * (globals()['previous_close'] - price)  # 'previous_close is update to current price'


def get_greedy_delta(price):
    # print('greedy delta', globals()['previous_close'], price)
    return globals()['previous_close'] - price  # 'previous_close is update to current price'


def get_normal_delta(price):
    # print('normal delta', price, globals()['open_price'])
    return price - globals()['open_price']


profit_policy = {
    'greedy-tiny': {
        'multiplier': 'greedy_cost_multiplier',
        'get_delta': get_greedy_tiny_delta
    },
    'greedy': {
        'multiplier': 'greedy_cost_multiplier',
        'get_delta': get_greedy_delta
    },
    'normal': {
        'multiplier': 'profit_cost_multiplier',
        'get_delta': get_normal_delta
    },
    'trans': {
        'buy': 1,
        'sell': -1
    }
}


def positive_profit_with(price, direction, typeof):
    cost = globals()[profit_policy[typeof]['multiplier']] * globals()['open_cost']
    delta = profit_policy[typeof]['get_delta'](price)
    trans = profit_policy['trans'][direction]
    # print(delta * trans, cost, delta * trans > cost)
    return delta * trans > cost


def positive_greedy_profit(price, direction):
    return positive_profit_with(price, direction, 'greedy')


def positive_greedy_tiny_profit(price, direction):
    return positive_profit_with(price, direction, 'greedy-tiny')


def positive_normal_profit(price, direction):
    return positive_profit_with(price, direction, 'normal')


def update_last_bond(symbol, contract, direction):
    t_bond = backend.query_bond(symbol, contract, direction)
    if t_bond > 0:
        globals()['last_bond'] = t_bond


def update_open_cost(price):
    if float(globals()['open_cost_rate']) > 0:
        globals()['open_cost'] = previous_close * float(globals()['open_cost_rate'])


# when do greedy trade, should choose aproperiate open_cost_rate x and reverse_amount_rate p
# assume leverage is 21, buy amount is 0.05, total is 21 * 0.05 = 1.05
# 0.0015 is open fee rate, 0.03 is close fee rate
# using this formula:
# 1.05 * (0.0015 + 0.003) * ( 1 + p) <= 1.05 * ( 1 - p) * x * 21
# 0.0045 / 21 * (1 + p) / ( 1 - p ) <= x
# let t = x * 21 / 0.0045
# p <=  (t - 1)/(t + 1)
# if x = 0.008, p should less than 0.947
# if x = 0.005, p should less than 0.917
# if x = 0.0055, p should less than 0.924
# if x = 0.0048, p should less than 0.914
# if x = 0.004,  p should less than 0.898
# [0.0035, 0.884]
# [0.003,  0.866]
# [0.002,  0.806]
# if leverage is 11
# [0.005, 0.848]
# if leverage is 13
# [0.005, 0.87]
request_price = '0'
last_fee = 0
open_cost = 0
open_cost_rate = 0.005  # percent of previous_close
reverse_amount_rate = 0.85
quarter_amount = 1
thisweek_amount_pending = 0
quarter_amount_multiplier = 2  # 2 times is up threshold
greedy_count_max = 1  # limit this times pending greedy
greedy_count = 0  # current pending greedy
greedy_whole_balance = False  # greedy will cover whole balance
greedy_same_amount = False  # greedy use the same as quarter_amount
close_greedy = False
open_greedy = False
amount_ratio_plus = 0.05  # percent of total amount
profit_cost_multiplier = 0.2  # times of profit with open_cost
greedy_cost_multiplier = 1  # times of greedy with open_cost
amount_real = 0.05  # supercede on amount_ratio, as percent of amount
ema_period_1 = 2  # signal period
ema_period_2 = 20  # tendency period
ema_1 = 0
ema_2 = 0
ema_1_up = 0  # up means high price
ema_1_lo = 0  # lo means low price
ema_2_up = 0
ema_2_lo = 0
forward_greedy = True  # following tendency
backward_greedy = False  # following reverse tendency
update_quarter_amount_forward = True  # update it if balance increase
update_quarter_amount_backward = False  # update it if balance decrease


def try_to_trade_tit2tat(subpath):
    global trade_file, old_close_mean
    global old_open_price
    global old_close, bins, direction
    global l_trade_file
    global previous_close
    global open_greedy, close_greedy
    global open_price
    global open_cost
    global quarter_amount, thisweek_amount_pending
    global last_bond, last_balance
    global last_decision_logic
    global ema_1, ema_1_up, ema_1_lo
    global ema_2, ema_2_up, ema_2_lo
    global forward_greedy, backward_greedy
    global update_quarter_amount_forward, update_quarter_amount_backward
    global greedy_count, greedy_count_max

    globals()['request_price'] = ''  # first clear it

    greedy_status = ''
    # print(subpath)
    event_path = subpath
    l_index = os.path.basename(event_path)
    # print(l_index, event_path)
    prices = read_4prices(event_path)
    close = prices[ID_CLOSE]
    l_dir = ''
    reverse_follow_dir = ''
    if trade_file.endswith('.sell'):  # sell order
        l_dir = 'sell'
        reverse_follow_dir = 'buy'
    elif trade_file.endswith('.buy'):  # buy order
        l_dir = 'buy'
        reverse_follow_dir = 'sell'
    new_ema_1 = get_ema(ema_1, close, ema_period_1)
    new_ema_2 = get_ema(ema_2, close, ema_period_2)
    new_ema_1_up = get_ema(ema_1_up, prices[ID_HIGH], ema_period_1)
    new_ema_1_lo = get_ema(ema_1_lo, prices[ID_LOW], ema_period_1)
    new_ema_2_up = get_ema(ema_2_up, prices[ID_HIGH], ema_period_2)
    new_ema_2_lo = get_ema(ema_2_lo, prices[ID_LOW], ema_period_2)
    delta_ema_1 = new_ema_1 - ema_1
    price_delta = 0

    globals()['current_close'] = close  # save early

    print('')  # add an empty line
    if trade_file == '':
        print('%.4f' % close, '-', 'ema_%d:%.4f' % (ema_period_1, new_ema_1),
              'ema_%d:%.4f' % (ema_period_2, new_ema_2))
    elif l_dir == 'sell':  # sell order
        ema_tendency = new_ema_2 - new_ema_1_lo  # ema_2 should bigger than ema_1_lo
        price_delta = (previous_close - close)
        ema_tuple = 'ema_%d/ema_%d: %.4f => %.4f' % (ema_period_1, ema_period_2, new_ema_1_lo, new_ema_2)
        print('%.4f' % -close, '%.4f' % previous_close, l_dir, end=' ')
    elif l_dir == 'buy':  # buy order
        ema_tendency = new_ema_1_up - new_ema_2  # ema_1_up should bigger than ema_2
        price_delta = (close - previous_close)
        ema_tuple = 'ema_%d/ema_%d: %.4f <= %.4f' % (ema_period_1, ema_period_2, new_ema_1_up, new_ema_2)
        print('%.4f' % close, '%.4f' % -previous_close, l_dir, end=' ')
    if len(l_dir):
        print(ema_tuple,
              'greedy: %.1f' % greedy_count,
              'cost: %.5f @ %.5f/%.2f%%' % (price_delta, open_cost, 100 * float(globals()['open_cost_rate'])),
              'balance: %.2f' % (globals()['last_balance']),
              'amount: %d/%d' % (globals()['quarter_amount'], globals()['thisweek_amount_pending']))

    ema_1 = new_ema_1  # saved now
    ema_1_up = new_ema_1_up
    ema_1_lo = new_ema_1_lo
    ema_2 = new_ema_2  # saved now
    ema_2_up = new_ema_2_up
    ema_2_lo = new_ema_2_lo
    if close == 0:  # in case read failed
        return
    if previous_close == 0:
        previous_close = close
        close_greedy = False
        return

    symbol = symbols_mapping[figure_out_symbol_info(event_path)]

    new_open = True
    forced_close = False
    if trade_file != '':
        new_open = False
        if l_dir == 'buy':
            delta = open_price - prices[ID_LOW]
        else:  # sell
            delta = prices[ID_HIGH] - open_price
        if delta < 0.001:  # zero means too small
            t_amount = 1
        else:
            t_amount = open_price - delta * amount_ratio  # calcuate by forced close probability
        if not options.emulate:  # if emualtion, figure it manually
            (loss, t_amount, leverage) = backend.check_holdings_profit(symbol, globals()['contract'], l_dir)
            globals()['amount_ratio'] = leverage
        if t_amount <= 0:
            # open it un-conditionally
            issue_quarter_order_now(symbol, l_dir, 1, 'open')
            # check if should take normal close action
            forced_close = True
        else:
            thisweek_amount_pending = math.ceil(t_amount - quarter_amount)
            if thisweek_amount_pending == 0:  # zero greedy count?
                greedy_count = greedy_count_max
    if forced_close:
        open_greedy = True
        # suffered forced close
        globals()['signal_close_order_with_%s' % l_dir](l_index, trade_file, close)
        print(trade_timestamp(), 'detected forced close signal %s at %s => %s' % (l_dir, previous_close, close))
        # action likes new_open equals true, but take original l_dir as it
        mini_amount = max(1, math.ceil(quarter_amount / 8))
        issue_quarter_order_now(symbol, l_dir, mini_amount, 'open')
        # clear it
        thisweek_amount_pending = 0
        (open_price,
         no_use) = backend.real_open_price_and_cost(symbol,
                                                    globals()['contract'], l_dir) if not options.emulate else (close,
                                                                                                               0.001)
    new_l_dir = ''
    if close > previous_close and delta_ema_1 > 0:
        new_l_dir = 'buy'
    elif close < previous_close and delta_ema_1 < 0:
        new_l_dir = 'sell'
    if not new_open:
        if not forced_close:
            pass
        else:
            forced_close = False  # let stop it here
        if ema_tendency <= 0:  # take charge of issuing_close signal
            issuing_close = True
        else:
            issuing_close = False
        # if issuing_close is true, check the new direction first
        if issuing_close and l_dir == new_l_dir:  # the same direction, just treat it as a greedy
            issuing_close = False
        greedy_action = ''
        greedy_status = ''
        update_quarter_amount = False
        if not issuing_close and (forward_greedy or backward_greedy):
            # emit open again signal
            if l_dir == 'buy':
                if (close - previous_close) > greedy_cost_multiplier * open_cost:
                    greedy_action = 'close'
                    greedy_status = 'maybe closed'
                elif (close - previous_close) < -greedy_cost_multiplier * open_cost:
                    greedy_action = 'open'
                    greedy_status = 'holding'
            elif l_dir == 'sell':
                if (close - previous_close) < -greedy_cost_multiplier * open_cost:
                    greedy_action = 'close'
                    greedy_status = 'maybe closed'
                elif (close - previous_close) > greedy_cost_multiplier * open_cost:
                    greedy_action = 'open'
                    greedy_status = 'holding'
            if greedy_status != '':
                print(trade_timestamp(),
                      'greedy signal %s at %s => %s (%s) ' % (l_dir, previous_close, close, greedy_status))
            if greedy_action != '':  # update amount
                open_greedy = True
                previous_close = close
                update_open_cost(close)
                if globals()['amount_real'] > 0 or globals()['greedy_same_amount']:
                    thisweek_amount = quarter_amount
                elif globals()['greedy_whole_balance']:
                    thisweek_amount = math.ceil(
                        (quarter_amount / (1 / amount_ratio + amount_ratio_plus) - quarter_amount) / greedy_count_max)
                else:
                    thisweek_amount = math.floor((quarter_amount_multiplier - 1) * quarter_amount / greedy_count_max)

                thisweek_amount = int(thisweek_amount)

#  持续更新 pending
#  开始状态，直接买入quarter_amount , greedy_count = max, pending = 0
#  逆向发展，greedy_count >= 1, 增加持仓，greedy_count = greedy_count * (1- 1/max), pending += thisweek_amount ;  == 重复该过程
#  逆向发展，greedy_count < 1, 减少持仓， - (quarter_amount - 1), 更新 pending
#  无动作，更新 balance，quarter_amount
#  同向发展，pending==0, greedy_count += 1/ max ;  == 重复该过程
#  同向发展，pending > 0, 减少持仓pending， 根据减少的比例增加 greedy_count
#  同向发展，pending < 0, greedy_count = max
#  同向发展，pending < 0, greedy_count >= max，则直接增加持仓为 -pending
            if greedy_action == 'close':  # yes, close action pending
                if forward_greedy:
                    if globals()['greedy_same_amount']:
                        (ret, price,
                         l_amount) = issue_quarter_order_now_conditional(symbol, reverse_follow_dir, 0, 'close', False)
                        if ret:
                            globals()['request_price'] = price
                    if thisweek_amount_pending > 0:
                        (ret, price,
                         l_amount) = issue_quarter_order_now_conditional(symbol, l_dir, thisweek_amount_pending,
                                                                         'close', False)  # as much as possible
                        if thisweek_amount_pending >= l_amount:  # is ok
                            thisweek_amount_pending -= l_amount
                        else:
                            print('greedy close request %d, return %d' % (thisweek_amount_pending, l_amount))
                            thisweek_amount_pending = 0
                        if thisweek_amount_pending == 0:  # fresh go
                            greedy_count = greedy_count_max  # increase it to threshold
                        else:
                            greedy_count += (l_amount / thisweek_amount)
                    elif thisweek_amount_pending < 0:  # if less holdings, increase it
                        if greedy_count < greedy_count_max:
                            greedy_count = greedy_count_max
                        else:
                            (ret, price, l_amount) = issue_quarter_order_now(symbol, l_dir, -thisweek_amount_pending,
                                                                             'open')  # as much as possible
                            thisweek_amount_pending += l_amount
                    else:
                        # greedy_count = greedy_count + (1 / greedy_count_max)
                        greedy_count = min(greedy_count + 1, greedy_count_max)

                if backward_greedy:
                    issue_quarter_order_now_conditional(symbol, reverse_follow_dir, 0, 'close', False)
            elif greedy_action == 'open':  # yes, open action pending
                r_rate = globals()['reverse_amount_rate']
                if greedy_count < greedy_count_max:
                    reverse_amount = int(thisweek_amount / r_rate)
                    if reverse_amount == thisweek_amount:
                        reverse_amount += 1
                else:
                    reverse_amount = int(thisweek_amount * r_rate)
                    if reverse_amount == thisweek_amount:
                        thisweek_amount += 1

                if reverse_amount < 1:
                    reverse_amount = 1

                cleanup_holdings_atopen(symbol,
                                        globals()['contract'],
                                        l_dir,
                                        quarter_amount + thisweek_amount_pending, close)

                if greedy_count > 0:  # must bigger than zero
                    # greedy_count = greedy_count * (1.0 - 1.0 / greedy_count_max) # decreasing fast
                    greedy_count -= 1
                    if forward_greedy:  # adjust open sequence according to l_dir
                        if l_dir == 'buy':  # first open sell, then open buy
                            if globals()['greedy_same_amount']:
                                (ret, price, l_amount) = issue_quarter_order_now(symbol, reverse_follow_dir,
                                                                                 reverse_amount, 'open')
                                if ret:
                                    globals()['request_price'] = price
                            issue_quarter_order_now(symbol, l_dir, thisweek_amount, 'open')
                            pass
                        else:
                            (ret, price, l_amount) = issue_quarter_order_now(symbol, l_dir, thisweek_amount, 'open')
                            if ret:
                                globals()['request_price'] = price
                            if globals()['greedy_same_amount']:
                                issue_quarter_order_now(symbol, reverse_follow_dir, reverse_amount, 'open')
                            pass
                        thisweek_amount_pending += thisweek_amount
                    if backward_greedy:
                        issue_quarter_order_now_conditional(symbol, reverse_follow_dir, 0, 'close')
                        # secondly open new order
                        issue_quarter_order_now(symbol, reverse_follow_dir, max(1, thisweek_amount / 2), 'open')
                else:  # less than 1
                    # first take reverse into account and do some makeup
                    (loss, t_amount, leverage) = backend.check_holdings_profit(symbol, contract, reverse_follow_dir)

                    # no enough reverse orders
                    do_makeup = (thisweek_amount_pending + quarter_amount) >= t_amount

                    if do_makeup:
                        # open reverse order
                        if globals()['greedy_same_amount']:
                            (ret, price, l_amount) = issue_quarter_order_now(symbol, reverse_follow_dir, reverse_amount,
                                                                             'open')
            if greedy_action == '' or greedy_count >= greedy_count_max:  # update balance
                update_quarter_amount = True
            if greedy_action != 'open':
                cleanup_holdings_atclose(symbol,
                                         globals()['contract'], l_dir, quarter_amount + thisweek_amount_pending, close)
                # update greedy_count according to amount
                greedy_count = greedy_count_max - (thisweek_amount_pending / quarter_amount)
        if issuing_close:
            globals()['signal_close_order_with_%s' % l_dir](l_index, trade_file, close)
            issue_quarter_order_now_conditional(symbol, l_dir, 0, 'close', False)  # use zero to close all
            # and open again, just like new_open == True
            new_open = True
            if open_greedy:
                close_greedy = backward_greedy  # only if backward_greedy is true
                open_greedy = False
                thisweek_amount_pending = 0
            update_quarter_amount = True
            trade_file = ''  # clear it
        if update_quarter_amount:
            update_last_bond(symbol, globals()['contract'], l_dir)

            old_balance = last_balance
            last_balance = backend.query_balance(symbol, globals()['contract'])
            if last_balance == 0:
                last_balance = old_balance  # in case quary failed
            delta_balance = (last_balance - old_balance) * 100 / old_balance if old_balance != 0 else 0
            amount = quarter_amount
            base_amount = last_balance / last_bond if last_bond > 0 else 1
            if amount_real > 0:  # if set, just use it
                new_quarter_amount = math.ceil(base_amount * amount_real)
            else:
                new_quarter_amount = math.ceil(base_amount / amount_ratio + base_amount * amount_ratio_plus)
            if new_quarter_amount < 1:
                new_quarter_amount = quarter_amount  # means no real update
            do_updating = ''
            if update_quarter_amount_forward and delta_balance > 0 and quarter_amount < new_quarter_amount:  # auto update
                do_updating = 'do '
                quarter_amount = new_quarter_amount
            elif update_quarter_amount_backward and delta_balance < 0 and quarter_amount > new_quarter_amount:  # auto update
                do_updating = 'do '
                quarter_amount = new_quarter_amount
            if do_updating != '':
                print(trade_timestamp(),
                      '%supdate quarter_amount from %s=>%s' % (do_updating, amount, new_quarter_amount),
                      end='')
                if greedy_action == 'close':
                    print(', balance=%f=>%f,%f%%' % (old_balance, last_balance, delta_balance), end='')
                print('')
    if close_greedy:
        print(
            trade_timestamp(), 'greedy signal %s at %s => %s %0.2f (%s%s)' %
            (l_dir, previous_close, close, price_delta, 'forced ' if forced_close else '', 'closed'))
        if forward_greedy:
            if globals()['greedy_same_amount']:
                issue_quarter_order_now_conditional(symbol, reverse_follow_dir, 0, 'close', False)
            issue_quarter_order_now_conditional(symbol, l_dir, thisweek_amount_pending, 'close', False)
        if backward_greedy:
            issue_quarter_order_now_conditional(symbol, reverse_follow_dir, 0, 'close', False)
        thisweek_amount_pending = 0
        close_greedy = False
    if new_open:
        if new_l_dir == '':
            previous_close = close
            return
        else:
            l_dir = new_l_dir
        trade_file = ''
        open_greedy = False
        close_greedy = False
        open_price = 0.0
        greedy_count = greedy_count_max

        if l_dir == '':  # no updating
            previous_close = close
            return

        # do open
        trade_file = generate_trade_filename(os.path.dirname(event_path), l_index, l_dir)
        # print(trade_file)
        globals()['signal_open_order_with_%s' % l_dir](l_index, trade_file, close)
        issue_quarter_order_now(symbol, l_dir, quarter_amount, 'open')

        (open_price,
         no_use) = backend.real_open_price_and_cost(symbol,
                                                    globals()['contract'], l_dir) if not options.emulate else (close,
                                                                                                               0.001)

        update_open_cost(open_price)

        previous_close = close
    return greedy_status


direction = 0
total_revenue = 0
previous_close_price = 0
total_orders = 0
old_total_revenue = 0

amount = 1
old_ema_0 = 0
direction = ''
old_close = 0
average_open_price = 0
old_delta = 0
delta = 0


def with_scandir_tit2tat(l_dir):
    files = list()
    with os.scandir(l_dir) as it:
        for entry in it:
            if entry.name.endswith('.t2t'):
                files.append(entry.name)
    return files


# try to emulate signal notification


def emul_signal_notify(l_dir, l_signal):
    global old_close_mean, signal_notify, trade_notify
    global total_revenue, total_orders
    try:
        files = globals()['with_scandir_%s' % l_signal](l_dir)
        files.sort()
        total_files = len(files)
        to_read = int(random.random() * total_files)
        start_at = int(random.random() * (total_files - to_read))
        print('Total %d files, read latest %d from %d' % (total_files, to_read, start_at))
        for fname in files[start_at:start_at + to_read]:
            fpath = os.path.join(l_dir, fname)
            # print(fpath)
            wait_signal_notify(fpath, l_signal, '')
        files = None
        if total_orders > 0:
            msg = 'Total revenue %.2f average %.2f(%d) with %d data from %d' % (
                total_revenue, total_revenue / total_orders, total_orders, to_read, start_at)
            with open("%s_new_result.txt" % l_dir, 'a') as f:
                f.write('%s\n' % msg)
                f.close()
                print(msg)
        # print(close_mean)
    except Exception as ex:
        print(ex)
        print(traceback.format_exc())


# ['Path', 'is', '/Users/zhangyuehui/workspace/okcoin/websocket/python/ok_sub_futureusd_btc_kline_quarter_1min\n']
# ['Watching', '/Users/zhangyuehui/workspace/okcoin/websocket/python/ok_sub_futureusd_btc_kline_quarter_1min\n']
# ['Change', '54052560', 'in', '/Users/zhangyuehui/workspace/okcoin/websocket/python/ok_sub_futureusd_btc_kline_quarter_1min/1535123280000,', 'flags', '70912Change', '54052563', 'in', '/Users/zhangyuehui/workspace/okcoin/websocket/python/ok_sub_futureusd_btc_kline_quarter_1min/1535123280000.lock,', 'flags', '66304', '-', 'matched', 'directory,', 'notifying\n']

fence_count = 0


def wait_signal_notify(notify, signal, shutdown):
    global fence_count
    global amount
    global trade_file
    shutdown_on_close = False
    while True:
        command = ['fswatch', '-1', notify, shutdown]
        print('', end='', flush=True)
        try:
            if options.emulate:
                globals()['try_to_trade_%s' % signal](notify)
                globals()['save_status_%s' % signal]()
                break
            if not options.one_shot and not options.do_self_trigger:
                result = subprocess.run(command, stdout=PIPE, encoding=default_encoding)  # wait file modified
                # if received shutdown notify, close all order
                if shutdown != '' and shutdown in result.stdout:
                    shutdown_on_close = True
                    print('shutdown triggered, shutdown when closed')
                    with open(shutdown, 'w') as f:
                        f.close()
            if shutdown_on_close and trade_file == '':
                print(trade_timestamp(), 'shutdown now')
                break
            with open(notify, 'r') as f:
                subpath = f.readline().rstrip('\n')
                f.close()
                # print(subpath)
                status = globals()['try_to_trade_%s' % signal](subpath)
                if status != 'no action':
                    globals()['save_status_%s' % signal](subpath)
                    # print(globals()['trade_status'])
            fence_count = 0
            if shutdown_on_close and trade_file == '':
                print(trade_timestamp(), 'shutdown now')
                break
            if options.one_shot or options.do_self_trigger:
                break
        except FileNotFoundError as fnfe:
            print(fnfe)
            break
        except Exception as ex:
            fence_count += 1
            print(ex)
            print(traceback.format_exc())
            if fence_count > 20:  # exceptions 20 continiously
                break
            continue


def read_int_var(filename, var_name):
    l_var = globals()[var_name]
    if os.path.isfile(filename) and os.path.getsize(filename) > 0:
        # check if should read from file
        with open(filename) as f:
            old_var = l_var
            try:
                l_var = float(f.readline())
                if old_var != l_var:
                    print('%s updated to %f' % (var_name, l_var))
                else:
                    print('%s unchanged, unlink %s' % (var_name, filename))
                    os.unlink(filename)
            except Exception as ex:
                l_var = globals()['default_%s' % var_name]
                print('%s reset to default %f' % (var_name, l_var))
                print(ex)
        f.close()
        globals()[var_name] = l_var
        return True
    return False


latest_to_read = int(options.latest_to_read)

l_signal = options.signals[0]
l_prefix = '%s_' % l_signal
l_dir = options.dirs[0]

if not os.path.isdir(l_dir):
    print('%s is not valid direction' % l_dir)
    sys.exit(1)

default_amount_ratio = float(options.amount_ratio)  # means use 1/50 of total amount on one trade, if auto_amount
amount_ratio = default_amount_ratio
ratio_file = '%s.%sratio' % (l_dir, l_prefix)
# print('ratio will read from %s if exist, default is %d' % (ratio_file, amount_ratio), flush=True)

trade_notify = '%s.%strade_notify' % (l_dir, l_prefix)  # file used to notify trade
logfile = '%s.log' % trade_notify
logging.basicConfig(filename=logfile, format='%(asctime)s %(message)s', level=logging.DEBUG)
# logging.info('trade_notify: %s' % trade_notify)
if not options.nolog:
    saved_stdout = sys.stdout
    sys.stdout = open(logfile, 'a')
    sys.stderr = sys.stdout
print(dt.now())
print('trade_notify: %s' % trade_notify)

status_file = '%s.%strade_status' % (l_dir, l_prefix)  # file used to save status
print('status_file: %s' % status_file)
trade_status = dict()

if options.signal_notify is not None:
    signal_notify = options.signal_notify
else:
    signal_notify = '%s.%snotify' % (l_dir, l_prefix)
# logging.info ('signal_notify: %s' % signal_notify)
print('signal_notify: %s' % signal_notify)

pid_file = '%s.%strade_notify.pid' % (l_dir, l_prefix)
# os.setsid() # privilge
# print(os.getpgrp(), os.getpgid(os.getpid()))
with open(pid_file, 'w') as f:
    f.write('%d' % os.getpid())
    f.close()
print('sid %d pgrp %d pid %d saved to file %s' % (os.getsid(os.getpid()), os.getpgrp(), os.getpid(), pid_file))

if options.previous_close is not None:
    previous_close = float(options.previous_close)

if options.startup_notify is not None:
    startup_notify = options.startup_notify
    print('startup_notify: %s' % startup_notify)
if options.shutdown_notify is not None:
    shutdown_notify = options.shutdown_notify
    print('shutdown_notify: %s' % shutdown_notify)

if options.emulate:
    emul_signal_notify(l_dir, l_signal)
    os.sys.exit(0)

if options.restore_status and \
   os.path.isfile(status_file) and \
   os.path.getsize(status_file) > 0:
    globals()['load_status_%s' % l_signal]()
    print('trade status restored:\n', globals()['trade_status'])

periods_mapping_s = {
    '1day': 24 * 60 * 60,
    '12hour': 12 * 60 * 60,
    '6hour': 6 * 60 * 60,
    '4hour': 4 * 60 * 60,
    '2hour': 2 * 60 * 60,
    '1hour': 1 * 60 * 60,
    '30min': 30 * 60,
    '15min': 15 * 60,
    '5min': 5 * 60,
    '3min': 3 * 60,
    '1min': 60
}

# logic copied from signal_notify.py


def prepare_for_self_trigger(notify, signal, l_dir):
    symbol = symbols_mapping[figure_out_symbol_info(notify)]
    contract = figure_out_contract_info(notify)
    period = periods_mapping_s[figure_out_period_info(notify)]
    try:
        reply = eval('%s' % backend.query_kline(symbol, period, contract, '1'))[0]
        price_filename0 = os.path.join(l_dir, '%s' % (reply[0]))
        price_filename = os.path.join(l_dir, '%s.%s' % (reply[0], signal))
        if os.path.isfile(price_filename) and os.path.getsize(price_filename) > 0:
            # print(trade_timestamp(), '%s is already exist' % (price_filename))
            return price_filename
        # print('save price to %s' % price_filename)
        with open(price_filename0, 'w') as f:
            f.write('%s, %s, %s, %s, %s, %s' % (reply[1], reply[2], reply[3], reply[4], reply[5], reply[6]))
            f.close()
        with open(price_filename, 'w') as f:
            f.write('%s, %s, %s, %s, %s, %s' % (reply[1], reply[2], reply[3], reply[4], reply[5], reply[6]))
            f.close()
        with open(notify, 'w') as f:
            f.write(price_filename)
            f.close()
            # print('save signal to %s' % notify)
        return price_filename
    except Exception as Ex:
        print(trade_timestamp(), Ex)
        print(traceback.format_exc())
        return None


def calculate_timeout_for_self_trigger(notify):
    period_s = periods_mapping_s[figure_out_period_info(notify)]
    moduls = int(datetime.datetime.utcnow().strftime('%s')) % period_s
    delta = int(30 * random.random())
    timeout = (period_s - moduls) + delta - 60  # should in current period, for correct high/low
    if timeout > 0:
        return (timeout, 60)
    else:
        return (-1, 60)  # wait at least this long time of seconds


contract = figure_out_contract_info(signal_notify)

first_prompt = True
while True:
    orig_startup_notify = startup_notify
    if startup_notify != '':
        print(trade_timestamp(), 'Waiting for startup signal', flush=True)
        command = ['fswatch', '-1', startup_notify]
        result = subprocess.run(command, stdout=PIPE)  # wait file modified
        if result.returncode < 0:  # means run failed
            os.sys.exit(result.returncode)
        print('%s received startup signal from %s' % (trade_timestamp(), startup_notify))
        limit_direction = ''
        limit_price = 0
        limit_symbol = ''
        limit_amount = 0
        read_int_var(ratio_file, 'amount_ratio')
        with open(startup_notify, 'r') as f:
            # f is a formated map type,just eval it
            line = f.readline()
            print('order_info: %s', line)
            order_info = eval(line)
            f.close()
            dirs = ['', 'buy', 'sell', '', '']  # 1:buy, 2:sell
            if order_info['result']:
                limit_direction = dirs[order_info['orders'][0]['type']]
                limit_price = order_info['orders'][0]['price']
                limit_symbol = order_info['orders'][0]['symbol']
                limit_amount = order_info['orders'][0]['amount']
        with open(startup_notify, 'w') as f:
            # try to clean startup notify
            f.close()
    if first_prompt:
        print(trade_timestamp(), 'Waiting for process new coming file\n', flush=True)
        first_prompt = False
    # issue kickup signal
    with open('%s.ok' % trade_notify, 'w') as f:
        f.close()

    if options.do_self_trigger:
        (timeout, delta) = calculate_timeout_for_self_trigger(signal_notify)

        if timeout > 0:  # wait for triggering
            # print(trade_timestamp(),
            #       'wait for next period about %dh:%dm:%ds later' %
            #       (timeout / 60 / 60,
            #        (timeout % 3600) / 60,
            #        timeout - int(timeout / 60) * 60))
            time.sleep(timeout)
        else:
            # print(trade_timestamp(), 'trigger safely')
            pass
        prepare_for_self_trigger(signal_notify, l_signal, l_dir)

    try:
        wait_signal_notify(signal_notify, l_signal, shutdown_notify)
    except Exception as ex:
        print(ex)

    # reset it in case network error
    backend.which_api = ''

    if options.do_self_trigger:
        time.sleep(delta)

    if options.one_shot:
        break

    if shutdown_notify != '':
        print(trade_timestamp(), 'shutdown signal processed')
    # flush stdout and stderr
    sys.stdout.flush()
    sys.stderr.flush()
    if startup_notify == '' and orig_startup_notify != '':
        break

# >>> datetime.date.today().strftime('%s')
# '1534003200'
