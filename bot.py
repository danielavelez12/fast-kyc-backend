import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)
from dotenv import load_dotenv
from db import create_new_account, update_name, update_address, update_email, update_ssn, update_id, upload_file_to_storage
from helpers import encode_image
from openai import query_openai_with_image
import requests

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
NAME, ADDRESS, EMAIL, SSN, ID_DOCUMENT = range(5)

# Define the start command handler
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Hi! I'll be your onboarding buddy for today. What's your email?"
    )
    context.user_data['account_id'] = create_new_account()
    return EMAIL

# Define the address handler
async def address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    update_address(context.user_data['account_id'], context.user_data['address'])
    await update.message.reply_text('What is your email?')
    return EMAIL

# Define the email handler
async def email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    update_email(context.user_data['account_id'], context.user_data['email'])
    api_key = os.getenv('ABSTRACT_API_KEY')
    response = requests.get("https://emailvalidation.abstractapi.com/v1/?api_key={0}&email={1}".format(api_key, context.user_data['email']))
    print(response.status_code)
    print(response.content)
    await update.message.reply_text("Got it. Next, please provide your SSN. We'll encrypt it for security.")
    return SSN

# Define the SSN handler
async def ssn(update: Update, context: CallbackContext) -> int:
    context.user_data['ssn'] = update.message.text
    update_ssn(context.user_data['account_id'], context.user_data['ssn'])
    await update.message.reply_text('Great! Please send a photo of your ID document.')
    return ID_DOCUMENT

# Define the ID document handler
async def id_document(update: Update, context: CallbackContext) -> int:
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f'{update.message.from_user.id}_id_document.jpg'
        await photo_file.download_to_drive(photo_path)
        file_url = upload_file_to_storage(photo_path, os.path.basename(photo_path))
        update_id(context.user_data['account_id'], file_url)
        # encoded_img = encode_image(photo_path)
        # response = query_openai_with_image(encoded_img)
        await update.message.reply_text('Photo received and saved.')
    else:
        await update.message.reply_text('Please send a photo of your ID document.')
        return ID_DOCUMENT

    await update.message.reply_text(
        'Thank you! Here is the information you provided:\n'
        # f"Name: {context.user_data['name']}\n"
        # f"Address: {context.user_data['address']}\n"
        f"Email: {context.user_data['email']}\n"
        f"SSN: {context.user_data['ssn']}\n"
        'ID Document: Saved'
    )
    return ConversationHandler.END

# Define the cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Conversation cancelled.')
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Get the bot's token from the environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('No TELEGRAM_BOT_TOKEN found in environment variables.')
        return

    # Create the Application and pass it your bot's token
    application = Application.builder().token(token).build()

    # Define the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            SSN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssn)],
            ID_DOCUMENT: [MessageHandler(filters.PHOTO, id_document)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
