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
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage
)
import random
import csv

app = Flask(__name__)

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN避免外流,改存外部檔案
with open("../linebotapi.csv", "r", newline="") as csvfile:
    temp = csvfile.readline().split(',', 2)
    linebotapi = temp[0]
    webhook = temp[1]
line_bot_api = LineBotApi(linebotapi)
handler = WebhookHandler(webhook)


@ app.route("/callback", methods=['POST'])
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


# decorator 負責判斷 event為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler

@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 判斷使用者輸入的內容，並做出回應
    match user_message:
        case '文字':
            reply_message = TextSendMessage(text=event.message.text)
        case '圖片':
            reply_message = ImageSendMessage(
                original_content_url='https://tenjo.tw/wp-content/uploads/20191105204427_91.jpg',
                preview_image_url='https://tenjo.tw/wp-content/uploads/20191105204427_91.jpg'
            )
        case '帥':
            reply_message = ImageSendMessage(
                original_content_url='https://cc.tvbs.com.tw/img/program/_data/i/upload/2018/07/27/20180727141440-a38d776d-me.jpg',
                preview_image_url='https://cc.tvbs.com.tw/img/program/_data/i/upload/2018/07/27/20180727141440-a38d776d-me.jpg'
            )
        case '美':
            reply_message = ImageSendMessage(
                original_content_url='https://i1.kknews.cc/W6eyomMD7HHsNfrzmCrNEZXiriV_E1uJmrOY9A8/0.jpg',
                preview_image_url='https://i1.kknews.cc/W6eyomMD7HHsNfrzmCrNEZXiriV_E1uJmrOY9A8/0.jpg'
            )
        case '影片':
            reply_message = VideoSendMessage(
                original_content_url='https://www.youtube.com/watch?v=g3MEL5kX66U',
                preview_image_url='https://img.youtube.com/vi/g3MEL5kX66U/sddefault.jpg'
            )
        case '貼圖':
            sticker_ran = str(random.randint(16581242, 16581265))
            reply_message = StickerSendMessage(
                package_id='8515',
                sticker_id=sticker_ran
            )
        case _:
            reply_message = TextSendMessage(text='不知你在說什麼')

 # 根據使用者輸入 event.message.text 條件判斷要回應哪一種訊息
    line_bot_api.reply_message(
        event.reply_token,
        reply_message)


# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 運行 Flask server，預設設定監聽 port 5000（網路 IP 位置搭配 Port 可以辨識出要把網路請求送到那邊 xxx.xxx.xxx.xxx:port）
    app.run()
