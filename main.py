from tinkoff.invest import Client, CandleInterval

import telebot
from telebot import types

from utils.auth import get_token
from utils import utils
from constants.time_columns import TIME_COLUMNS

from classes.SharesInvest import SharesInvest
from locales import locales

PATH = "models/decision-tree-model_shares_10.pickle"


bot = telebot.TeleBot(get_token.get_tg_token())
shares_client = SharesInvest()

def start_message(user_id):
    button_get_category_a = types.InlineKeyboardButton(locales.GET_SHARES_CLASS_A, callback_data=f'get_company_A')
    button_get_category_b = types.InlineKeyboardButton(locales.GET_SHARES_CLASS_B, callback_data=f'get_company_B')
    button_get_category_ab = types.InlineKeyboardButton(locales.GET_SHARES_CLASS_AB, callback_data=f'get_company_AB')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_get_category_a)
    keyboard.add(button_get_category_b)
    keyboard.add(button_get_category_ab)

    bot.send_message(user_id, locales.START_MESSAGE, reply_markup=keyboard)

def unknown_message(user_id):
    bot.send_message(user_id, locales.UNKNOWN_MESSAGE)

def help_message(user_id):
    bot.send_message(user_id, locales.HELP_MESSAGE)

def share_message(user_id, input_ticker):
    share = shares_client.get_share_by_ticker(input_ticker.upper())

    if not share:
        bot.send_message(user_id, locales.INVALID_TIKER)
        return

    bot.send_message(user_id, locales.GETTING_CANDLES_MESSAGE)

    candles = shares_client.get_candle_by_interval(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN, 5)

    candles_last_date = candles[list(candles.keys())[-1]]

    last_10_candles = candles_last_date[-10:]

    candles_message = "Тикер имеет следующие свечки за последний час:"

    for candle in last_10_candles:
        candles_message += f"\nВремя: {candle['time']} | Цена: {candle['close']} руб"

    button_get_predict = types.InlineKeyboardButton(locales.GET_PREDICT_BUTTON_NAME, callback_data=f'get_predict_{input_ticker}')
    button_get_fin = types.InlineKeyboardButton(locales.GET_FIN_BUTTON_NAME, callback_data=f'get_fin_{input_ticker}')
    button_get_potential_price = types.InlineKeyboardButton(locales.GET_RECOMMEND_TO_BUY_BUTTON_NAME, callback_data=f'get_potential_price_{input_ticker}')
    button_get_divs = types.InlineKeyboardButton(locales.GET_DIV_BUTTON_NAME, callback_data=f'get_divs_{input_ticker}')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_get_predict)
    keyboard.add(button_get_fin)
    keyboard.add(button_get_potential_price)
    keyboard.add(button_get_divs)
    bot.send_message(user_id, candles_message, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    print(call.data)
    if "get_predict_" in call.data:
        ticker = call.data.split("_")[-1]
        share_predict(ticker, call.message.chat.id)
    elif "get_fin_" in call.data:
        ticker = call.data.split("_")[-1]
        share_get_fin(ticker, call.message.chat.id)
    elif "get_company_A" in call.data:
        get_companies_a(call.message.chat.id)
    elif "get_company_B" in call.data:
        get_companies_b(call.message.chat.id)
    elif 'get_potential_price_' in call.data:
        ticker = call.data.split("_")[-1]
        get_potential_price(ticker, call.message.chat.id)
    elif 'get_divs_' in call.data:
        ticker = call.data.split("_")[-1]
        get_divs_by_share(ticker.lower(), call.message.chat.id)
    elif "get_company_AB" in call.data:
        pass

def get_companies_a(user_id):
    class_type = 'А'
    start_text = f'Получение списка компаний класса {class_type}.'
    bot.send_message(user_id, start_text)

    shares_class_a = shares_client.get_shares_by_class_a()
    text = shares_client.get_share_fin_classification_text(shares_class_a, class_type)

    bot.send_message(user_id, text)

def get_companies_b(user_id):
    class_type = 'Б'
    start_text = f'Получение списка компаний класса {class_type}.'
    bot.send_message(user_id, start_text)

    shares_class_b = shares_client.get_shares_by_class_b()
    text = shares_client.get_share_fin_classification_text(shares_class_b, class_type)

    bot.send_message(user_id, text)

def share_get_fin(ticker, user_id):
    start_text = f"Получение информации по тикеру {ticker}.\n\nПодождите, это займет несколько минут..."
    bot.send_message(user_id, start_text)

    share_financials = shares_client.get_share_financials(ticker)

    if share_financials:
        text = shares_client.get_share_fin_classification_text(share_financials)
    else:
        text = locales.NO_FINANCAL_DATA

    bot.send_message(user_id, text)

def share_predict(input_ticker, user_id):
    shares_client = None

    try:
        shares_client = SharesInvest()
    except Exception as e:
        error_text = "Предсказание сейчас недоступно. Попробуйте позже"
        bot.send_message(user_id, error_text)
        return

    share = shares_client.get_share_by_ticker(input_ticker.upper())

    if not share:
        error_text = "Вы ввели неправильный тикер. Попробуйте еще раз!"
        bot.send_message(user_id, error_text)
        return

    candles = shares_client.get_candle_by_interval(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN, 5)

    candles_last_date = candles[list(candles.keys())[-1]]

    last_10_candles = candles_last_date[-10:]

    x_predict = []

    for candle in last_10_candles:
        x_predict.append(candle['close'])

    start_predict_text = "Пытаюсь предсказать цены акций на следующие 4 часа..."
    bot.send_message(user_id, start_predict_text)

    model = None

    try:
        model = utils.load_model(PATH)
    except Exception as e:
        error_text = "Предсказание сейчас недоступно. Попробуйте позже"
        bot.send_message(user_id, error_text)
        return

    predict_text = "Предположительно, акции дальше будут иметь следующую стоимость:"

    for i in range(1, (4 * 12) + 1):
        y = model.predict([x_predict])
        symbol = '-' if y[0] < x_predict[-1] else '+'

        predict_text += f"\n{'{:.2f}'.format(y[0])} руб -> {symbol}"

        x_predict = x_predict[1:]
        x_predict.append(y[0])

    bot.send_message(user_id, predict_text)

def get_potential_price(input_ticker, user_id):
    potential_price_a, potential_price_b = shares_client.get_potential_share_price(input_ticker.upper())

    text = ''

    if potential_price_a:
        reasonable_price_3 = shares_client.get_reasonable_share_price(potential_price_a, 1.3)
        reasonable_price_5 = shares_client.get_reasonable_share_price(potential_price_a, 1.5)

        if reasonable_price_3 and reasonable_price_5:
            text = f'Потенциальная цена акции через 5 лет: {"{:.2f}".format(potential_price_a)} руб'
            text += f'\nРекомендуемся к покупке цена акции со скидкой 30%: {"{:.2f}".format(reasonable_price_3)} руб'
            text += f'\nРекомендуемся к покупке цена акции со скидкой 50%: {"{:.2f}".format(reasonable_price_5)} руб'

    if potential_price_b:
        enters = ''
        if text != '':
            enters = '\n\n'

        text += f'{enters}Если компания класса Б, то'
        text += f'\nРекомендуется покупать акцию, если отношение минимальной цены за акцию и EPS за текущий год находится в диапазоне или меньше {potential_price_b}'

    if text == '':
        text = 'Акция не рекомендуется к покупке'

    bot.send_message(user_id, text)

def get_divs_by_share(ticker, user_id):
    text = shares_client.get_divs_by_share(ticker)

    bot.send_message(user_id, text)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '/start':
        start_message(message.from_user.id)
    elif message.text == '/help':
        help_message(message.from_user.id)
    elif utils.is_only_latin_letters(message.text):
        share_message(message.from_user.id, message.text)
    else:
        unknown_message(message.from_user.id)



bot.polling(none_stop=True, interval=0)
