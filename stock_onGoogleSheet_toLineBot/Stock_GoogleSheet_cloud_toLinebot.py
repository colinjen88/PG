import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler

from linebot import (
    LineBotApi
)

from linebot.models import (
    TextSendMessage,
)
import twstock
# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

# KEY / TOKEN / USERID 存放在環境變數
# 我們使用 Google API 的範圍為 spreadsheets
gsp_scopes = ['https://spreadsheets.google.com/feeds']
SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')
# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 參數設定 #####
stock_num = '2330'  # 要抓取的股票代碼
how_long = 6  # 以最近幾年為計算範圍
crawl_cycle = 1  # (日)抓取股價的週期
# linebot_cycle = 1  # (分)Line訊息傳送週期 (並抓即時股價比較)

# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client


def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)
    return gspread.authorize(credentials)


gsp_client = auth_gsp_client(credential_file_path, gsp_scopes)
# 我們透過 open_by_key 這個方法來開啟工作表一 worksheet
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).sheet1


def crawl_for_stock_price(stock_num):
    header_info = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
    }
    # 《《《 從 台灣證券交易所 抓取資料並整理 》》》
    resp = requests.get(f"https://www.twse.com.tw/exchangeReport/FMNPTK?response=json&stockNo={stock_num}", headers=header_info)
    resp.encoding = 'utf-8-sig'

    # 把json轉給python可以使用
    resp_json = resp.json()
    # 篩選整理用list容器
    yr_high = []
    yr_avg = []
    yr_low = []
    yr_list = []
    # 取得股票名稱
    stock_name = resp_json['title'][5:10].strip()  # 多取字串再清空白
    # 篩選資料
    resp_data = resp_json['data']  # 取得數據本體

    # 《《《 擷取所需欄位資料》》》
    # 要抓的第一筆資料在最後,計算資料總長
    fix_order = len(resp_data)
    for n in range(0, how_long):
        fix_n = fix_order - n - 1  # 從最後面往前抓年份資料
        yr_high.append(float(resp_data[fix_n][4]))  # 數字
        yr_avg.append(float(resp_data[fix_n][8]))  # 數字
        yr_low.append(float(resp_data[fix_n][6]))  # 數字
        yr_list.append(resp_data[fix_n][0])  # 字串

    # 《《《 整理計算，並填入最終dict容器 》》》
    # 使用dict容器(year_value)存放最終資料
    year_value = {
        'year_list': [],
        'high': [],
        'avg': [],
        'low': []
    }
    # 參考資訊 (小數位的值不重要，故使用 round取不精準的四捨五入到第一位)
    year_value['highest'] = round(max(yr_high))  # 統計區間最高價
    year_value['lowest'] = round(min(yr_low))  # 統計區間最低價
    # 標準統計值
    year_value['year_list'] = yr_list  # 參與統計的年份列表
    year_value['high'] = round(sum(yr_high)/len(yr_high))  # 區間高價平均-昂貴價 [↑長線分批賣出]
    year_value['avg'] = round(sum(yr_avg)/len(yr_avg),1)  # 區間平均值-合理價 [↑波段分批賣出]
    year_value['low'] = round(sum(yr_low)/len(yr_low),1)  # 區間低價平均-便宜價 [↓考慮分批買進]

    # 《《《 顯示最終結果 》》》
    print(f"股票名稱：「{stock_name}」")
    print(f"列入統計的年份: {year_value['year_list']} (最近{how_long}年股價)")
    print(">>>參考數據")
    print(f"區間最高價: {year_value['highest']}")
    print(f"區間最低價: {year_value['lowest']}")
    print(">>>標準估價")
    print(f"高價平均值(昂貴價): {year_value['high']}")
    print(f"區間平均價(合理價): {year_value['avg']}")
    print(f"低價平均值(便宜價): {year_value['low']}")
    print('-'*30)
    # 將資料插入第 2 列
    print('寫入資料至Google Sheet...')
    worksheet.insert_row([stock_num, year_value['high'],year_value['avg'], year_value['low']], 2)

# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行

# 每一日抓一次近年股價統計資料
@sched.scheduled_job('interval', days=crawl_cycle)
# @sched.scheduled_job('interval', minutes=crawl_cycle)
def crawl_for_stock_price_job():
    # 要注意不要太頻繁抓取
    print(f'每{crawl_cycle}日執行一次爬蟲程式，並寫入GoogleSheet')
    # 每次清除之前資料
    worksheet.clear()
    # 將標頭插入第 1 列
    print('開始寫入標題...')
    worksheet.insert_row(['股票代號', '昂貴價', '合理價', '便宜價'], 1)
    sotck_no_list = [stock_num]
    # 執行股價爬蟲
    crawl_for_stock_price(sotck_no_list[0])


def judge_value(high_price, middle_price, low_price, realtime_price):
    if realtime_price > high_price:
        message_str = '目前股價太貴'
    elif high_price > realtime_price and realtime_price > middle_price:
        message_str = '股價稍貴'
    elif middle_price > realtime_price and realtime_price > low_price:
        message_str = '稍微便宜'
    elif low_price > realtime_price:
        message_str = '目前股價便宜'
    return message_str


# ===測試用===(縮短時間)
# @sched.scheduled_job('interval', seconds=6)
# 設計一個定時執行程式在週間, 每周一 ~ 五，9點到14點，每小時執行一次 (台股開盤時間)
@sched.scheduled_job('cron', day_of_week='mon-fri', hour='9-14')
def get_notify():
    print(f'台股開般時間，每小時,從Google Sheet讀取資料...')
    # 使用twstock套件,查詢即時報價、時間點、股票名稱
    realprice = twstock.realtime.get(stock_num)['realtime']['latest_trade_price']
    realprice_dot = float(realprice)
    rrr = twstock.realtime.get('2330')
    print(rrr)
    realtime = twstock.realtime.get(stock_num)['info']['time']
    stockname = twstock.realtime.get(stock_num)['info']['name']
    # 讀取google sheet資料
    msg_to_line = ''
    stock_item_lists = worksheet.get_all_values()
    # print(stock_item_lists)
    price_high = stock_item_lists[1][1]
    price_avg = stock_item_lists[1][2]
    price_low = stock_item_lists[1][3]
    msg_num = stock_item_lists[0][0]+stock_item_lists[1][0]
    msg_high = stock_item_lists[0][1] + price_high
    msg_avg = stock_item_lists[0][2] + price_avg
    msg_low = stock_item_lists[0][3] + price_low
    # 判斷目前股價位於什麼價值位階
    show_value = judge_value(float(price_high), float(price_avg), float(price_low), realprice_dot)
    # 整合要傳送到line的資訊
    msg_to_line = f'{msg_num},{stockname} \n 現在股價:【{round(realprice_dot,2)}】\n | {msg_high} | {msg_avg} | {msg_low} \n "即時股價資料時間："{realtime} \n ======= \n 價值判定：《 {show_value} 》'
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=msg_to_line)
    )
    print('LINE通知已發送')


# 開始執行
sched.start()
