import os

from flask import Flask
from flask import request
from flask import jsonify
from flask_sslify import SSLify
import requests
import misc
import gspread
from gspread_formatting import get_user_entered_format
from oauth2client.service_account import ServiceAccountCredentials
import re
import time

from constants import Format
from helpers import get_cell_templates

app = Flask(__name__)
sslify = SSLify(app)


token = misc.token
URL = 'https://api.telegram.org/bot' + token + '/'
global last_update_id
last_update_id = 0


def send_message(chat_id, text='Type your order'):
    url = URL + 'sendMessage?chat_id={}&text={}'.format(chat_id, text)
    return requests.get(url)


def create_connection():
    scope = ["https://spreadsheets.google.com/feeds",
             'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/mrsmilez3/bot/Creds.json', scope)
    client = gspread.authorize(creds)
    document = client.open('Transfercopy')
    sheet = document.worksheet('Производство')
    answer_sheet = document.worksheet('telegram-bot')
    return sheet, answer_sheet


def order_validation(order_number):
    if order_number.isdigit() and len(order_number) == 7:
        return True
    else:
        return False


def order_status(number_order, sheet, answer_sheet):
    number_order, sheet, answer_sheet = number_order, sheet, answer_sheet
    order = re.compile(f'{number_order}')
    all_orders = sheet.findall(order)
    print(all_orders)
    list_of_answers = answer_sheet.col_values(4)
    if all_orders:
        result = ''
        for data in all_orders:
            data = str(data)
            row_coordinate = int(re.search(r'(R[0-9]+)', data).group(0)[1:])
            print('row_coordinate',row_coordinate)
            col_coordinate = int(
                re.search(r'(C[0-9]+)', data).group(0)[1:]) - 1
            print('col_coordinate',col_coordinate)
            cell_address = sheet.cell(row_coordinate, col_coordinate).address
            print('cell_address',cell_address)
            steel_type = sheet.cell(row_coordinate, 4).value
            steel_depth = sheet.cell(row_coordinate, 5).value
            check_f_row = f'F{row_coordinate}'

            templates = get_cell_templates(answer_sheet, Format)
            user_cell = get_user_entered_format(sheet,
                                       f'{cell_address}').backgroundColor
            user_f_row_cell = get_user_entered_format(sheet,
                                         f'{check_f_row}').backgroundColor

            if user_cell == templates[Format.A5]:
                result = result + f'Детали из {steel_type} толщиной {steel_depth} - {list_of_answers[8]}\n\n'
            elif user_cell == templates[Format.A3] and user_f_row_cell == templates[Format.A4]:
                result = result + f'Детали из {steel_type} толщиной {steel_depth} - {list_of_answers[6]}\n\n'
            elif user_cell == templates[Format.A4]:
                result = result + f'Детали из {steel_type} толщиной {steel_depth} - {list_of_answers[7]}\n\n'
            elif user_cell == templates[Format.A3] and user_f_row_cell == templates[Format.A3]:
                result = result + f'Детали из {steel_type} толщиной {steel_depth} - {list_of_answers[5]}\n\n'
            else:
                result = result + f'Детали из {steel_type} толщиной {steel_depth} - {list_of_answers[4]}\n\n'
    else:
        result = f'''{number_order} - {list_of_answers[3]}'''
    return result


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        print('Подождите 30 секунд')

        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text']

        send_message(chat_id, f'Обрабатываю Ваш запрос. Это может занять некоторое время.')
        print(r)
        print(r['update_id'])

        if not order_validation(message):
            first_answer = 'Номер заказа должен состоять из 7 цифр'
            send_message(chat_id, first_answer)
        else:
            time.sleep(30)
            first_answer = f'Ищу ваш заказ №{message}. Ожидайте...'
            send_message(chat_id, first_answer)
            sheet, answer_sheet = create_connection()
            res = order_status(message, sheet, answer_sheet)
            # res = 1

            send_message(chat_id, res)
            print(res)

        return jsonify(r)
    return '<h1>Hello 9world</h1>'


if __name__ == '__main__':
    # app.run(port=int(os.environ.get('BOT_PORT') or 5000))
    app.run()