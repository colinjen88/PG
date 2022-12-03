import requests
import pandas as pd
import matplotlib.pyplot as data_chat

# 下載證交所 個股日成交檔案
catch_url = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data'
recive = requests.get(catch_url)

# 儲存日成交檔案備存
with open('stock_data.csv', 'wb') as my_file:
    my_file.write(recive.content)

# 載入日成交檔案
df = pd.read_csv('stock_data.csv', encoding='utf-8-sig')

# 取出x/y軸資料
data_X = df.loc[0:5, '證券代號']
data_Y = df.loc[0:5, '收盤價']

# 畫出折線圖
data_chat.plot(data_X, data_Y)

# 圖表標示
data_chat.title('Daily Quote-ETF')
data_chat.xlabel('Close Price')
data_chat.ylabel('Stock Name')

# 產出圖表
data_chat.show()
