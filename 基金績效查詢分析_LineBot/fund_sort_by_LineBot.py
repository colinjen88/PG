import requests
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
}
app = Flask(__name__)

# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
handler = WebhookHandler(os.environ.get('YOUR_CHANNEL_SECRET'))
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    # 取得網路請求的標頭
    signature = request.headers['X-Line-Signature']

    # 取得請求的 body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 取得使用者輸入的文字
    message = event.message.text

    # 判斷關鍵字
    if message == "@查詢基金":
        fund_list = queryFund('f_list')
        fund_list_clear = str(fund_list).lstrip("[").rstrip("]").replace("'","")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text= "::::: 三個月績效排名前1/5的基金類別 :::::\n" + fund_list_clear +"\n\n\n"+ "》請輸入要查詢的基金類別名稱："))
    else:
        keyword = message
        # 取得某一基金類別的網址
        result = queryFund(keyword)
        #對該網址進行316分析
        result_316 = fund316(result)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text= "『" + message + " 』類別，316法則篩選結果： \n" + result_316.to_string().replace(" ","")))

#=== 基本爬蟲分析程式
# ===取得基金(晨星)績效列表(&超鏈結)
fund_sort_list = []
dict_info = {}
fund_link = ''
def queryFund(msg):
    #這網址為近三個月報酬率排序(由高至低) txtOrderby為排序參數，txtOrderby為排序參數，2是指以三個月做排序=2是指以三個月做排序
    url = 'https://www.sitca.org.tw/ROC/Industry/IN2421.aspx?txtOrderby=2'
    response = requests.get(url, headers=headers)
    html = response.text

    # 使用 Beautiful Soup 解析 HTML 格式的回應內容
    soup = BeautifulSoup(html, 'html.parser')
    # 找出所有的「基金類別名稱」欄位的元素
    elements = soup.select('#ctl00_ContentPlaceHolder1_TableClassList a')
    # 計算5分之1 的資料數量
    filter_count = len(elements) // 5  #「//」→只取整數
    # 遍歷所有的元素，並提取出文字名稱和超鏈結
    ct = 0
    for element in elements:
        name = element.text
        fund_link = element['href']
        dict_info[name] = fund_link
        # 多存一個名稱列表, 只取前1/5的資料筆數
        if name and ct < filter_count:
            ct+=1
            fund_sort_list.append(str(ct) + ".【" + name + "】 ")
    # 輸出清單/網址
    if msg == 'f_list':
        #回傳基金列表
        return fund_sort_list
    else:
        # 回傳關鍵字對應的網址
        fund_url = dict_info[msg]
        return fund_url

# ===基金做 316篩選
def fund316(res):
    # 基礎網址+各分頁網址(res)
    result_url = 'https://www.sitca.org.tw/ROC/Industry/'+ res
    # 網路爬蟲抓取資料
    resp = requests.get(result_url, headers=headers)
    # 使用BeautifulSoup解析器，解析資料
    soup_316 = BeautifulSoup(resp.text, 'html.parser')

    #分頁資料位於 #ctl00_ContentPlaceHolder1_TableClassList的table之中 ([0]是取出第一筆)
    table_content = soup_316.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]

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

    # 轉換資料型別從 object 轉為 floatW (只轉需用的)
    fund_DF['六個月'] = fund_DF['六個月'].astype(float)
    fund_DF['一年'] = fund_DF['一年'].astype(float)
    fund_DF['三年'] = fund_DF['三年'].astype(float)
    # 計算前 2分之1 筆的資料數量
    half_count = len(fund_DF.index) // 2  #「//」→只取整數
    # 316 法則篩選標準，ascending True 為由小到大排序，nlargest 為取出前面 x 筆資料， (pandas新版本的語法)
    # 3年內的(篩選&排序)結果存入 rule_3
    rule_3 = fund_DF.sort_values(by='三年', ascending=True).nlargest(half_count, '三年')
    # 1年內的(篩選&排序)結果存入 rule_1
    rule_1 = fund_DF.sort_values(by='一年', ascending=True).nlargest(half_count, '一年')
    # 6個月內的(篩選&排序)結果存入 rule_6m
    rule_6m = fund_DF.sort_values(by='六個月', ascending=True).nlargest(half_count, '六個月')

    # 最終結果，取三者交集（ merge一次只能處理兩個,兩兩交集）
    rule_31 = pd.merge(rule_3, rule_1, how='inner')
    rule_316 = pd.merge(rule_31, rule_6m, how='inner')
    # 這次只取「基金名稱」
    rule_316_name = rule_316['基金名稱']
    # 索引編號從1開始
    rule_316_name.index = rule_316_name.index +1
    return rule_316_name
    #  印出最終結果( 316法則 )
    # print('》》》====316 法則====\n', rule_316)


if __name__ == "__main__":
    # 在 Heroku 上運行
    # port = int(os.environ.get("PORT", 5000))
    app.run(port=5000)