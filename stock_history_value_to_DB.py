
import json
import requests
import sqlite3
import pandas as pd
# from bs4 import BeautifulSoup  (接收json,不需bs4解析網頁)

print('='*20, '《 歷年股價法估價 》', '='*20)
# 《《《 使用者輸入查調代號及參數 》》》
stock_num = input('輸入股票代號：')
how_long = int(input('想統計最近多少年的股價?(建議7~10)：'))
safe_ratio = float(input('安全邊際想設幾%?(建議0.85~0.9,愈保守設愈低)：'))

header_info = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
}
# 《《《 從 台灣證券交易所 抓取資料並整理 》》》
resp = requests.get(
    f"https://www.twse.com.tw/exchangeReport/FMNPTK?response=json&stockNo={stock_num}", headers=header_info)
resp.encoding = 'utf-8-sig'
# 資料轉換成soup物件 (使用html.parser解析器) →接收json格式就不需BS幫解析網頁
# soup_object = BeautifulSoup(resp.text, 'html.parser')
# 把json轉給python可以使用
resp_json = resp.json()
# 篩選整理用list容器
stock_name = []
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
    'low': [],
    'safe_high': [],
    'safe_avg': [],
    'safe_low': []
}
# 標準統計值 (小數位的值不重要，故使用 round取不精準的四捨五入到第一位)
year_value['year_list'] = yr_list  # 參與統計的年份列表
year_value['high'] = round(max(yr_high))  # 統計區間最高價-昂貴價 [↑長線分批賣出]
year_value['avg'] = round(sum(yr_avg)/len(yr_avg), 1)  # 統計區間平均值-合理價 [↑波段分批賣出]
year_value['low'] = round(min(yr_low))  # 統計區間最低價-便宜價 [↓考慮分批買進]
# 安全邊際值
year_value['safe_high'] = round(max(yr_high)*safe_ratio, 1)
year_value['safe_avg'] = round((sum(yr_avg)/len(yr_avg))*safe_ratio, 1)
year_value['safe_low'] = round(min(yr_low)*safe_ratio, 1)


# 《《《 顯示最終結果 》》》
print(f'股票名稱：「{stock_name}」')
print(f"列入統計的年份: {year_value['year_list']} (最近{how_long}年股價)")
print(">>>標準估價")
print(f"區間最高價(昂貴價): {year_value['high']}")
print(f"區間平均價(合理價): {year_value['avg']}")
print(f"區間最低價(便宜價): {year_value['low']}")
print(f">>>安全邊際估價(x {(safe_ratio*100)}%)")
print(f"區間最高價(安全昂貴價): {year_value['safe_high']}")
print(f"區間平均價(安全合理價): {year_value['safe_avg']}")
print(f"區間最低價(安全便宜價): {year_value['safe_low']}")

# 《《《 將結果寫進資料庫 》》》
# DB_step1 建立資料庫
connection = sqlite3.connect('year_value.db')
cursor = connection.cursor()
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS stock_value(
        stock_id TEXT PRIMARY KEY NOT NULL,
        stock_name TEXT NOT NULL,
        year_list TEXT NOT NULL,
        high REAL NOT NULL,
        avg REAL NOT NULL,
        low REAL NOT NULL,
        safe_high REAL NOT NULL,
        safe_avg REAL NOT NULL,
        safe_low REAL NOT NULL
    );
   '''
)
connection.commit()

# DB_step2 寫入資料庫 (使用「INSERT OR REPLACE/IGNORE」 ←解決id重覆會報錯的問題)
cursor.execute(
    f'''
    INSERT OR REPLACE INTO stock_value (stock_id, stock_name, year_list,high,avg,low,safe_high,safe_avg,safe_low)
    VALUES ("{stock_num}","{stock_name}", "{year_value['year_list']}", {year_value['high']},{year_value['avg']},{year_value['low']},{year_value['safe_high']},{year_value['safe_avg']},{year_value['safe_low']});
    '''
)
connection.commit()
connection.close()
