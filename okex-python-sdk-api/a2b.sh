COIN=$1
OLD=$2
NEW=$3

set -ex

SUF=$(date "+%Y-%m-%d")

  mkdir -p ok_sub_futureusd_${COIN}_kline_swap_${NEW}
  mv ok_sub_futureusd_${COIN}_kline_swap_${OLD}.tit2tat_trade_status ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_status
  mv ok_sub_futureusd_${COIN}_kline_swap_${OLD}.tit2tat_trade_notify.pid ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_notify.pid
  mv ok_sub_futureusd_${COIN}_kline_swap_${OLD}.tit2tat_trade_notify.log.$SUF ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_trade_notify.log.$SUF
  mv ok_sub_futureusd_${COIN}_kline_swap_${OLD}.tit2tat_notify.balance ok_sub_futureusd_${COIN}_kline_swap_${NEW}.tit2tat_notify.balance

