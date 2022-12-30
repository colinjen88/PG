# 引入套件 flask
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
# 引入 linebot 異常處理
from linebot.exceptions import (
    InvalidSignatureError
)
# 引入 linebot 訊息元件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,ImageMessage
)
# 引用查詢匯率套件
import twder

# Spread Sheets API 套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# import matplotlib.pyplot as plt

app = Flask(__name__)
# 我們使用 Google API 的範圍為 spreadsheets
gsp_scopes = ['https://spreadsheets.google.com/feeds']
# GOOGLE_SHEETS_CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDS_JSON')
# SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')
SPREAD_SHEETS_KEY = '1WEza37iHQhTppvs0YjUEwJ9HR_o6jfdEwF0A9XQ6STU'

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

#《@查詢所有匯率》取得匯率數據 (使用twder套件查詢)
def get_all_currencies_rates_str():
    """取得所有幣別目前匯率字串
    """
    all_currencies_rates_str = ''
    # all_currencies_rates 是一個 dict
    all_currencies_rates = twder.now_all()

    # 取出 key, value : {貨幣代碼: (時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...}
    # (時間, 現金買入, 現金賣出, 即期買入, 即期賣出) 是個 tuple
    for currency_code, currency_rates in all_currencies_rates.items():
        dividing = "-"*35
        all_currencies_rates_str += f'[{currency_code}]\n現金買入:{currency_rates[1]} | 現金賣出:{currency_rates[2]} | 即期買入:{currency_rates[3]} | 即期賣出:{currency_rates[4]}\n({currency_rates[0]})\n{dividing}\n'
    return all_currencies_rates_str

#連接GoogleSheet
# 金鑰檔案路徑
credential_file_path = 'credentials.json'
# auth_gsp_client建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)
    return gspread.authorize(credentials)
gsp_client = auth_gsp_client(credential_file_path, gsp_scopes)
# 透過 open_by_key來開啟工作表worksheet
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).worksheet('transaction')

#紀錄交易到Google Sheet中
def record_currency_transaction(action, currency_name, unit):
    """紀錄交易
    :params action: 買/賣
    :params currency_name: ['CNY', 'THB', 'SEK', 'USD', 'IDR', 'AUD', 'NZD', 'PHP', 'MYR', 'GBP', 'ZAR', 'CHF', 'VND', 'EUR', 'KRW', 'SGD', 'JPY', 'CAD', 'HKD']
    :params unit: 數量
    """
    current_row_length = len(worksheet.get_all_values())
    currency_data = twder.now(currency_name)
    # 取出日期
    transaction_date = currency_data[0].split(' ')[0]
    if action == '買':
        # 即期賣出
        currency_price = currency_data[4]
    elif action == '賣':
        # 即期買入
        currency_price = currency_data[3]
    # 寫入試算表欄位：交易日期, 交易幣別, 買進賣出, 交易單位, 單位成交價格、累計交易金額、目前損益、投資報酬率
    worksheet.insert_row([transaction_date, currency_name, action, unit, currency_price], current_row_length + 1)
    return True

#《查詢損益》計算損益
def get_currency_profit():
    records = worksheet.get_all_values()
    currency_data = {}
    print('計算中...')
    # 遞迴取出每一筆交易做「成本」計算，暫存每一筆「成本」及「數量」
    for index, record in enumerate(records):
        # 若為標頭跳過
        if index == 0:
            continue
        currency_name = record[1]
        action = record[2]
        unit = float(record[3])
        price = float(record[4])
        # 計算單筆交易成本
        cost = unit * price
        # 使用貨幣名稱建立容器_暫存統計資料 (還未存在的才進行進立)
        if currency_name not in currency_data:
            currency_data[currency_name] = {}
            currency_data[currency_name]['total_cost'] = 0
            currency_data[currency_name]['total_unit'] = 0
        # 計算交易總成本 (單一貨幣)
        if action == '買':
            # 買入,總成本增加,總數量增加 (單一貨幣)
            currency_data[currency_name]['total_cost'] += cost
            currency_data[currency_name]['total_unit'] += unit
        elif action == '賣':
            # 賣出,總成本減少,總數量減少 (單一貨幣)
            currency_data[currency_name]['total_cost'] -= cost
            currency_data[currency_name]['total_unit'] -= unit
    #設定容器
    currency_str = ''
    profit = 0
    profit_cul = 0
    amount_cul = 0
    roi_cul = 0
    # 進行損益計算 (利用 twder套件查目前匯率)
    # 遞迴取出(單一貨幣)每一筆交易成本及數量，做(單一貨幣)每一筆的「損益」計算
    for currency_name, currency_data in currency_data.items():
        now_currency_data = twder.now(currency_name)
        # 若 即期買入 有值，則計算損益
        if now_currency_data[3] != '-':
            current_price = float(now_currency_data[3])
            #單一貨幣總損益 = 現在單價 * 擁有數量 - 總成本(單一貨幣)
            profit = current_price * currency_data['total_unit'] - currency_data['total_cost']
            #加總所有損益(所有幣種)
            profit_cul += profit
            #加總所有成本(所有幣種)
            amount_cul += currency_data['total_cost']
            #計算投資報酬率
            roi_cul = (profit_cul/amount_cul)*100
            # 印出損益分析字串
            currency_str += f'[{currency_name}]損益:{profit:.2f}\n'
    currency_str += f'================\n總損益：{profit_cul:.2F}\n================\n總投資報酬率:{roi_cul:.1f}%\n'
    return currency_str

#畫出長條圖(顯示各貨幣庫存),存圖檔至本地
# def drwa_plt():
#     # 定義 x 軸和 y 軸資料
#     x_values = ['貨幣 A', '貨幣 B', '貨幣 C']
#     y_values = [10, 20, 30]
#     # 畫出長條圖
#     plt.bar(x_values, y_values)
#     plt.show()
#     # 儲存圖片至本地端
#     plt.savefig('output.png')

# 此為歡迎畫面處理函式，當網址後面是 / 時由它處理
@app.route("/", methods=['GET'])
def hello():
    return 'hello heroku'

# 此為 Webhook callback endpoint 處理函式，當網址後面是 /callback 時由它處理
@app.route("/callback", methods=['POST'])
def callback():
    # 取得網路請求的標頭 X-Line-Signature 內容，確認請求是從 LINE Server 送來的
    signature = request.headers['X-Line-Signature']
    # 將請求內容取出
    body = request.get_data(as_text=True)
    # handle webhook body（轉送給負責處理的 handler，ex. handle_message）
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# lineBot判斷處理
# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    user_input = event.message.text
    if user_input == '@查詢所有匯率':
        all_currencies_rates_str = get_all_currencies_rates_str()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=all_currencies_rates_str))
    # 輸入格式：買賣/幣別/數量 EX.買/USD/2000
    elif '買/' in user_input or '賣/' in user_input:
        split_user_input = user_input.split('/')
        action = split_user_input[0]
        currency_name = split_user_input[1]
        unit = split_user_input[2]
        record_currency_transaction(action, currency_name, unit)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='紀錄完成'))
    elif user_input == '@查詢損益':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='計算中'))
        # 執行計算損益函數
        currency_profit = get_currency_profit()
        # 怕計算時間太長reply_token過期，改用push_mess
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=currency_profit))
        # # 讀取圖片檔案
        # with open("output.png", "rb") as f:
        #     image_data = f.read()
        # line_bot_api.push_message(
        #     LINE_USER_ID,
        #     ImageSendMessage(original_content_url='https://7b77-111-255-125-246.jp.ngrok.io/output.png',
        #                      preview_image_url='https://7b77-111-255-125-246.jp.ngrok.io/output.png'))

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == '__main__':
    app.run()
