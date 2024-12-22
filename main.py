from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from dotenv import load_dotenv
import openai
import os

app = FastAPI()

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()

    if user_message in ["ส่งรูป", "send picture"]:
        send_image(event)
    elif user_message in ["สรุปผล", "summarize"]:
        summarize_results(event)
    else:
        handle_chatgpt(event, user_message)

def send_image(event):
    image_url = "https://example.com/path-to-your-image.jpg"
    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    )

def summarize_results(event):
    summary = "ผลการวิเคราะห์: รายงานสรุปของคุณเสร็จสมบูรณ์แล้ว"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=summary)
    )

def handle_chatgpt(event, user_message):
    chatgpt_response = get_chatgpt_response(user_message)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=chatgpt_response)
    )

def get_chatgpt_response(user_message: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            max_tokens=150,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Sorry, I couldn't process your request: {e}"