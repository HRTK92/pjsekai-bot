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
import os

app = Flask(__name__)

#ボットの読み込み
line_bot_api = LineBotApi(os.getenv("YOUR_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("YOUR_CHANNEL_SECRET"))

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#メッセージがとどいた時
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if message.startswith('!'):
      pass



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)