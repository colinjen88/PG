import os

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
    MessageEvent, TextMessage, TextSendMessage,
)
# 引用查詢匯率套件
import twder

user_command_dict = {}

show_rates_str = ""
app = Flask(__name__)

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_all_currencies_rates_str():
    """取得所有幣別目前匯率字串
    """
    all_currencies_rates_str = ''
    # all_currencies_rates 是一個 dict
    all_currencies_rates = twder.now_all()

    # 取出 key, value : {貨幣代碼: (時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...}
    # (時間, 現金買入, 現金賣出, 即期買入, 即期賣出) 是個 tuple
    for currency_code, currency_rates in all_currencies_rates.items():
        # \ 為多行斷行符號，避免組成字串過長
        all_currencies_rates_str += f'[{currency_code}]:\n 現金買入:[{currency_rates[1]}] 現金賣出:[{currency_rates[2]}] 即期買入:[{currency_rates[3]}] 即期賣出:[{currency_rates[4]}] \n({currency_rates[0]})\n'
    return all_currencies_rates_str


"""取得特定幣別目前匯率"""
def get_currency_rate(currency_name):
    show_rates = twder.now(currency_name)
    show_rates_str = f'查詢時間：{show_rates[0]} \n ↳現金買入：[ {show_rates[1]} ]\n ↳現金賣出：[ {show_rates[2]} ]\n ↳即期買入：[ {show_rates[3]} ]\n ↳即期賣出：[ {show_rates[4]} ]'
    return show_rates_str

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

# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    user_input = event.message.text
    # 取得使用者id
    user_id = event.source.user_id
    # 打什麼回什麼
    reply_message = TextSendMessage(text=event.message.text)
    # 根據使用者ID暫存指令到 user_command 和 user_command_dict
    user_command = user_command_dict.get(user_id)

    # 判斷使用者輸入的內容，並做出回應
    match user_input:
        case '@列出所有匯率':
            take_all_rates = get_all_currencies_rates_str()
            reply_message = TextSendMessage(text=take_all_rates)
        case '@查詢匯率':
            # 之前未輸入過「@查詢匯率」才執行輸入提示文字
            if user_command != '@查詢匯率':
                reply_message = TextSendMessage(text='輸入查詢的幣別：')
                # 儲存該使用者輸入了 @查詢匯率 指令
                user_command_dict[user_id] = '@查詢匯率'
        case _:
            if user_command == '@查詢匯率':
                # 若使用者已經輸入過 @查詢股價 ，則取關鍵字進行匯率查詢
                qeury_rates = str(get_currency_rate(user_input))
                if qeury_rates:
                    reply_message = TextSendMessage(text=qeury_rates)
                    # 清除指令暫存
                    user_command_dict[user_id] = None
    # 回傳訊息給使用者
    line_bot_api.reply_message(
        event.reply_token,
        reply_message)


# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == '__main__':
    app.run()