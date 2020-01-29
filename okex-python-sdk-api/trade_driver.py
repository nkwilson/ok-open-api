# -*- coding: utf-8 -*-

from optparse import OptionParser
parser = OptionParser()
parser.add_option("", "--signal_notify", dest="signal_notify",
                  help="specify signal notifier")
parser.add_option("", "--startup_notify", dest="startup_notify",
                  help="specify startup notifier")
parser.add_option("", "--shutdown_notify", dest="shutdown_notify",
                  help="specify shutdown notifier")
parser.add_option('', '--emulate', dest='emulate',
                  action="store_true", default=False,
                  help="try to emulate trade notify")
parser.add_option('', '--skip_gate_check', dest='skip_gate_check',
                  action="store_false", default=True,
                  help="Should skip checking gate when open trade")
parser.add_option('', '--cmp_scale', dest='cmp_scale', default='1',
                  help='Should multple it before do compare')
parser.add_option('', '--policy', dest='policy',
                  help="use specified trade policy, ema_greedy/close_ema/boll_greedy/simple_greedy")
parser.add_option('', '--which_ema', dest='which_ema', default=0, 
                  help='using with one of ema')
parser.add_option('', '--order_num', dest='order_num',
                  help='how much orders')
parser.add_option('', '--fee_amount', dest='fee_amount',
                  help='take amount int account with fee')
parser.add_option('', '--signal', dest='signals', default=['tit2tat'],
                  action='append',
                  help='use wich signal to generate trade notify and also as prefix, boll, simple, tit2tat')
parser.add_option('', '--latest', dest='latest_to_read', default='1000',
                  help='only keep that much old values')
parser.add_option('', '--dir', dest='dirs', default=[],
                  action='append',
                  help='target dir should processing')
parser.add_option('', '--bins', dest='bins', default=0,
                  help='wait how many reverse, 0=once, 1=twice')
parser.add_option('', '--nolog', dest='nolog', 
                  action='store_true', default=False,
                  help='Do not log to file')
parser.add_option('', '--ratio', dest='amount_ratio', default=9,
                  help='default trade ratio of total amount')
parser.add_option('', '--open_start_price', dest='open_start_price',
                  help='init open_start_price')
parser.add_option('', '--previous_close', dest='previous_close',
                  help='init previous_close')
parser.add_option('', '--restore_status', dest='restore_status',
                  action='store_false', default=True,
                  help='restore status from status_file')
parser.add_option('', '--one_shot', dest='one_shot',
                  action='store_true', default=False,
                  help='just run once, save status and quit')
parser.add_option('', '--self_trigger', dest='do_self_trigger',
                  action='store_false', default=True,
                  help='read price by myself and do following trade')
parser.add_option('', '--noaction', dest='noaction',
                  action='store_true', default=False,
                  help='dry run, no real buy/sell action')
parser.add_option('', '--api', dest='api_version',
                  default='v3',
                  help='use specified api version[v1|v3], default is v3')

(options, args) = parser.parse_args()
print (type(options), options, args)

backend=__import__('%s_trade_backend' % options.api_version, globals())

__import__('%s_trade_driver' % options.api_version)

