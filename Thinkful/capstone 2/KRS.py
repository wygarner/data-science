

import cbpro
import time
import datetime

import pandas as pd
import numpy as np

import urllib3
import certifi
import sqlite3

import sys

public_client = cbpro.PublicClient()

# conn= sqlite3.connect('cb_trades.db')
conn= sqlite3.connect('cb_books.db')

c= conn.cursor()

http= urllib3.PoolManager(cert_reqs= 'CERT_REQUIRED', ca_certs= certifi.where())


def get_oir(bids, asks):
    bid_side = 0
    ask_side = 0

    for x, y in bids.iterrows():
        bid_side += np.exp(-0.5 * x + 1) * y["size"]

    for x, y in asks.iterrows():
        ask_side += np.exp(-0.5 * x + 1) * y["size"]

    order_imbalance_ratio = (bid_side - ask_side) / (bid_side + ask_side)

    return order_imbalance_ratio


def get_voi(bids, asks):
    bid_side = 0
    ask_side = 0

    for x, y in bids.iterrows():
        bid_side +=y["size"]

    for x, y in asks.iterrows():
        ask_side +=y["size"]

    volume_order_imbalance = bid_side - ask_side

    return volume_order_imbalance


# trades_gen = public_client.get_product_trades(product_id='BTC-USD')
# trades = list(trades_gen)

# # print(trades,'\n')

# for trade in trades[:-1]:
#     # print(trade)
#     c.execute("INSERT INTO better_trades VALUES (?,?,?,?)",(trade['time'],trade['trade_id'],
#                                                             trade['size'],trade['side']))
#     conn.commit()

while True:
    
    orderbook = public_client.get_product_order_book('BTC-USD',level=2)
    decimal_time = time.time()
    timestamp = datetime.datetime.now()
    
    # print(orderbook)
    
    
    # sys.exit()
    try:
        bids = pd.DataFrame(orderbook['bids'],columns=['price','size','order_count'])
        bids['price'] = pd.to_numeric(bids['price'])
        bids['size'] = pd.to_numeric(bids['size'])
        bids['size'] = bids['size']*bids['order_count']
        bids['time_ms'] = decimal_time
        bids['timestamp'] = timestamp
        bids= bids.drop(columns=['order_count'])
        
        asks = pd.DataFrame(orderbook['asks'],columns=['price','size','order_count'])
        asks['price'] = pd.to_numeric(asks['price'])
        asks['size'] = pd.to_numeric(asks['size'])
        asks['size'] = asks['size']*asks['order_count']
        asks['time_ms'] = decimal_time
        asks['timestamp'] = timestamp
        asks= asks.drop(columns=['order_count'])
        
        oir = get_oir(bids,asks)
        voi = get_voi(bids,asks)
        spread = asks['price'].min() - bids['price'].max()
        midprice = bids['price'].max() + (spread/2)
        
        # print(bids,'\n')
        # print(asks,'\n')
        
        print(oir,voi,spread,midprice)
        c.execute("INSERT INTO better_books VALUES (?,?,?,?,?,?)",(decimal_time,timestamp,oir,voi,
                                                                    spread,midprice))
        conn.commit()
        
        # new_trades = public_client.get_product_trades(before=trades[0]['trade_id'] , product_id='BTC-USD')
        # new_trades = (list(new_trades))
        
        # print(new_trades[0])
        
        # for trade in new_trades[:-1]:
        #     c.execute("INSERT INTO better_trades VALUES (?,?,?,?)",(trade['time'],trade['trade_id'],
        #                                                         trade['size'],trade['side']))
        #     conn.commit()
        
        time.sleep(1)
    except(KeyError):
        print('...','\n')
    
    # sys.exit()
    
    
    
    
    
    
    

