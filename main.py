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
import requests
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

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
        args = message[1:].split()
        command = args[0]
        if command == "楽曲":
            response = requests.get('https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/musics.json')
            musics = response.json()
            if args[1] == "一覧":
                text = ""
                for musics in musics:
                    text += f"{music['title']}|"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=text
                    )
                )
            else:
                for music in musics:
                    if args[1] == music['title']:
                        template = Template(
                            """"""
                        )
        elif command == "カード":
           response = requests.get('https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/cards.json')
           cards = response.json()
           for card in cards:
               if card == args[1]
           reply_flex = FlexSendMessage(
                   alt_text=f'カード情報: {}',
                   contents={

                   }
           )
           line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text)
            )
          



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)