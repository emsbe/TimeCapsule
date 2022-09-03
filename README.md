# TimeCapsule
A telegram bot that interacts with you as if it was a daily jorunal of yours. It collects your data and will create a book of your year afterwards based on your messages.


### Setup
install python packages 
telegram
python-telegram-bot
boto3
datetime
pymongo

Then execute the main in main.py to start the bot


### How it works
The timecapsule bot gathers user data and stores images on AWS and the text entries and references to the images on a MongoDB.
First the setup is done, where the users the time when he wants to be notified everyday to write into his journal.
A daily Job is placed on the jobqueue to write a message to the user at the specified time every day. 
Whenever the user answers, a journal entry object is created to note down the photo or image in the journal entry of the given day.
The user can exit by using the /cancel command and starts the bot using the /start command.
The bot has 3 states - start, config and idle.
It spends most of its time in idle, waitng for message input.
