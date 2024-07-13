import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)
from dotenv import load_dotenv
from db import create_new_account, update_name, update_address, update_email, update_ssn, update_id
from helpers import encode_image
from openai import query_openai_with_image
import asyncio
import aiohttp

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
    # await update.message.reply_text(
    #     'Hi! I am going to collect some information from you.\n\nWhat is your name?'
    # )
    await update.message.reply_text('Upload your document:')
    # context.user_data['account_id'] = create_new_account()
    # return NAME
    return ID_DOCUMENT

# Define the name handler
async def name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update_name(context.user_data['account_id'], context.user_data['name'])
    await update.message.reply_text('What is your address?')
    return ADDRESS

# Define the address handler
async def address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    update_address(context.user_data['account_id'], context.user_data['address'])

    asyncio.create_task(post_name_and_address(context.user_data))
    
    await update.message.reply_text('What is your email?')
    return EMAIL

async def post_name_and_address(user_data):

    async with aiohttp.ClientSession() as session:
        web_search_result = await web_search(user_data)

        payload = {
            'name': user_data['name'],
            'address': user_data['address'],
            'adverse_media': web_search_result 
        }
        async with session.post('https://your-api-endpoint.com', json=payload) as response:
            # Handle the response if needed
            print(f"POST request status: {response.status}")

async def web_search(user_data):
    async with aiohttp.ClientSession() as session:
        payload = {
            "browse_config": {
                "startUrl": "https://google.com",
                "objective": [
                    f"Find information about {user_data['name']} from {user_data['address']}. If no evidence is found, just say No, if some evidence is found, just say Yes and provide a brief summary."
                ],
                "maxIterations": 10
            },
            "provider_config": {
                "provider": "openai",
                "apiKey": os.getenv('OPENAI_API_KEY')
            },
            "model_config": {
                "model": "gpt-4",
                "temperature": 0
            },
            "response_type": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "required": True,
                        "description": "A brief summary of the findings"
                    }
                }
            },
            "inventory": [
                {
                    "name": "PersonName",
                    "value": user_data['name'],
                    "type": "string"
                },
                {
                    "name": "PersonAddress",
                    "value": user_data['address'],
                    "type": "string"
                }
            ],
            "headless": True,
            "hdr_config": {
                "apikey": os.getenv('HDR_API_KEY'),
                "endpoint": "https://api.hdr.is"
            }
        }
        async with session.post('http://localhost:3000/browse', json=payload) as response:
            if response.status == 200:
                result = await response.json()
                if 'objectiveComplete' in result and 'result' in result['objectiveComplete']:
                    search_result = result['objectiveComplete']['result']
                    if "Yes" in search_result:
                        print("Web search result: Information found")
                        return True
                    elif "No" in search_result:
                        print("Web search result: No information found")
                        return False
                    else:
                        print("Web search result: Unexpected response")
                        return None
                else:
                    print("Web search result: No relevant information found in the response")
                    return None
            else:
                print(f"Web search request failed with status: {response.status}")
                return None

# Define the email handler
async def email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    update_email(context.user_data['account_id'], context.user_data['email'])
    await update.message.reply_text('What is your SSN?')
    return SSN

# Define the SSN handler
async def ssn(update: Update, context: CallbackContext) -> int:
    context.user_data['ssn'] = update.message.text
    update_ssn(context.user_data['account_id'], context.user_data['ssn'])
    await update.message.reply_text('Please send a photo of your ID document.')
    return ID_DOCUMENT

# Define the ID document handler
async def id_document(update: Update, context: CallbackContext) -> int:
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f'{update.message.from_user.id}_id_document.jpg'
        await photo_file.download_to_drive(photo_path)
        encoded_img = encode_image(photo_path)
        response = query_openai_with_image(encoded_img)
        print(response)
        context.user_data['id_document'] = photo_path
        await update.message.reply_text('Photo received and saved.')
    else:
        await update.message.reply_text('Please send a photo of your ID document.')
        return ID_DOCUMENT

    # await update.message.reply_text(
    #     'Thank you! Here is the information you provided:\n'
    #     f"Name: {context.user_data['name']}\n"
    #     f"Address: {context.user_data['address']}\n"
    #     f"Email: {context.user_data['email']}\n"
    #     f"SSN: {context.user_data['ssn']}\n"
    #     'ID Document: Saved as id_document.jpg'
    # )
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
            # NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            # ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            # EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            # SSN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssn)],
            ID_DOCUMENT: [MessageHandler(filters.PHOTO, id_document)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()





# curl -X 'POST' \
#   'http://localhost:3000/browse' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "browse_config": {
#     "startUrl": "https://google.com",
#     "objective": [
#       "did Al Capone commit a crime? If no evidence is found, just say No, if some evidence is found, just say Yes."
#     ],
#     "maxIterations": 10
#   },
#   "provider_config": {
#     "provider": "openai",
#     "apiKey": "sk-None-vS43HkXhRNGVc6rPdgD3T3BlbkFJvZUFLCwDewjjLTovNL7T"
#   },
#   "model_config": {
#     "model": "gpt-4",
#     "temperature": 0
#   },
#   "response_type": {
#     "type": "object",
#     "properties": {
#       "numberOfActiveUsers": {
#         "type": "number",
#         "required": true,
#         "description": "The number of active users"
#       }
#     }
#   },
#   "inventory": [
#     {
#       "name": "Username",
#       "value": "tdaly",
#       "type": "string"
#     }
#   ],
#   "headless": true,
#   "hdr_config": {
#     "apikey": "hdr-1CBgVVt9zkd6RMaPgp3z9NSf9SmgTlGo",
#     "endpoint": "https://api.hdr.is"
#   }
# }'