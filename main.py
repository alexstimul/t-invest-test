from time import sleep

from bs4 import BeautifulSoup as bs
import requests

from tinkoff.invest import Client, CandleInterval

import telebot
from telebot import types

from utils.auth import get_token
from utils import utils
from constants.time_columns import TIME_COLUMNS

from classes.SharesInvest import SharesInvest

PATH = "models/decision-tree-model_shares_10.pickle"

REQUEST_HEADER = header = {'accept': '*/*',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(HTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}


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
    shares_client = None

    try:
        shares_client = SharesInvest()

        start_text = "Получаем информацию об акции"

        bot.send_message(user_id, start_text)
    except Exception as e:
        error_text = "Информация об акция сейчас не доступна. Попробуйте позже"
        bot.send_message(user_id, error_text)
        return

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

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_get_predict)
    keyboard.add(button_get_fin)
    bot.send_message(user_id, candles_message, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
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
    elif "get_company_AB" in call.data:
        pass

def get_companies_a(user_id):
    start_text = "Получение списка компаний класса А.\n\nПодождите, это займет несколько минут..."
    bot.send_message(user_id, start_text)

    url = 'https://smart-lab.ru/q/__TICKER__/f/y/'

    shares_client = SharesInvest()

    shares = shares_client.get_shares()

    shares_financials = []

    for share in shares:
        print(share["ticker"])
        request = requests.get(url.replace("__TICKER__", share["ticker"]), headers=REQUEST_HEADER)

        if request.status_code == 200:
            share_obj = { "name": share["name"], "ticker": share["ticker"], "net_income": [], "book_value": [], "debt": [], "roe": [] }

            soup = bs(request.content, 'html.parser')
            table = soup.find_all('table', {'class': 'simple-little-table financials'})

            if not table or len(table) < 1:
                continue

            rows = table[0].find_all('tr')

            for tr in rows:
                field = tr.get("field")

                if field == "net_income": # чистая прибыль
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["net_income"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["net_income"].append(value)
                elif field == "book_value": # собственный капитал = балансная стоимость
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["book_value"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["book_value"].append(value)
                elif field == "roe":
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and "%" in td.text and len(share_obj["roe"]) <= 5:
                            share_obj["roe"].append(float(td.text.replace(" ", "").split("%")[0]))
                elif field == "debt": # долгосрочный долг
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["debt"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["debt"].append(value)

            if len(share_obj["book_value"]) == 5 and len(share_obj["net_income"]) == 5:
                shares_financials.append(share_obj)

        sleep(2)

    print("All A:", len(shares_financials))

    shares_a = []

    for share_fin in shares_financials:
        last_net_income = share_fin["net_income"][-1]
        first_net_income = share_fin["net_income"][0]

        last_book_value = share_fin["book_value"][-1]
        first_book_value = share_fin["book_value"][0]

        if first_net_income > 0 and last_net_income > 0 and first_book_value > 0 and last_book_value > 0:
            net_income_up = (((last_net_income / first_net_income) ** (1 / 4)) - 1) * 100
            book_value_up = (((last_book_value / first_book_value) ** (1 / 4)) - 1) * 100
            mean_roe = sum(share_fin["roe"]) / len(share_fin["roe"])

            if net_income_up > 15 and book_value_up > 10 and mean_roe >= 15:
                shares_a.append({
                    "name": share_fin["name"],
                    "ticker": share_fin["ticker"],
                    "mean_income": net_income_up,
                    "mead_book_value": book_value_up,
                    "mean_roe": mean_roe
                })

    result_text = "Акции класса А:"

    for share_a in shares_a:
        result_text += f'\n\nИмя: {share_a["name"]}'
        result_text += f'\nТикер: {share_a["ticker"]}'
        result_text += f'\nРост прибыли: {"{:.2f}".format(share_a["mean_income"])}%'
        result_text += f'\nРост собственного капитала: {"{:.2f}".format(share_a["mead_book_value"])}%'
        result_text += f'\nСредняя рентабельность капитала: {"{:.2f}".format(share_a["mean_roe"])}%'

    result_text += "\n\n *Пока не учитывается долг компаний. В ближайшем обновлении будет"

    bot.send_message(user_id, result_text)

# todo запоминание данных
def get_companies_b(user_id):
    start_text = "Получение списка компаний класса Б.\n\nПодождите, это займет несколько минут..."
    bot.send_message(user_id, start_text)

    url = 'https://smart-lab.ru/q/__TICKER__/f/y/'

    shares_client = SharesInvest()

    shares = shares_client.get_shares()

    shares_financials = []

    for share in shares:
        print(share["ticker"])
        request = requests.get(url.replace("__TICKER__", share["ticker"]), headers=REQUEST_HEADER)

        if request.status_code == 200:
            share_obj = { "name": share["name"], "ticker": share["ticker"], "net_income": [], "book_value": [], "debt": [], "roe": [] }

            soup = bs(request.content, 'html.parser')
            table = soup.find_all('table', {'class': 'simple-little-table financials'})

            if not table or len(table) < 1:
                continue

            rows = table[0].find_all('tr')

            for tr in rows:
                field = tr.get("field")

                if field == "net_income": # чистая прибыль
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["net_income"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["net_income"].append(value)
                elif field == "book_value": # собственный капитал = балансная стоимость
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["book_value"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["book_value"].append(value)
                elif field == "roe":
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and "%" in td.text and len(share_obj["roe"]) <= 5:
                            share_obj["roe"].append(float(td.text.replace(" ", "").split("%")[0]))
                elif field == "debt": # долгосрочный долг
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["debt"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["debt"].append(value)

            if len(share_obj["book_value"]) == 5 and len(share_obj["net_income"]) == 5:
                shares_financials.append(share_obj)

        sleep(2)

    print("All B:", len(shares_financials))

    shares_a = []

    for share_fin in shares_financials:
        last_net_income = share_fin["net_income"][-1]
        first_net_income = share_fin["net_income"][0]

        last_book_value = share_fin["book_value"][-1]
        first_book_value = share_fin["book_value"][0]

        # todo убрать условие, оберунть вычисления в try except
        if first_net_income > 0 and last_net_income > 0 and first_book_value > 0 and last_book_value > 0:
            net_income_up = (((last_net_income / first_net_income) ** (1 / 4)) - 1) * 100
            book_value_up = (((last_book_value / first_book_value) ** (1 / 4)) - 1) * 100
            mean_roe = sum(share_fin["roe"]) / len(share_fin["roe"])

            if (0 <= net_income_up <= 20) and book_value_up <= 15 and mean_roe <= 15: # todo границы увеличины на 5, чтоб попадали пограничные акции
                shares_a.append({
                    "name": share_fin["name"],
                    "ticker": share_fin["ticker"],
                    "mean_income": net_income_up,
                    "mead_book_value": book_value_up,
                    "mean_roe": mean_roe
                })

    result_text = "Акции класса Б:"

    for share_a in shares_a:
        result_text += f'\n\nИмя: {share_a["name"]}'
        result_text += f'\nТикер: {share_a["ticker"]}'
        result_text += f'\nРост прибыли: {"{:.2f}".format(share_a["mean_income"])}%'
        result_text += f'\nРост собственного капитала: {"{:.2f}".format(share_a["mead_book_value"])}%'
        result_text += f'\nСредняя рентабельность капитала: {"{:.2f}".format(share_a["mean_roe"])}%'

    result_text += "\n\n *Пока не учитывается долг компаний. В ближайшем обновлении будет"

    bot.send_message(user_id, result_text)

def share_get_fin(ticker, user_id):
    start_text = "Получение списка компаний класса Б.\n\nПодождите, это займет несколько минут..."
    bot.send_message(user_id, start_text)

    url = 'https://smart-lab.ru/q/__TICKER__/f/y/'

    shares_client = SharesInvest()

    shares = [shares_client.get_share_by_ticker(ticker.upper())]

    shares_financials = []

    for share in shares:
        print(share["ticker"])
        request = requests.get(url.replace("__TICKER__", share["ticker"]), headers=REQUEST_HEADER)

        if request.status_code == 200:
            share_obj = {"name": share["name"], "ticker": share["ticker"], "net_income": [], "book_value": [],
                         "debt": [], "roe": []}

            soup = bs(request.content, 'html.parser')
            table = soup.find_all('table', {'class': 'simple-little-table financials'})

            if not table or len(table) < 1:
                continue

            rows = table[0].find_all('tr')

            for tr in rows:
                field = tr.get("field")

                if field == "net_income":  # чистая прибыль
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["net_income"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["net_income"].append(value)
                elif field == "book_value":  # собственный капитал = балансная стоимость
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["book_value"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["book_value"].append(value)
                elif field == "roe":
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and "%" in td.text and len(share_obj["roe"]) <= 5:
                            share_obj["roe"].append(float(td.text.replace(" ", "").split("%")[0]))
                elif field == "debt":  # долгосрочный долг
                    tds = tr.find_all('td')
                    for td in tds:
                        if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj["debt"]) < 5:
                            value = float(td.text.replace(" ", ""))
                            share_obj["debt"].append(value)

            shares_financials.append(share_obj)

    shares_a = []

    for share_fin in shares_financials:
        last_net_income = share_fin["net_income"][-1]
        first_net_income = share_fin["net_income"][0]

        last_book_value = share_fin["book_value"][-1]
        first_book_value = share_fin["book_value"][0]

        # todo убрать условие, оберунть вычисления в try except
        if first_net_income > 0 and last_net_income > 0 and first_book_value > 0 and last_book_value > 0:
            net_income_up = (((last_net_income / first_net_income) ** (1 / 4)) - 1) * 100
            book_value_up = (((last_book_value / first_book_value) ** (1 / 4)) - 1) * 100
            mean_roe = sum(share_fin["roe"]) / len(share_fin["roe"])

            shares_a.append({
                "name": share_fin["name"],
                "ticker": share_fin["ticker"],
                "mean_income": net_income_up,
                "mead_book_value": book_value_up,
                "mean_roe": mean_roe
            })


    result_text = ""

    for share_a in shares_a:
        result_text += f'Имя: {share_a["name"]}'
        result_text += f'\nТикер: {share_a["ticker"]}'
        result_text += f'\nРост прибыли: {"{:.2f}".format(share_a["mean_income"])}%'
        result_text += f'\nРост собственного капитала: {"{:.2f}".format(share_a["mead_book_value"])}%'
        result_text += f'\nСредняя рентабельность капитала: {"{:.2f}".format(share_a["mean_roe"])}%'

    result_text += "\n\n *Пока не учитывается долг компаний. В ближайшем обновлении будет"

    bot.send_message(user_id, result_text)

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
