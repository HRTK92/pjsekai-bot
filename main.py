import datetime
import json
import os
import re
import time

import requests
from flask import Flask, abort, request
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    FlexSendMessage,
    MessageAction,
    MessageEvent,
    QuickReply,
    QuickReplyButton,
    TextMessage,
    TextSendMessage,
)
from pytz import timezone

app = Flask(__name__)

# ボットの読み込み
line_bot_api = LineBotApi(os.getenv("YOUR_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("YOUR_CHANNEL_SECRET"))


@app.route("/keep", methods=["POST"])
def keep():
    return "OK"


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
      },
      {
        "type": "image",
        "url": "https://minio.dnaroma.eu/sekai-assets/music/jacket/{{music.assetbundleName}}_rip/{{music.assetbundleName}}.png",
        "size": "xl"
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
                            music=music,
                            publishedAt=music["publishedAt"],
                            music_id=str(music["id"]).zfill(3),
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
            musicDifficulties = requests.get(
                "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/musicDifficulties.json"
            ).json()
            if re.fullmatch(r"^!譜面 .+ (easy|normal|hard|expert|master)", message):
                difficulty = re.search(
                    r"(easy|normal|hard|expert|master)", message
                ).groups()[0]
                music_title = re.search(rf"!譜面 (.+) {difficulty}", message).groups()[0]
                for music in musics:
                    if music["title"] == music_title:
                        music_id = str(music["id"]).zfill(4)
                        for musicDifficulty in musicDifficulties:
                            if (
                                musicDifficulty["musicId"] == music["id"]
                                and musicDifficulty["musicDifficulty"] == difficulty
                            ):
                                level = musicDifficulty["playLevel"]
                        svg_url = f"https://minio.dnaroma.eu/sekai-assets/music/charts/{music_id}/{difficulty}.svg"
                        template = Template(
                            """
{
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "image",
            "url": "https://minio.dnaroma.eu/sekai-assets/music/jacket/{{music.assetbundleName}}_rip/{{music.assetbundleName}}.png",
            "align": "start",
            "size": "xs"
          },
          {
            "type": "text",
            "text": "{{music.title}}",
            "align": "start",
            "gravity": "center",
            "size": "lg"
          },
          {
            "type": "text",
            "text": "Level: {{level}}"
          }
        ]
      },
      {
        "type": "button",
        "action": {
          "type": "uri",
          "label": "{{difficulty}}の譜面を見る",
          "uri": "{{svg_url}}"
        }
      }
    ]
  }
}
"""
                        )
                        ren_s = template.render(
                            difficulty=difficulty,
                            svg_url=svg_url,
                            music=music,
                            level=level,
                        )
                        line_bot_api.reply_message(
                            event.reply_token,
                            FlexSendMessage(
                                alt_text=f"{music['title']} {difficulty}の譜面",
                                contents=json.loads(ren_s),
                            ),
                        )
            else:
                music_title = re.search(r"!譜面 (.+)", message).groups()[0]
                for music in musics:
                    if music["title"] in music_title:
                        difficulties = filter(
                            lambda x: x["musicId"] == music["id"], musicDifficulties
                        )
                        levels = []
                        for difficulty in difficulties:
                            levels.append(difficulty["playLevel"])
                        items = [
                            QuickReplyButton(
                                action=MessageAction(
                                    label=f"{action}の譜面 Lv.{level}",
                                    text=f"!譜面 {music['title']} {action}",
                                )
                            )
                            for (action, level) in zip(
                                ["easy", "normal", "hard", "expert", "master"], levels
                            )
                        ]
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text=f"以下から見たい譜面を選んでください",
                                quick_reply=QuickReply(items=items),
                            ),
                        )
        elif command == "イベント":
            response = requests.get(
                "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main/events.json"
            )
            events = response.json()
            last_event = events[-1]
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
        "text": "{{event.name}}",
        "size": "lg",
        "align": "center"
      },
      {
        "type": "image",
        "url": "https://minio.dnaroma.eu/sekai-assets/event/{{event.assetbundleName}}/logo_rip/logo.png",
        "size": "xl"
      }
    ]
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "開始時間: {{utcfromtimestamp(event.startAt / 1000)}}",
            "contents": [],
            "align": "center"
          },
          {
            "type": "text",
            "text": "終了時間: {{utcfromtimestamp(event.closedAt / 1000)}}",
            "align": "center"
          },
          {
            "type": "text",
            "text": "終了まで{{countdown}}",
            "align": "center"
          }
        ]
      }
    ]
  }
}
                                """
            )
            countdown = (
                datetime.datetime.utcfromtimestamp(last_event["closedAt"] / 1000)
                - datetime.datetime.now()
            )
            ren_s = template.render(
                event=last_event,
                utcfromtimestamp=datetime.datetime.utcfromtimestamp,
                countdown=countdown,
            )
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text=f"{last_event['name']}",
                    contents=json.loads(ren_s),
                ),
            )
        elif command == "攻略情報":
            response = requests.get(f"https://appmedia.jp/pjsekai/?s={args[1]}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"https://appmedia.jp/pjsekai/?s={args[1]}",
                ),
            )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
