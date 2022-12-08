
import requests
from bs4 import BeautifulSoup
import pandas as pd

print('='*20, '查詢股利程式開始', '='*20)
stock_num = input('輸入股票代號：')
data_amount = input('想取得最近幾年的財報資料?(請輸入數字)：')

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
financial = {
    'finan_time': [],
    'finan_yield': [],
    'finan_eps': [],
    'finan_avg_price': [],
    'finan_pe': []
}

# 取得歷年股利資料
fixed_n = 1
n = float(data_amount)
while n >= fixed_n:
    # 年度(單筆)
    catch_time = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(1)')[0].text
    # 殖利率(單筆)
    catch_yield = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(19)')[0].text
    # EPS(單筆)
    catch_eps = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(21)')[0].text
    # 年度平均股價
    catch_avg_price = soup_object.select(
        f'#divDetail>table tr:nth-child({fixed_n+4}):not([class*="bg_h2"])>td:nth-child(16)')[0].text

    # 排除季度資料 (有'∟'為季度,整筆略過)
    if '∟' not in catch_time:
        # 有取得數值才計算
        if '-' not in catch_avg_price and '-' not in catch_eps:
            # 本益比 = 股價/EPS
            cal_pe = int(float(catch_avg_price) / float(catch_eps))
        else:
            cal_pe = '未公佈'

        financial['finan_time'].append(catch_time)
        financial['finan_yield'].append(catch_yield)
        financial['finan_eps'].append(catch_eps)
        financial['finan_avg_price'].append(catch_avg_price)
        financial['finan_pe'].append(cal_pe)
    else:
        # 找到一筆無用資料，需補取一次資料
        n += 1
    fixed_n += 1  # 取下一筆

# 展示資料取得結果
print(f"所取得的資料年份為: {financial['finan_time']}")
print(f"【近{data_amount}年 殖利率】={financial['finan_yield']}")
print(f"【近{data_amount}年 EPS】={financial['finan_eps']}")
print(f"【近{data_amount}年 平均股價】={financial['finan_avg_price']}")
print(f"【近{data_amount}年 本益比】={financial['finan_pe']}")
print("^^^以上為查詢結果^^^")

# 將dict轉成 pandas Dataframe 以存取
d_frame = pd.DataFrame.from_dict(financial)
# 存成csv
d_frame.to_csv(f"financial_{stock_num}.csv", index=False)
print(f"《 股票代號{stock_num} 》近{data_amount}年的財報資料，已保存至『financial_{stock_num}.csv』")
print('-'*23, ' 程式結束 ', '-'*23)
