import requests
import pandas as pd
from bs4 import BeautifulSoup

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
}

# 網路爬蟲抓取資料 (抓取【日本大型股票】的基金績效)
resp = requests.get('https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?txtYEAR=2022&txtMONTH=11&txtGROUPID=EUCA000521', headers=headers)

soup = BeautifulSoup(resp.text, 'html.parser')

# 觀察發現透過 id ctl00_ContentPlaceHolder1_TableClassList 可以取出 Morningstar table 資料。取出第一筆
table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]

#bs4的.prettify()格式化(排版美化)資料
#使用pandas讀取資料
fund_DF = pd.read_html(table_content.prettify(),encoding='utf-8')[1]
# 資料前處理，將不必要的列(刪除標題列(分割式表格)多餘的部份)
fund_DF = fund_DF.drop(index=[0])
# 設第一列為標頭(第0列的數字序標題，被換成第1列的中文字標題)
fund_DF.columns = fund_DF.iloc[0]
# 去除不必要列 (標頭(第0列)已產生，原文字標題文字列(第1列)可以刪除了)
fund_DF = fund_DF.drop(index=[1])
# 重新設定index(刪除一些列，要重設 row index)
fund_DF.reset_index(drop=True,inplace=True)
# 把非數值資料 填成0
fund_DF=fund_DF.fillna(value=0)

# 轉換資料型別從 object 轉為 floatW
fund_DF['三個月'] = fund_DF['三個月'].astype(float)
fund_DF['六個月'] = fund_DF['六個月'].astype(float)
fund_DF['一年'] = fund_DF['一年'].astype(float)
fund_DF['二年'] = fund_DF['二年'].astype(float)
fund_DF['三年'] = fund_DF['三年'].astype(float)
fund_DF['五年'] = fund_DF['五年'].astype(float)
fund_DF['自今年以來'] = fund_DF['自今年以來'].astype(float)

# 前二分之一筆資料數量
half_of_row_count = len(fund_DF.index) // 2

# 316 法則篩選標準，ascending True 為由小到大排序，nlargest 為取出前面 x 筆資料，// 代表取整數去掉小數（轉為整數意思）
# pandas新版本的語法
rule_3y_df = fund_DF.sort_values(by='三年', ascending=True).nlargest(half_of_row_count, '三年')
rule_1y_df = fund_DF.sort_values(by='一年', ascending=True).nlargest(half_of_row_count, '一年')
rule_6m_df = fund_DF.sort_values(by='六個月', ascending=True).nlargest(half_of_row_count, '六個月')
# 316法則， 取三者交集（merge 一次只能兩個 DataFrame，先前兩個取交集再和後一個取交集）
rule_31_df = pd.merge(rule_3y_df, rule_1y_df, how='inner')
rule_316_df = pd.merge(rule_31_df, rule_6m_df, how='inner')
rule_316_df = rule_316_df.drop(columns=['加入自選視窗'])

#4433法則
rule4433_thisy_df = fund_DF.sort_values(by='自今年以來', ascending=True).nlargest(len(fund_DF.index)//4, '自今年以來')
rule4433_1y_df = fund_DF.sort_values(by='一年', ascending=True).nlargest(len(fund_DF.index)//4, '一年')
rule4433_2y_df = fund_DF.sort_values(by='二年', ascending=True).nlargest(len(fund_DF.index)//4, '二年')
rule4433_3y_df = fund_DF.sort_values(by='三年', ascending=True).nlargest(len(fund_DF.index)//4, '三年')
rule4433_5y_df = fund_DF.sort_values(by='五年', ascending=True).nlargest(len(fund_DF.index)//4, '五年')
rule4433_6m_df = fund_DF.sort_values(by='六個月', ascending=True).nlargest(len(fund_DF.index)//3, '六個月')
rule4433_3m_df = fund_DF.sort_values(by='三個月', ascending=True).nlargest(len(fund_DF.index)//3, '三個月')
# 4433法則，兩兩取交集
rule4433_a_df = pd.merge(rule4433_thisy_df, rule4433_1y_df, how='inner')
rule4433_b_df = pd.merge(rule4433_a_df, rule4433_2y_df, how='inner')
rule4433_c_df = pd.merge(rule4433_b_df, rule4433_3y_df, how='inner')
rule4433_d_df = pd.merge(rule4433_c_df, rule4433_5y_df, how='inner')
rule4433_e_df = pd.merge(rule4433_d_df, rule4433_6m_df, how='inner')
rule4433_f_df = pd.merge(rule4433_e_df, rule4433_3m_df, how='inner')
rule4433_f_df = rule4433_f_df.drop(columns=['加入自選視窗'])

print('-'*40)
print('====316 法則====\n', rule_316_df)
print('-'*40)
print('====4433 法則====\n', rule4433_f_df)