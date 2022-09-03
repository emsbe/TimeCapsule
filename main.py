import logging
#from config import *
from datetime import time, datetime, date, time, timedelta

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update  # das ist das, was wir brauchen: Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

START, CONFIG, IDLE, WRITING, PROMPT, FREE, EXPORT, STOP = range(8)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their gender."""
    # reply_keyboard = [['Boy', 'Girl', 'Other']]

    update.message.reply_text(
        'Hi! I\'m your personal time capsule. I will hold a conversation with you and by this you will build a journal of your everyday activites.'
        'This is a prototype that stores your data publicly accessible on AWS. Please only share what is ok for you.'
        'Send /cancel to stop talking to me. Tell me when do you want to write your journal? Please use the format HH:MM in UCT. \n\n'
    )

    return CONFIG


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    print("hello")
    job = context.job
    print(job, job.context)
    context.bot.send_message(job.context["chat_id"], text=f'Hey {job.context["data"]}, how was your day? What did you do today? Maybe send one or two images to show me what you did!')


def config(update: Update, context: CallbackContext) -> int:
    """Stores the info about the user and ends the conversation."""
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    time1 = update.message.text.split(":")
    hours = time1[0]
    minutes = time1[1]
    update.message.reply_text(f'Thank you! I will message you at {hours}:{minutes}.')

    # debugging timer setting to 10 seconds after now (Berlin is UTC+2)
    x = datetime.now()
    print(x)
    later = x + timedelta(hours =  -2, seconds = 2)

    chat_id = update.effective_message.chat_id
    #job_removed = remove_job_if_exists(str(chat_id), context)

    # get this to work and we can safe a lot of code
    context.job_queue.run_daily(alarm, later, context={"chat_id":chat_id,"data":user.first_name}, name=str(chat_id))
    text = "Timer successfully set!"

    update.effective_message.reply_text(text)
    #if job_removed:
    #    text += " Old one was removed."
    #await update.effective_message.reply_text(text)

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
    update.message.reply_text(
        'I received your message and will note it down in your journal'
    )

    message = update.message.text

    return IDLE


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONFIG: [MessageHandler(Filters.text & ~Filters.command, config)],
            IDLE: [MessageHandler(Filters.text & ~Filters.command, idle)],
            WRITING: [MessageHandler(Filters.text & ~Filters.command, config)],
            PROMPT: [MessageHandler(Filters.text & ~Filters.command, config)],
            FREE: [MessageHandler(Filters.text & ~Filters.command, config)],
            EXPORT: [MessageHandler(Filters.text & ~Filters.command, config)],
            STOP: [MessageHandler(Filters.text & ~Filters.command, config)],
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
