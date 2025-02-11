import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)
from dotenv import load_dotenv
from db import (
    create_new_account,
    update_name,
    update_address,
    update_email,
    update_ssn,
    update_id,
    upload_file_to_storage,
    update_id_fields,
    update_adverse_media_check
)
from helpers import encode_image
from openai import query_openai_with_image
import asyncio
import aiohttp
import requests
from helpers import validate_ssn
import json

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
NAME, ADDRESS, EMAIL, SSN, ID_DOCUMENT = range(5)


# Define the start command handler
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Hi! I'll be your onboarding buddy for today. Please upload your ID document to start."
    )
    context.user_data["account_id"] = create_new_account()

    return ID_DOCUMENT


# Define the address handler
# async def address(update: Update, context: CallbackContext) -> int:
#     context.user_data['address'] = update.message.text
#     update_address(context.user_data['account_id'], context.user_data['address'])

#     # asyncio.create_task(post_name_and_address(context.user_data))

#     await update.message.reply_text('What is your email?')
#     return EMAIL


async def post_name_and_address(user_data):

    async with aiohttp.ClientSession() as session:
        web_search_result = await web_search(user_data)

        # Call the update_adverse_media_check function
        update_adverse_media_check(user_data['account_id'], web_search_result)



async def web_search(user_data):
    async with aiohttp.ClientSession() as session:
        payload = {
            "browse_config": {
                "startUrl": "https://google.com",
                "objective": [
                    f"Find information about {user_data['name']} who lives around {user_data['address']}. If no evidence is found, just say No, if some evidence is found, just say Yes and provide a brief summary."
                ],
                "maxIterations": 10,
            },
            "provider_config": {
                "provider": "openai",
                "apiKey": os.getenv("OPENAI_API_KEY"),
            },
            "model_config": {"model": "gpt-4", "temperature": 0},
            "response_type": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "required": True,
                        "description": "A brief summary of the findings",
                    }
                },
            },
            "inventory": [
                {"name": "PersonName", "value": user_data["name"], "type": "string"},
                {
                    "name": "PersonAddress",
                    "value": user_data["address"],
                    "type": "string",
                },
            ],
            "headless": True,
            "hdr_config": {
                "apikey": os.getenv("HDR_API_KEY"),
                "endpoint": "https://api.hdr.is",
            },
        }
        async with session.post(
            "http://localhost:3000/browse", json=payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                if (
                    "objectiveComplete" in result
                    and "result" in result["objectiveComplete"]
                ):
                    search_result = result["objectiveComplete"]["result"]
                    if "Yes" in search_result:
                        print("Web search result: Information found")
                        return True
                    elif "No" in search_result:
                        print("Web search result: No information found")
                        return False
                    else:
                        print("Web search result: Unexpected response")
                        return False
                else:
                    print(
                        "Web search result: No relevant information found in the response"
                    )
                    return False
            else:
                print(f"Web search request failed with status: {response.status}")
                return False


# Define the email handler
async def email(update: Update, context: CallbackContext) -> int:
    context.user_data["email"] = update.message.text
    update_email(context.user_data["account_id"], context.user_data["email"])

    api_key = os.getenv("ABSTRACT_API_KEY")
    response = requests.get(
        f"https://emailvalidation.abstractapi.com/v1/?api_key={api_key}&email={context.user_data['email']}"
    )

    if response.status_code != 200:
        await update.message.reply_text(
            "There was an error validating your email. Please try again."
        )
        return EMAIL

    email_data = response.json()

    # Check email validation fields
    if (
        not email_data["is_valid_format"]["value"]
        or not email_data["is_mx_found"]["value"]
        or not email_data["is_smtp_valid"]["value"]
    ):
        await update.message.reply_text(
            "Oops! Looks like this email is invalid. Please provide a valid email address."
        )
        return EMAIL

    if email_data["deliverability"] == "UNDELIVERABLE":
        await update.message.reply_text(
            "We see that the email address is undeliverable. Please provide a valid email address to ensure you can receive our communications!"
        )
        return EMAIL

    if email_data["is_disposable_email"]["value"]:
        await update.message.reply_text(
            "Sorry, disposable email addresses are not allowed. Please provide a valid email address."
        )
        return EMAIL

    # If all checks pass, proceed to the next step
    await update.message.reply_text(
        "Got it. Next, please provide your SSN. We'll encrypt it for security."
    )
    return SSN


# Define the SSN handler
async def ssn(update: Update, context: CallbackContext) -> int:
    context.user_data["ssn"] = update.message.text
    update_ssn(context.user_data["account_id"], context.user_data["ssn"])
    if not validate_ssn(context.user_data["ssn"]):
        await update.message.reply_text("Please provide a valid SSN.")
        return SSN
    await update.message.delete()
    await update.message.reply_text(
        "Thank you! We've hidden it for your privacy. Here is the information you provided:\n"
        # f"Name: {context.user_data['name']}\n"
        # f"Address: {context.user_data['address']}\n"
        f"Email: {context.user_data['email']}\n"
        "ID Document: Saved"
    )
    return ConversationHandler.END


async def process_id_document(photo_path, account_id):
    """
    Processes an ID document by encoding the image and querying the OpenAI API.

    Args:
    - photo_path (str): Path to the photo file.
    - account_id (str): The account ID associated with this document.

    Returns:
    - dict: The JSON response from the OpenAI API.
    """
    encoded_img = encode_image(photo_path)
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please process this image and output the following in JSON:

                        idNumber (string)
                        name (string)
                        birthdate (string)
                        sex (string)
                        address (string)
                        electronicReplicaOfID (boolean)
                        paperReplicaOfID (boolean)
                        pictureIsClear (boolean)
                        idImageIsTampered (boolean)
                        """,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        ) as response:
            result = await response.json()

    # Process the response here
    print(result)

    # Update the user's data with the verification results
    # This is a placeholder - implement according to your needs
    # update_verification_results(account_id, result)

    # Parse the outer JSON

    # Extract the content field
    content_string = result["choices"][0]["message"]["content"]

    # Parse the content field
    card_parsed = json.loads(content_string)

    # Now you can access the parsed content
    print(json.dumps(card_parsed, indent=2))

    # You can also access individual fields, for example:
    print(f"Name: {card_parsed['name']}")
    print(f"Birthdate: {card_parsed['birthdate']}")

    # Call the post_name_and_address function with data from card_parsed
    asyncio.create_task(
        post_name_and_address(
            {"name": card_parsed["name"], "address": card_parsed["address"], "account_id": account_id}
        )
    )

    # Update the ID fields in the database
    update_id_fields(account_id, card_parsed)

    # Update the user's data with the verification results
    # This is a placeholder - implement according to your needs
    # update_verification_results(account_id, result)
    return result


# Define the ID document handler
async def id_document(update: Update, context: CallbackContext) -> int:
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"{update.message.from_user.id}_id_document.jpg"
        await photo_file.download_to_drive(photo_path)
        file_url = upload_file_to_storage(photo_path, os.path.basename(photo_path))
        update_id(context.user_data["account_id"], file_url)

        # Start the ID verification process in the background
        asyncio.create_task(
            process_id_document(photo_path, context.user_data["account_id"])
        )

        await update.message.reply_text(
            "ID document received! Please provide your email."
        )
        return EMAIL
    else:
        await update.message.reply_text("Please send a photo of your ID document.")
        return ID_DOCUMENT


# Define the cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Conversation cancelled.")
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Get the bot's token from the environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables.")
        return

    # Create the Application and pass it your bot's token
    application = Application.builder().token(token).build()

    # Define the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            ID_DOCUMENT: [MessageHandler(filters.PHOTO, id_document)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            SSN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssn)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
