import csv
import requests
from bs4 import BeautifulSoup

url = 'https://goodinfo.tw/tw/StockIdxDetail.asp?STOCK_ID=0000'

# 自定偽裝headr
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}

# 定義一個list物件 <大容器>
stock_list = []

# 取得網址原始內容
catch = requests.get(url, headers=headers)

# 指定編碼，避免亂碼
catch.encoding = 'utf-8-sig'

# 把網址內容編碼倒進來 (text 屬性就是 html 檔案)
catch_html = catch.text

#把html轉成BeautifulSoup物件 (使用內建parser解析)
soupOJ = BeautifulSoup(catch_html, "html.parser")

# 使用css選擇器抓取元素 (從第3列抓到第6列)
for index in range(3, 7):
    # 定義一個dict物件,並利用迴圈蒐集需要的元素 <小容器-蒐集元素>
    stock_dict = {}
    # 00取行標題
    stock_dict['Range'] = soupOJ.select(
        f'#CHT_PRICE_YEAR+div table tr:nth-child({index}) > td:nth-child(1)')[0].text
    # 01取漲跌點
    stock_dict['區間漲跌'] = soupOJ.select(
        f'#CHT_PRICE_YEAR+div table tr:nth-child({index}) > td:nth-child(2) > nobr')[0].text
    # 02取漲跌幅度
    stock_dict['區間漲幅'] = soupOJ.select(
        f'#CHT_PRICE_YEAR+div table tr:nth-child({index}) > td:nth-child(3) > nobr')[0].text
    # 03取乖離率
    stock_dict['乖離率'] = soupOJ.select(
        f'#CHT_PRICE_YEAR+div table tr:nth-child({index}) > td:nth-child(6) > nobr')[0].text

    # 把蒐集好的dict 寫入stock_list中
    stock_list.append(stock_dict)

    # 檢閱取得的索引及內容
    print('>>> index', index, '取得的內容是：')
    print(stock_dict)
    print("="*30)

    # 設定csv第一行標題行
    headers = ['Range', '區間漲跌', '區間漲幅', '乖離率']

# 使用with…open寫入csv檔案 <指定utf-8-sig,解決csv中文亂碼>
with open('stockcsv.csv', 'w', encoding='utf-8-sig') as output:
    dict_output = csv.DictWriter(output, headers)
    # 寫入標題
    dict_output.writeheader()
    # 寫入內容
    dict_output.writerows(stock_list)

    # 檢閱最終寫入檔案內容
    print("*"*66)
    print("《 最終寫入檔案的內容是 》：", stock_list)
    print("*"*66)
