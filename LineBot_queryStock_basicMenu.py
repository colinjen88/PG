# 載入股票查詢套件
import twstock
import random

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
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage
)
# 第一次要更新股票查詢套件
# twstock.__update_codes()

user_command_dict = {}
app = Flask(__name__)

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN避免外流,改存外部檔案
with open("linebotapi.csv", "r", newline="") as csvfile:
    temp = csvfile.readline().split(',', 2)
    linebotapi = temp[0]
    webhook = temp[1]
line_bot_api = LineBotApi(linebotapi)
handler = WebhookHandler(webhook)


# 此為 Webhook callback endpoint
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
    user_message = event.message.text
    user_id = event.source.user_id
    # 打什麼回什麼
    reply_message = TextSendMessage(text=event.message.text)
    # 根據使用者 ID 暫存指令
    user_command = user_command_dict.get(user_id)

    reply_message = TextSendMessage(text='打錯了啦,請再試試!')
    # 判斷使用者輸入的內容，並做出回應
    match user_message:
        case '@看照片':
            photo_random = str(random.randint(3, 11))
            reply_message = ImageSendMessage(
                original_content_url=f'https://www.fotobeginner.com/wp-content/uploads/2009/04/{photo_random}.jpg',
                preview_image_url=f'https://www.fotobeginner.com/wp-content/uploads/2009/04/{photo_random}.jpg'
            )
        case '@看貼圖':
            sticker_ran = str(random.randint(11088016, 11088039))
            reply_message = StickerSendMessage(
                package_id='6370',
                title="th",
                sticker_id=sticker_ran
            )
        case '@查股價':
            # 判斷使用者輸入為 @查詢股價 且 之前輸入的指令非 @查詢股價
            if user_command != '@查股價':
                reply_message = TextSendMessage(text='輸入查詢的股票：')
                # 儲存使用者輸入了 @查詢股價 指令
                user_command_dict[user_id] = '@查股價'
        case _:
            if user_command == '@查股價':
                # 若使用者上一指令為 @查詢股價 則取出使用者輸入代號的股票價格資訊
                # 使用twstock套件查詢股票資訊
                stock_n = twstock.realtime.get(f'{user_message}')
                if stock_n:
                    reply_message = TextSendMessage(
                        text=f'|股票名稱：{stock_n["info"]["name"]}\n|資料時間：{stock_n["info"]["time"]}\n|即時成交價：{stock_n["realtime"]["latest_trade_price"]}\n|今日累積成交量：{stock_n["realtime"]["accumulate_trade_volume"]}')
                    # 清除指令暫存
                    user_command_dict[user_id] = None
    # 回傳訊息給使用者
    line_bot_api.reply_message(
        event.reply_token,
        reply_message)


# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 運行 Flask server，預設設定監聽 127.0.0.1 port 5000（網路 IP 位置搭配 Port 可以辨識出要把網路請求送到那邊 xxx.xxx.xxx.xxx:port，app.run 參數可以自己設定監聽 ip/port）
    app.run()
