from telegram import Bot

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    def send_message(self, message: str):
        self.bot.send_message(chat_id=self.chat_id, text=message)
