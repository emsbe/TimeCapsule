""" General TODOS"""
# Deploy bot
# Add Export Trigger -> should be a HTTP request to our server that generates the pdf


import logging
import boto3
import pymongo
from pymongo import MongoClient, InsertOne

from datetime import datetime, date, time, timedelta

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update  # das ist das, was wir brauchen: Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

START, CONFIG, IDLE = range(3)

# s3 Setup - overview https://s3.console.aws.amazon.com/s3/buckets/timecapsule-spehsa?region=eu-central-1&tab=objects
# TODO Refactor Access Data to external file
s3region = "eu-central-1"
s3 = boto3.client('s3', s3region,
                  aws_access_key_id=s3AcessKey,
                  aws_secret_access_key=s3secretKey)

# MongoDB Setup - overview https://cloud.mongodb.com/v2/6313883d4daf6d3c135563fc#clusters/detail/Main
# TODO Refactor Access Data to external file
client = pymongo.MongoClient(f'mongodb+srv://{mongoAccess}@main.kgnrhwx.mongodb.net/?retryWrites=true&w=majority')
db = client.TimeCapsule
collection = db.Entries


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their gender."""

    # TODO Add User Name here to make it more personal
    update.message.reply_text(
        'Hi! I\'m your personal time capsule. I will hold a conversation with you and by this you will build a journal of your everyday activites.'
        'This is a prototype that stores your data publicly accessible on AWS. Please only share what is ok for you.'
        'Send /cancel to stop talking to me. Tell me when do you want to write your journal? Please use the format HH:MM in UCT. \n\n'
    )

    return CONFIG


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context["chat_id"],
                             text=f'Hey {job.context["data"]}, how was your day? What did you do today? Maybe send one or two images to show me what you did!')


def config(update: Update, context: CallbackContext) -> int:
    """Stores the info about the user and ends the conversation."""
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    # TODO Handle that user can be in different time zone as bot deployment, hence always focusing on users send times to specify in which entry to write
    # TODO Error Handling to only accept real HH:MM Values - f.e. no 71:94
    time1 = update.message.text.split(":")
    hours = time1[0]
    minutes = time1[1]
    update.message.reply_text(f'Thank you! I will message you at {hours}:{minutes}.')

    # debugging timer setting to 10 seconds after now (Berlin is UTC+2), finally use hours and minutes to create timestamp instead of "later"
    currentTime = datetime.now()
    later = currentTime + timedelta(hours=-2, seconds=2)

    chat_id = update.effective_message.chat_id

    context.job_queue.run_daily(alarm, later, context={"chat_id": chat_id, "data": user.first_name}, name=str(chat_id))
    text = "Reminder successfully set!"

    update.effective_message.reply_text(text)

    return IDLE


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def idle(update: Update, context: CallbackContext) -> int:
    """Sends a message"""
    user = update.message.from_user
    logger.info("User %s wrote an entry.", user.first_name)

    # This should idealy also be the users local time instead of the time of the deployed bot
    currentTime = datetime.now()

    # handle photo
    # TODO Refactor json structure to only create one journal entry with an id that has other journal entry objects referencing this entry with the id.
    # Images should then only be stored as link and with a reference to the journal entry. Same is for text. This also includes overhead to check if journal entry
    # for this day already exists. Might be something to think a bit longer about
    if (update.message.photo):
        # TODO how to handle multiple images sent at once?
        photo_file = update.message.photo[-1].get_file()
        photo_file.download('images/user_photo.jpg')
        logger.info("Photo of %s: %s", user.first_name, 'images/user_photo.jpg')
        update.message.reply_text(
            'I\'ve received your photo and added it to your journal entry for today.'
        )
        filename = f'{user.id}_{currentTime.year}{currentTime.month}{currentTime.day}_{currentTime.hour}{currentTime.minute}{currentTime.second}.jpg'
        bucketname = 'timecapsule-spehsa'
        # TODO figure out how to make the image on s3 accessible for our future react app to create the book.
        # Currently one has to manually edit the permissions to the image to access it via the link. This has to go by somehow adding the credentials on one
        # side or making them all publicly accessibly (lesss favoured option)
        s3.upload_file('images/user_photo.jpg', bucketname, filename)
        url = f"https://{bucketname}.s3.{s3region}.amazonaws.com/{filename}"

        imageEntry = [{"type": "image", "link": url, "high_importance": "false"}]
        result = {"user": user.id, "date": f'{currentTime.year}-{currentTime.month}-{currentTime.day}', "message": "",
                  "resources": imageEntry}
        collection.insert_one(result)

    # handle text input
    if (update.message.text):
        # TODO check if emojis can be stored in JSON
        result = {"user": user.id, "date": f'{currentTime.year}-{currentTime.month}-{currentTime.day}',
                  "message": update.message.text,
                  "resources": []}
        collection.insert_one(result)

        update.message.reply_text(
            'I received your message and will note it down in your journal'
        )

    return IDLE


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    # TODO Refactor Token into external file
    updater = Updater(botToken)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONFIG: [MessageHandler(Filters.text & ~Filters.command, config)],
            # TODO Check which other filters are feasible
            # TODO Check why Image upload in full size are not recognized, might be document filter then
            IDLE: [MessageHandler(Filters.text & ~Filters.command | Filters.photo, idle)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
