import logging

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import re

import paramiko
import os

from dotenv import load_dotenv, find_dotenv

import psycopg2
from psycopg2 import Error

from uuid import uuid4

from pathlib import Path
#found_dotenv = find_dotenv()
#load_dotenv(found_dotenv)

TOKEN = os.getenv('TOKEN')
# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'find_email'


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'


def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета, для вывода всех пакетов напишите "-":')

    return 'get_apt_list'


def find_email(update: Update, context):
    key = update.message.chat.username
    user_input = update.message.text  # Получаем текст

    emailRegex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+.[a-zA-Z0-9_-]+')

    emailList = emailRegex.findall(user_input)

    if not emailList:
        update.message.reply_text('Электронные почты не найдены')
        return

    emails = ''
    for i in range(len(emailList)):
        emails += f'{i + 1}. {emailList[i]}\n'

    context.user_data[key] = emails

    emails += 'Желаете записать данные в базу данных? Введите "Да" или "Нет":'
    update.message.reply_text(emails)
    return 'add_to_db_email'


def add_to_db_email(update: Update, context):
    if update.message.text.lower() != 'да' and update.message.text.lower() != 'нет':
        update.message.reply_text('Введите "Да" или "Нет":')
    if update.message.text.lower() == 'да':
        key = update.message.chat.username
        value = context.user_data.get(key, 'Not found')
        data = connectDB('add_email', value)
        update.message.reply_text(data)
        return ConversationHandler.END
    elif update.message.text.lower() == 'нет':
        return ConversationHandler.END


def find_phone_number(update: Update, context):
    key = update.message.chat.username
    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'((8|\+7)[\-\s]?\(?\d{3}\)?[\-\s]?\d{3}[\-\s]?\d{2}[\-\s]?\d{2})')  # формат 8 (000) 000-00-00

    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов

    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return  # Завершаем выполнение функции

    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {phoneNumberList[i][0]}\n'  # Записываем очередной номер

    context.user_data[key] = phoneNumbers

    phoneNumbers += 'Желаете записать данные в базу данных? Введите "Да" или "Нет":'

    update.message.reply_text(phoneNumbers)  # Отправляем сообщение пользователю
    return 'add_to_db_phone'


def add_to_db_phone(update: Update, context):
    if update.message.text.lower() != 'да' and update.message.text.lower() != 'нет':
        update.message.reply_text('Введите "Да" или "Нет":')
    if update.message.text.lower() == 'да':
        key = update.message.chat.username
        value = context.user_data.get(key, 'Not found')
        data = connectDB('add_phone', value)
        update.message.reply_text(data)
        return ConversationHandler.END
    elif update.message.text.lower() == 'нет':
        return ConversationHandler.END


def verify_password(update: Update, context):
    user_input = update.message.text
    passwordRegex = re.compile(r'^(?=.*\d)(?=.*[!@#$%^&*()])(?=.*[a-z])(?=.*[A-Z])[\da-zA-Z!@#$%^&*()]{8,}$')

    password = passwordRegex.search(user_input)

    if not password:
        update.message.reply_text("Пароль простой")
    else:
        update.message.reply_text('Пароль сложный')
    return ConversationHandler.END


def connectHost(command, package=None):
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    logging.debug(f'HOST: {host}')
    logging.debug(f'PORT: {port}')
    logging.debug(f'USERNAME: {username}')
    logging.debug(f'PASSWORD: {password}')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdout, stderr = '', ''
    if command == 'get_release':
        stdin, stdout, stderr = client.exec_command('cat /etc/os-release')
    elif command == 'get_uname':
        stdin, stdout, stderr = client.exec_command('uname -a')
    elif command == 'get_uptime':
        stdin, stdout, stderr = client.exec_command('uptime')
    elif command == 'get_df':
        stdin, stdout, stderr = client.exec_command('df -h')
    elif command == 'get_free':
        stdin, stdout, stderr = client.exec_command('free -h')
    elif command == 'get_mpstat':
        stdin, stdout, stderr = client.exec_command('mpstat -P ALL')
    elif command == 'get_w':
        stdin, stdout, stderr = client.exec_command('w')
    elif command == 'get_auth':
        stdin, stdout, stderr = client.exec_command('tail /var/log/auth.log')
    elif command == 'get_critical':
        stdin, stdout, stderr = client.exec_command('tail -n 5 /var/log/syslog | grep "crit"')
    elif command == 'get_ps':
        stdin, stdout, stderr = client.exec_command('ps | head -20')
    elif command == 'get_ss':
        stdin, stdout, stderr = client.exec_command('ss -s')
    elif command == 'get_apt_list_none':
        stdin, stdout, stderr = client.exec_command('apt list --installed | head')
    elif command == 'get_apt_list':
        stdin, stdout, stderr = client.exec_command(f'apt show {package}')
    elif command == 'get_services':
        stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service --state=running')
    elif command == 'get_repl_logs':
        stdin, stdout, stderr = client.exec_command('cat /var/log/postgresql/postgresql-14-main.log | grep repl_user | tail')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    logging.debug(f'DATA: {data}')
    return data


def connectDB(command, data=None):
    load_dotenv()
    connection = None
    try:
        user=os.getenv('DB_USER')
        password=os.getenv('DB_PASSWORD')
        host=os.getenv('DB_HOST')
        port=os.getenv('DB_PORT')
        database=os.getenv('DB_DATABASE')
        logging.debug(f'USER: {user}')
        logging.debug(f'PASSWORD: {password}')
        logging.debug(f'HOST: {host}')
        logging.debug(f'PORT: {port}')
        logging.debug(f'DATABASE: {database}')
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                      password=os.getenv('DB_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'),
                                      database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        if command == 'get_emails':
            cursor.execute("SELECT email FROM emails;")
            data_tmp = cursor.fetchall()
            data = ''
            i = 1
            for row in data_tmp:
                data += f'{i}. {"".join((row))}\n'
                i += 1
        elif command == 'get_phones':
            cursor.execute("SELECT phone FROM phones;")
            data_tmp = cursor.fetchall()
            data = ''
            i = 1
            for row in data_tmp:
                data += f'{i}. {"".join((row))}\n'
                i += 1
        elif command == 'add_email':
            try:
                for email in data.split('\n')[:-1]:
                    email = email.split()[1]
                    logging.debug(f'Email: {email}')
                    cursor.execute(f"INSERT INTO emails (email) VALUES ('{email}');")
                connection.commit()
                data = "Данные успешно записаны"
                logging.info("Команда успешно выполнена")
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                data = "Произошла ошибке при загрузке данных"
        elif command == 'add_phone':
            try:
                for phone in data.split('\n')[:-1]:
                    phone = phone[phone.index(' ') + 1:]
                    logging.debug(f'Phone: {phone}')
                    cursor.execute(f"INSERT INTO phones (phone) VALUES ('{phone}');")
                connection.commit()
                data = "Данные успешно записаны"
                logging.info("Команда успешно выполнена")
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                data = "Произошла ошибке при загрузке данных"
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
        else:
            return "Произошла ошибка при подключении к базе данных"
    return data


def get_release(update: Update, context):
    data = connectHost('get_release')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_uname(update: Update, context):
    data = connectHost('get_uname')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_uptime(update: Update, context):
    data = connectHost('get_uptime')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_df(update: Update, context):
    data = connectHost('get_df')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_free(update: Update, context):
    data = connectHost('get_free')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_mpstat(update: Update, context):
    data = connectHost('get_mpstat')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_w(update: Update, context):
    data = connectHost('get_w')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_auth(update: Update, context):
    data = connectHost('get_auth')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_critical(update: Update, context):
    data = connectHost('get_critical')
    if data:
        update.message.reply_text(data)
    else:
        update.message.reply_text("Критических событий не обнаружено")
    return ConversationHandler.END


def get_ps(update: Update, context):
    data = connectHost('get_ps')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_ss(update: Update, context):
    data = connectHost('get_ss')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_apt_list(update: Update, context):
    user_input = update.message.text.lower()
    if user_input == '-':
        data = connectHost('get_apt_list_none')
    else:
        data = connectHost('get_apt_list', user_input)
    update.message.reply_text(data)
    return ConversationHandler.END


def get_services(update: Update, context):
    data = connectHost('get_services')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_repl_logs(update: Update, context):
    data = connectHost('get_repl_logs')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_emails(update: Update, context):
    data = connectDB('get_emails')
    update.message.reply_text(data)
    return ConversationHandler.END


def get_phones(update: Update, context):
    data = connectDB('get_phones')
    update.message.reply_text(data)
    return ConversationHandler.END


convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'add_to_db_phone': [MessageHandler(Filters.text & ~Filters.command, add_to_db_phone)],
        },
        fallbacks=[]
    )


convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'add_to_db_email': [MessageHandler(Filters.text & ~Filters.command, add_to_db_email)],
        },
        fallbacks=[]
    )


convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )


convHandlerGetRelease = ConversationHandler(
        entry_points=[CommandHandler('get_release', get_release)],
        states={
            'get_release': [MessageHandler(Filters.text & ~Filters.command, get_release)],
        },
        fallbacks=[]
    )


convHandlerGetUname = ConversationHandler(
        entry_points=[CommandHandler('get_uname', get_uname)],
        states={
            'get_uname': [MessageHandler(Filters.text & ~Filters.command, get_uname)],
        },
        fallbacks=[]
    )


convHandlerGetUptime = ConversationHandler(
        entry_points=[CommandHandler('get_uptime', get_uptime)],
        states={
            'get_uptime': [MessageHandler(Filters.text & ~Filters.command, get_uptime)],
        },
        fallbacks=[]
    )


convHandlerGetDf = ConversationHandler(
        entry_points=[CommandHandler('get_df', get_df)],
        states={
            'get_df': [MessageHandler(Filters.text & ~Filters.command, get_df)],
        },
        fallbacks=[]
    )


convHandlerGetFree = ConversationHandler(
        entry_points=[CommandHandler('get_free', get_free)],
        states={
            'get_free': [MessageHandler(Filters.text & ~Filters.command, get_free)],
        },
        fallbacks=[]
    )


convHandlerGetMpstat = ConversationHandler(
        entry_points=[CommandHandler('get_mpstat', get_mpstat)],
        states={
            'get_mpstat': [MessageHandler(Filters.text & ~Filters.command, get_mpstat)],
        },
        fallbacks=[]
    )


convHandlerGetW = ConversationHandler(
        entry_points=[CommandHandler('get_w', get_w)],
        states={
            'get_w': [MessageHandler(Filters.text & ~Filters.command, get_w)],
        },
        fallbacks=[]
    )


convHandlerGetAuth = ConversationHandler(
        entry_points=[CommandHandler('get_auth', get_auth)],
        states={
            'get_auth': [MessageHandler(Filters.text & ~Filters.command, get_auth)],
        },
        fallbacks=[]
    )


convHandlerGetCritical = ConversationHandler(
        entry_points=[CommandHandler('get_critical', get_critical)],
        states={
            'get_critical': [MessageHandler(Filters.text & ~Filters.command, get_critical)],
        },
        fallbacks=[]
    )


convHandlerGetPs = ConversationHandler(
        entry_points=[CommandHandler('get_ps', get_ps)],
        states={
            'get_ps': [MessageHandler(Filters.text & ~Filters.command, get_ps)],
        },
        fallbacks=[]
    )


convHandlerGetSs = ConversationHandler(
        entry_points=[CommandHandler('get_ss', get_ss)],
        states={
            'get_ss': [MessageHandler(Filters.text & ~Filters.command, get_ss)],
        },
        fallbacks=[]
    )


convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )


convHandlerGetServices = ConversationHandler(
        entry_points=[CommandHandler('get_services', get_services)],
        states={
            'get_services': [MessageHandler(Filters.text & ~Filters.command, get_services)],
        },
        fallbacks=[]
    )


convHandlerGetReplLogs = ConversationHandler(
        entry_points=[CommandHandler('get_repl_logs', get_repl_logs)],
        states={
            'get_repl_logs': [MessageHandler(Filters.text & ~Filters.command, get_repl_logs)],
        },
        fallbacks=[]
    )


convHandlerGetEmails = ConversationHandler(
        entry_points=[CommandHandler('get_emails', get_emails)],
        states={
            'get_emails': [MessageHandler(Filters.text & ~Filters.command, get_emails)],
        },
        fallbacks=[]
    )


convHandlerGetPhones = ConversationHandler(
        entry_points=[CommandHandler('get_phones', get_phones)],
        states={
            'get_phones': [MessageHandler(Filters.text & ~Filters.command, get_phones)],
        },
        fallbacks=[]
    )


def main():
    # Создайте программу обновлений и передайте ей токен вашего бота
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetRelease)
    dp.add_handler(convHandlerGetUname)
    dp.add_handler(convHandlerGetUptime)
    dp.add_handler(convHandlerGetDf)
    dp.add_handler(convHandlerGetFree)
    dp.add_handler(convHandlerGetMpstat)
    dp.add_handler(convHandlerGetW)
    dp.add_handler(convHandlerGetAuth)
    dp.add_handler(convHandlerGetCritical)
    dp.add_handler(convHandlerGetPs)
    dp.add_handler(convHandlerGetSs)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(convHandlerGetServices)
    dp.add_handler(convHandlerGetReplLogs)
    dp.add_handler(convHandlerGetEmails)
    dp.add_handler(convHandlerGetPhones)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
