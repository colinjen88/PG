import requests
from bs4 import BeautifulSoup
import pandas as pd

print('='*20, '查詢股利程式開始', '='*20)
stock_num = input('輸入股票代號：')
data_amount = input('想取得最近幾年的現金股利資料?(請輸入數字)：')

header_info = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
}
# 抓取資料
resp = requests.get(
    f"https://goodinfo.tw/StockInfo/StockDividendPolicy.asp?STOCK_ID={stock_num}", headers=header_info)
resp.encoding = 'utf-8-sig'

#資料轉換成soup物件 (使用thml.parser解析器)
soup_object = BeautifulSoup(resp.text, 'html.parser')

# 使用dict容器存放資料
dividend = {
    'divi_time': [],
    'divi_data': []
}

# 取得歷年股利資料
fixed_n = 1
n = float(data_amount)
while n >= fixed_n:
    # 單筆(年)時間
    catch_time = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(1)')[0].text
    # 單筆(年)現金股利總和
    catch_data = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(4)')[0].text
    # 排除季度資料 (有'∟'整行跳過)
    if '∟' not in catch_time:
        dividend['divi_time'].append(catch_time)
        dividend['divi_data'].append(catch_data)
    else:
        # 找到一筆無用資料，需補取一次資料
        n += 1
    fixed_n += 1  # 取下一筆

print('【現金股利查詢結果】=', dividend)

# 將dict轉成 pandas Dataframe 以存取
d_frame = pd.DataFrame.from_dict(dividend)
# 存成csv
d_frame.to_csv(f"divident_{stock_num}.csv", index=False)
print(f'《 股票代號{stock_num} 》近{data_amount}年的現金股利資料，已保存至『{stock_num}.csv』')
print('-'*23, ' 程式結束 ', '-'*23)
