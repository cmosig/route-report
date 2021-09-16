# TODO add message when new country data needs to be downloaded
# TODO use different name instead of result.csv

import logging
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import output

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    InvalidCallbackData,
    PicklePersistence,
    MessageHandler,
    Filters,
)

import route_report

MAX_FILE_SIZE = 52428800

def handle_gpx_file(update, context):
    file = context.bot.getFile(update.message.document.file_id)

    filename = update.message.document.file_name
    filename_path = f"downloaded_files/{filename}"

    if filename.split('.')[-1] != "gpx":
        update.effective_message.reply_text("I do not think this file is a gpx file ;)")
        return

    if update.message.document.file_size > MAX_FILE_SIZE:
        update.effective_message.reply_text("This gpx file is too large. The limit is 50MB.")
        return

    # download file
    file.download(filename_path)

    update.effective_message.reply_text("I received your GPX file! Let me process the route. This usually takes less than a minute.")
    args = {
        'input-file': filename_path,
        'search-distance': 1,
        'country-codes': 'AUTO',
        'redownload-files': False,
        'reprocess-files': False,
        'output-modes': 'csv,print,html-map',
        'points-of-interest': 'food-shop,water,petrol-station'
    }
    route_with_shops, orignal_route = route_report.main(args)
    output.output_results(route_with_shops,
                          orignal_route,
                          modes=args["output-modes"].split(','),
                          original_filename=filename.replace(".gpx", ""),
                          gui=False)

    update.effective_message.reply_text("Done! Sending files to you...")
    result_csv_fname = f"{filename.replace('gpx', 'csv')}"
    result_csv = open(result_csv_fname)
    result_html_fname = f"{filename.replace('gpx', 'html')}"
    result_html = open(result_html_fname)
    update.effective_message.reply_document(result_csv)
    update.effective_message.reply_document(result_html)
    os.remove(result_csv_fname)
    os.remove(result_html_fname)
    os.remove(filename_path)
    

updater = Updater(open("./telegram_api_key").read().replace("\n",""),
                  arbitrary_callback_data=True)
updater.dispatcher.add_handler(
    MessageHandler(Filters.document, handle_gpx_file))
updater.start_polling()
