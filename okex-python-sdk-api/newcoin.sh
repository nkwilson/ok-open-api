TEMP=$3
COIN=$1
NEW=$2

set -ex

SUF=$(date "+%Y-%m-%d")

  mkdir -p ok_sub_futureusd_${COIN}_kline_swap_${NEW}
  cp ok_sub_futureusd_${TEMP}_kline_swap_${NEW}.tit2tat_trade_status ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_status
  touch ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_notify.pid 
  touch ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_notify.log.${SUF} 
  touch ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_notify.balance

