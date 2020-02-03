import telebot
import logging
from model import StyleTransferModel
from io import BytesIO
from config import token


telebot.apihelper.proxy = {'https': 'socks5h://163.172.152.192:1080', 'http': 'socks5h://163.172.152.192:1080'}

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(token)

style_transfers_dict = {}


class StyleTransfer:
    def __init__(self):
        # self.chat_id = chat_id
        self.num_steps = 80
        self.image_size = 120
        self.content_image_file = None
        self.style_image_file = None
        self.progress_lambda = None
        self.progress_message = None

    def run(self):
        model = StyleTransferModel()
        model.num_steps = self.num_steps
        model.image_size = self.image_size
        model.progress_lambda = lambda progress: self.progress_action(progress)

        content_image = bot.download_file(self.content_image_file.file_path)
        style_image = bot.download_file(self.style_image_file.file_path)

        output = model.transfer_style(content_image, style_image)

        return output

    def progress_action(self, progress):
        self.progress_lambda(progress, self.progress_message)


@bot.message_handler(commands=['new'])
def new_transfer(message):
    transfer = StyleTransfer()
    transfer.progress_lambda = (lambda progress, message: editMessage(message, progress))
    style_transfers_dict[message.chat.id] = transfer

    bot.send_message(message.chat.id, "Waiting for the content image")

def editMessage(message, progress):
    if progress < 1:
        text = "Transfering: " + str(int(progress*100)) + "%"
    else:
        text = "Transfering: Done!"
    if message.text != text:
        message.text = text
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text)
    else:
        print(progress)

@bot.message_handler(commands=['setsize'])
def set_size(message):

    if message.chat.id in style_transfers_dict:
        msg = bot.reply_to(message, "Enter output image size.")
        bot.register_next_step_handler(msg, process_szie)
    else:
        msg = bot.reply_to(message, "Start style transfering with /new")

def process_szie(message):
    try:
        chat_id = message.chat.id
        size = int(message.text)
        if size > 1 and size < 5000:
            style_transfers_dict[chat_id].image_size = size
        else:
            bot.reply_to(message, "Please enter size between 1 and 5000")

    except Exception as e:
        bot.reply_to(message, 'oooops')


@bot.message_handler(content_types=['photo'])
def image_handler(message):
    print(message)
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    image_file = bot.get_file(file_id)
    if chat_id in style_transfers_dict:
        if style_transfers_dict[chat_id].content_image_file:

            style_transfers_dict[chat_id].style_image_file = image_file
            style_transfers_dict[chat_id].progress_message = bot.send_message(chat_id, "Transfering...")
            output = style_transfers_dict[chat_id].run()

            bot.send_message(chat_id, "Done!")
            output_stream = BytesIO()
            output.save(output_stream, format='PNG')
            output_stream.seek(0)
            bot.send_photo(chat_id, photo=output_stream)

        else:
            style_transfers_dict[chat_id].content_image_file = image_file

            bot.send_message(chat_id, "Waiting for the style image")


bot.polling()