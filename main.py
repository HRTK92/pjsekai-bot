from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FlexSendMessage,
    QuickReplyButton,
    MessageAction,
    QuickReply,
)
import os, json
import requests
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

app = Flask(__name__)

# ボットの読み込み
line_bot_api = LineBotApi(os.getenv("YOUR_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("YOUR_CHANNEL_SECRET"))


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# メッセージがとどいた時
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if message.startswith("!"):
        args = message[1:].split()
        command = args[0]
        if command == "楽曲":
            response = requests.get(
                "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/musics.json"
            )
            musics = response.json()
            if args[1] == "一覧":
                text = ""
                for music in musics:
                    text += f"{music['title']}\n"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=text)
                )
            else:
                for music in musics:
                    if music["title"] in args[1]:
                        template = Template(
                            """
{
  "type": "bubble",
  "header": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "楽曲情報: {{music.title}}",
        "size": "lg"
      }
    ]
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "baseline",
        "contents": [
          {
            "type": "text",
            "contents": [
              {
                "type": "span",
                "text": "作詞: {{music.lyricist}}"
              },
              {
                "type": "span",
                "text": "作曲: {{music.composer}}"
              },
              {
                "type": "span",
                "text": "編曲: {{music.arranger}}"
              }
            ],
            "wrap": true
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "カテゴリー: {{music.categories}}"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "公開日: {{publishedAt}}"
          }
        ]
      },
      {
        "type": "button",
        "action": {
          "type": "message",
          "label": "譜面を見る",
          "text": "!譜面 {{music.title}}"
        }
      }
    ]
  }
}
                                            """
                        )
                        ren_s = template.render(
                            music=music, publishedAt=music["publishedAt"]
                        )
                        line_bot_api.reply_message(
                            event.reply_token,
                            FlexSendMessage(
                                alt_text=f"楽曲情報: {music['title']}",
                                contents=json.loads(ren_s),
                            ),
                        )

        elif command == "譜面":
            response = requests.get(
                "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/musics.json"
            )
            musics = response.json()
            for music in musics:
                if music["title"] == args[1]:
                    if len(args) == 2:
                        items = [
                            QuickReplyButton(
                                action=MessageAction(
                                    label=f"{action}の譜面",
                                    text=f"!譜面 {music['title']} {action}",
                                )
                            )
                            for action in ["easy", "normal", "hard", "expert", "master"]
                        ]
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text=f"以下から見たい譜面を選んでください", quick_reply=QuickReply(items=items)
                            ),
                        )
                        return
                    music_id = str(music["id"]).zfill(4)
                    difficulty = args[2]
                    svg_url = f"https://minio.dnaroma.eu/sekai-assets/music/charts/{music_id}/{difficulty}.svg"
                    line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=svg_url)
                    )
        elif command == "カード":
            response = requests.get(
                "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/cards.json"
            )
            cards = response.json()
            for card in cards:
                if card == args[1]:
                    pass
            reply_flex = FlexSendMessage(alt_text=f"カード情報: ", contents={})
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=event.message.text)
            )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
