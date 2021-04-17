COIN=$1
NEW=$2
CONTRACT=$3
MODEL=$4
MODEL_CONTRACT=${5:-swap}

set -ex

echo 'For example, use fil as model, create new coin: newcoin.sh coin 1min contract fil [contract2]'

SUF=$(date "+%Y-%m-%d")

  mkdir -p ok_sub_futureusd_${COIN}_kline_${CONTRACT}_${NEW}
  cp ok_sub_futureusd_${MODEL}_kline_${MODEL_CONTRACT}_${NEW}.tit2tat_trade_status ok_sub_futureusd_${COIN}_kline_${CONTRACT}_${NEW}.tit2tat_trade_status
  touch ok_sub_futureusd_${COIN}_kline_${CONTRACT}_${NEW}.tit2tat_trade_notify.pid 
  touch ok_sub_futureusd_${COIN}_kline_${CONTRACT}_${NEW}.tit2tat_trade_notify.log.${SUF} 
  touch ok_sub_futureusd_${COIN}_kline_${CONTRACT}_${NEW}.tit2tat_notify.balance

