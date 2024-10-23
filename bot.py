import os
import moviepy.editor as mp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Replace with your API token from BotFather
TELEGRAM_BOT_TOKEN = "5707293090:AAHGLlHSx101F8T1DQYdcb9_MkRAjyCbt70"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# YouTube authentication
def youtube_authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# Combine audio and image into a video
def combine_audio_image(image_path, audio_path, output_path):
    image_clip = mp.ImageClip(image_path)
    audio_clip = mp.AudioFileClip(audio_path)
    video = image_clip.set_duration(audio_clip.duration).set_audio(audio_clip)
    video.write_videofile(output_path, fps=24)

# YouTube video upload
def upload_to_youtube(video_file, title="Uploaded Video", description="Uploaded by bot", tags=None):
    youtube = youtube_authenticate()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # Category: People & Blogs
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    return response

# Handlers for the Telegram bot
async def start(update: Update, context):
    await update.message.reply_text("Send me an image and an audio file, and I'll combine them into a video and upload it to YouTube!")

# Storing the files
user_data = {}

async def handle_photo(update: Update, context):
    file = await update.message.photo[-1].get_file()
    file_path = f"{update.message.from_user.id}_image.jpg"
    await file.download(file_path)
    user_data['image'] = file_path
    await update.message.reply_text("Image received! Now send me an audio file.")

async def handle_audio(update: Update, context):
    file = await update.message.audio.get_file()
    file_path = f"{update.message.from_user.id}_audio.mp3"
    await file.download(file_path)
    user_data['audio'] = file_path
    await update.message.reply_text("Audio received! Now combining...")

    # Check if both files are received
    if 'image' in user_data and 'audio' in user_data:
        video_path = f"{update.message.from_user.id}_video.mp4"
        combine_audio_image(user_data['image'], user_data['audio'], video_path)
        
        await update.message.reply_text("Uploading video to YouTube...")
        response = upload_to_youtube(video_path, title="Bot Video", description="Generated by Telegram bot")

        await update.message.reply_text(f"Video uploaded! You can view it here: https://www.youtube.com/watch?v={response['id']}")

        # Clean up files
        os.remove(user_data['image'])
        os.remove(user_data['audio'])
        os.remove(video_path)

# Main function to run the bot
async def main():
    # Create Application instead of Updater
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))

    # Start the bot
    await application.start_polling()
    await application.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
