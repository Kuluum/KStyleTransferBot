import telebot
import logging
from StyleTransfer import StyleTransfer
from io import BytesIO
from config import token

telebot.apihelper.proxy = {'https': 'socks5h://163.172.152.192:1080', 'http': 'socks5h://163.172.152.192:1080'}

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(token, num_threads=5)

style_transfers_dict = {}

# @bot.message_handler(commands=['help'])
# def help(message):
#     bot.send_message(message.chat.id,
#                      "Use /new command for starting new style transferring.\n" +
#                      "Use /setsize command to setup result image size to current transferring.\n" +
#                      "Use /cancel command to cancel current transferring."
#                      )

@bot.message_handler(commands=['new'])
def new_transfer(message):
    transfer = StyleTransfer()
    transfer.progress_lambda = (lambda progress, msg: editTransferMessage(msg, progress))
    style_transfers_dict[message.chat.id] = transfer

    bot.send_message(message.chat.id, "Waiting for the content image")

def editTransferMessage(message, progress):
    if progress < 1:
        text = "Transferring: " + str(int(progress*100)) + "%"
    else:
        text = "Transferring: Done!"
    if message.text != text:
        message.text = text
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text)
    else:
        print(progress)

@bot.message_handler(commands=['setsize'])
def set_size(message):
    if message.chat.id in style_transfers_dict:
        msg = bot.reply_to(message, "Enter output image size between 1 and 2048.")
        bot.register_next_step_handler(msg, process_szie)
    else:
        bot.reply_to(message, "Start style transferring with /new")

def process_szie(message):
    try:
        chat_id = message.chat.id
        size = int(message.text)
        if 1 < size <= 2048:
            style_transfers_dict[chat_id].image_size = size
            bot.reply_to(message, "New size: " + str(size) + "x" + str(size))
        else:
            bot.reply_to(message, "Please enter size between 1 and 2048")
    except Exception as e:
        bot.reply_to(message, 'oooops')

@bot.message_handler(commands=['setiterations'])
def set_iterations(message):
    if message.chat.id in style_transfers_dict:
        msg = bot.reply_to(message, "Enter iterations count between 5 and 500.")
        bot.register_next_step_handler(msg, process_iterations)
    else:
        bot.reply_to(message, "Start style transferring with /new")

def process_iterations(message):
    try:
        chat_id = message.chat.id
        iterations = int(message.text)
        if 5 <= iterations <= 500:
            style_transfers_dict[chat_id].num_steps = iterations
            bot.reply_to(message, "New iterations count: " + str(iterations))
        else:
            bot.reply_to(message, "Please enter size between 5 and 500")
    except Exception as e:
        bot.reply_to(message, 'oooops')

@bot.message_handler(commands=['cancel'])
def cancel_transfer(message):
    if message.chat.id in style_transfers_dict:
        style_transfers_dict[message.chat.id].cancelled = True
        del style_transfers_dict[message.chat.id]
    bot.reply_to(message, 'Ok!')


@bot.message_handler(content_types=['photo'])
def image_handler(message):
    print(message)
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    image_file = bot.get_file(file_id)
    if chat_id in style_transfers_dict:
        if style_transfers_dict[chat_id].content_image:

            style_transfers_dict[chat_id].style_image = bot.download_file(image_file.file_path)
            style_transfers_dict[chat_id].progress_message = bot.send_message(chat_id, "Transferring...")

            try:
                output = style_transfers_dict[chat_id].run()
            except Exception as e:
                bot.send_message(chat_id, "Transferring terminated.")
                return

            bot.send_message(chat_id, "Done!")
            output_stream = BytesIO()
            output.save(output_stream, format='PNG')
            output_stream.seek(0)
            bot.send_photo(chat_id, photo=output_stream)

        else:
            style_transfers_dict[chat_id].content_image = bot.download_file(image_file.file_path)

            bot.send_message(chat_id, "Waiting for the style image")
    else:
        bot.reply_to(message, "Start style transferring with /new")


@bot.message_handler(content_types=['text'])
def text_handler(message):
    chat_id = message.chat.id
    if chat_id not in style_transfers_dict:
        bot.send_message(chat_id, "Start with /new command")
    else:
        if style_transfers_dict[chat_id].content_image:
            bot.send_message(chat_id, "Waiting for the style image")
        else:
            bot.send_message(chat_id, "Waiting for the content image")


bot.polling()
