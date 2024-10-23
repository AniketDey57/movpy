from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

TELEGRAM_BOT_TOKEN = "5707293090:AAHGLlHSx101F8T1DQYdcb9_MkRAjyCbt70"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Function to send the OAuth login URL
async def send_login_link(update: Update, context):
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    
    # Generate the OAuth authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    # Send the login link to the user via Telegram
    await update.message.reply_text(f"Please click the link to authorize the bot: {auth_url}")
    await update.message.reply_text("After you authorize the app, you will see an authorization code. Please send me that code here.")

    # Save the flow in user_data for later use (to fetch the token with the code)
    context.user_data['flow'] = flow

# Function to handle the authorization code
async def handle_auth_code(update: Update, context):
    code = update.message.text

    if 'flow' in context.user_data:
        flow = context.user_data['flow']
        
        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save the credentials to a token file
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        await update.message.reply_text("Authorization successful! You can now upload videos.")
        
    else:
        await update.message.reply_text("Please request a login link first by sending /login.")

# Upload video to YouTube using saved credentials
def upload_to_youtube(video_file, title="Uploaded Video", description="Uploaded by bot", tags=None):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    youtube = build("youtube", "v3", credentials=creds)
    
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
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response

# Main function to run the bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("login", send_login_link))
    application.add_handler(MessageHandler(filters.TEXT, handle_auth_code))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
