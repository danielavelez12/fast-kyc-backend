import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)
from dotenv import load_dotenv

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
        'Hi! I am going to collect some information from you.\n\nWhat is your name?'
    )
    return NAME

# Define the name handler
async def name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text('What is your address?')
    return ADDRESS

# Define the address handler
async def address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    await update.message.reply_text('What is your email?')
    return EMAIL

# Define the email handler
async def email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text('What is your SSN?')
    return SSN

# Define the SSN handler
async def ssn(update: Update, context: CallbackContext) -> int:
    context.user_data['ssn'] = update.message.text
    await update.message.reply_text('Please send a photo of your ID document.')
    return ID_DOCUMENT

# Define the ID document handler
async def id_document(update: Update, context: CallbackContext) -> int:
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        context.user_data['id_document'] = 'id_document.jpg'
    else:
        await update.message.reply_text('Please send a photo of your ID document.')
        return ID_DOCUMENT

    await update.message.reply_text(
        'Thank you! Here is the information you provided:\n'
        f"Name: {context.user_data['name']}\n"
        f"Address: {context.user_data['address']}\n"
        f"Email: {context.user_data['email']}\n"
        f"SSN: {context.user_data['ssn']}\n"
        'ID Document: Saved as id_document.jpg'
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
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
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
