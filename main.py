from tinkoff.invest import Client, CandleInterval

import telebot
from telebot import types

from utils.auth import get_token
from utils import utils
from constants.time_columns import TIME_COLUMNS

from classes.SharesInvest import SharesInvest

PATH = "models/decision-tree-model_shares_10.pickle"

def test_api():
    shares_client = SharesInvest()

    """
    "name", "ticker", "class_code", "figi", "uid", "lot", "sector"
    """
    # shares = shares_client.get_shares() # возвращает 80 акций
    # print(shares[0])

    share = shares_client.get_share_by_ticker("ROSN")

    candles = shares_client.get_candle_by_year(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN)

    print(candles[list(candles.keys())[-1]])

    shares_and_candles = []

    # todo куча циклов в цикле, обязательно придумать что-то более оптимальное
    # for share in shares:
    #     """
    #     "time", "open", "high", "low", "close"
    #     """
    #     candles = shares_client.get_candle_by_year(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN)
    #     print("candles getted")
    #     # sleep(60)
    #     for date in candles.keys():
    #         candles_by_share = {
    #             "figi": share["figi"],
    #             "class_code": share["class_code"],
    #             "name": share["name"],
    #             "ticker": share["ticker"],
    #             "lot": share["lot"],
    #             "sector": share["sector"],
    #             "date": date,
    #         }
    #
    #         # перебираем все свечи за один день
    #         for time_column in TIME_COLUMNS:
    #             value = None
    #
    #             for candle in candles[date]:
    #                 if candle["time"] == time_column:
    #                     # Now get only close
    #                     value = candle["close"]
    #
    #             candles_by_share[time_column] = value
    #
    #         shares_and_candles.append(candles_by_share)
    #     break
    #
    # shares_df = pd.DataFrame(shares_and_candles)
    # print(shares_df.head(15))
    # exit(0)
    # shares_client.df_to_csv("shares_test.csv", shares_df)

    # assets = shares_client.get_assets()
    #
    # print(assets[0])

    # asset_client = AssetInvest()
    # assets = ["40d89385-a03a-4659-bf4e-d3ecba011782"]
    #
    # assets_df = asset_client.get_asset_fundamentals(assets[:100])
    # print(assets_df.columns)


bot = telebot.TeleBot(get_token.get_tg_token())
shares_client = SharesInvest()

def start_message(user_id):
    text = """
Привет! Это тестовый бот для работы с акциями и облигациями.

Тут ты можешь получить предсказания по ценам акции на ближайший час

Узнать информацию об облигациях

Получить финансовую отчетность интересной тебе компании
"""

    button_get_category_a = types.InlineKeyboardButton('Получить акции категории А', callback_data=f'get_company_A')
    button_get_category_b = types.InlineKeyboardButton('Получить акции категории Б', callback_data=f'get_company_B')
    button_get_category_ab = types.InlineKeyboardButton('Получить акции категории А и Б', callback_data=f'get_company_AB')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_get_category_a)
    keyboard.add(button_get_category_b)
    keyboard.add(button_get_category_ab)
    bot.send_message(user_id, text, reply_markup=keyboard)

def unknown_message(user_id):
    text = "Напиши /start или /help для получения полезной информации"

    bot.send_message(user_id, text)

def help_message(user_id):
    text = "Когда-нибудь тут будет полезная информация"

    bot.send_message(user_id, text)

def share_message(user_id, input_ticker):
    share = shares_client.get_share_by_ticker(input_ticker.upper())

    if not share:
        error_text = "Вы ввели неправильный тикер. Попробуйте еще раз!"
        bot.send_message(user_id, error_text)
        return

    start_candles_text = "Получаем информацию о свечках"

    bot.send_message(user_id, start_candles_text)

    candles = shares_client.get_candle_by_year(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN, 5)

    candles_last_date = candles[list(candles.keys())[-1]]

    last_10_candles = candles_last_date[-10:]

    candles_message = "Тикер имеет следующие свечки за последний час:"

    for candle in last_10_candles:
        candles_message += f"\nВремя: {candle['time']} | Цена: {candle['close']} руб"

    button_get_predict = types.InlineKeyboardButton('Получить предсказание', callback_data=f'get_predict_{input_ticker}')
    button_get_fin = types.InlineKeyboardButton('Получить финансовый отчет за 5 лет', callback_data=f'get_fin_{input_ticker}')
    button_get_potential_price = types.InlineKeyboardButton('Получить потенциальную стоимость акции и рекомендованную к покупке', callback_data=f'get_potential_price_{input_ticker}')
    button_get_divs = types.InlineKeyboardButton('Получить информацию о дивидендах', callback_data=f'get_divs_{input_ticker}')

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
        text = "Финансовые данные по указанной компании не найдены"

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

    candles = shares_client.get_candle_by_year(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN, 5)

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
    potential_price = shares_client.get_potential_share_price(input_ticker.upper())

    text = "Акция не рекомендуется к покупке"

    if potential_price:
        reasonable_price = shares_client.get_reasonable_share_price(potential_price, 1.3)

        if reasonable_price:
            text = f'Потенциальная цена акции через 5 лет: {"{:.2f}".format(potential_price)} руб'
            text += f'\nРекомендуемся к покупке цена акции: {"{:.2f}".format(reasonable_price)} руб'

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

"""
2 - 2440.65
48.39

"""