import os
import telegram
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from dotenv import load_dotenv
import logging
import subprocess

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение значения переменных из файла .env
TOKEN = os.getenv("TOKEN")
PASSWORD = os.getenv("PASSWORD")

# Устанавливаем уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для конечного автомата
PASSWORD_CHECK, ACTION_CONFIRMED = range(2)

def start(update, context):
    update.message.reply_text(
        "Привет! Чтобы выполнить перезагрузку сервера, введите команду /reset_jupyter"
    )

def reset_jupyter(update, context):
    logger.info("Пользователь %s запросил перезагрузку сервера.", update.message.from_user.username)
    # Запрос пароля у пользователя
    update.message.reply_text("Введите пароль для выполнения действия:")
    return PASSWORD_CHECK

def check_password(update, context):
    # Получаем введенный пользователем пароль
    user_password = update.message.text

    # Проверяем пароль
    if user_password != PASSWORD:
        logger.warning("Пользователь %s ввел неверный пароль.", update.message.from_user.username)
        update.message.reply_text("Неверный пароль. Действие отменено.")
        return ConversationHandler.END
    else:
        logger.info("Пользователь %s ввел верный пароль. Выполняется перезагрузка сервера...", update.message.from_user.username)
        update.message.reply_text("Пароль верный. Выполняется перезагрузка сервера...")
        # Выполняем команду gcloud compute instances reset prod-jupyter
        try:
            subprocess.run(["gcloud", "compute", "instances", "reset", "prod-jupyter"], check=True)
            logger.info("Перезагрузка сервера выполнена.")
            update.message.reply_text("Сервер успешно перезагружен.")
        except subprocess.CalledProcessError as e:
            logger.error("Ошибка при выполнении команды: %s", str(e))
            update.message.reply_text("Ошибка при выполнении команды. Пожалуйста, проверьте настройки.")
        return ConversationHandler.END

def cancel(update, context):
    logger.warning("Пользователь %s отменил действие.", update.message.from_user.username)
    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

def help_command(update, context):
    help_text = (
        "Список команд:\n"
        "/start - Начать\n"
        "/reset_jupyter - Выполнить перезагрузку сервера"
    )
    update.message.reply_text(help_text)

def show_commands(update, context):
    if update.message.text.startswith('/'):
        help_command(update, context)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчик команды /start
    dp.add_handler(CommandHandler("start", start))

    # Добавляем обработчик команды /help
    dp.add_handler(CommandHandler("help", help_command))

    # Создаем ConversationHandler для команды /reset_jupyter
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reset_jupyter", reset_jupyter)],
        states={
            PASSWORD_CHECK: [MessageHandler(Filters.text, check_password)],
            ACTION_CONFIRMED: [MessageHandler(Filters.text, action_confirmed)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Добавляем ConversationHandler в диспетчер
    dp.add_handler(conv_handler)

    # Добавляем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text, show_commands))

    # Запускаем бота
    updater.start_polling()

    # Оставляем бота активным до принудительной остановки
    updater.idle()

if __name__ == '__main__':
    main()

