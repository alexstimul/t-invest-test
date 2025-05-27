from datetime import datetime, timedelta
import re
from itertools import count

import pytz
import requests
from bs4 import BeautifulSoup as bs
from utils import utils
from time import sleep

from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.schemas import InstrumentExchangeType, GetAssetFundamentalsRequest, InstrumentIdType, CandleSource

from classes.BaseInvest import BaseInvest
from utils.utils import utc_to_moscow
import constants.financial as fin


class SharesInvest(BaseInvest):
    def __init__(self):
        super().__init__()
        self.shares_financials = []

        self.get_shares_financials()

    def __get_smart_lab_data_content(self, ticker):
        try:
            request = requests.get(fin.SMART_LAB_URL.replace(fin.TICKER_PATTERN, ticker), headers=fin.SMART_LAB_REQUEST_HEADER)

            if request.status_code == 200 and request.content:
                return request.content

            return None
        except Exception as e:
            print(f'Error when get smart lab data. {e}')
            return None

    def __get_dohod_data_content(self, ticker):
        try:
            request = requests.get(fin.DOHOD_URL.replace(fin.TICKER_PATTERN, ticker), headers=fin.SMART_LAB_REQUEST_HEADER)

            if request.status_code == 200 and request.content:
                return request.content

            return None
        except Exception as e:
            print(f'Error when get smart lab data. {e}')
            return None

    def __parse_div_response(self, content, share_name, ticker):
        share_obj = {"name": share_name, "ticker": ticker, "few_divs": ''}

        soup = bs(content, 'html.parser')
        main_div = soup.find_all('div', {'id': 'leftside-col'})

        if not main_div or len(main_div) < 1:
            return None

        paragraphs = main_div[0].find_all('p')

        share_obj['few_divs'] = ' '.join(paragraphs[0].text.split())

        return share_obj

    def get_divs_by_share(self, ticker):
        share = self.get_share_by_ticker(ticker.upper())

        content = self.__get_dohod_data_content(ticker)
        share_divs = self.__parse_div_response(content, share["name"], share["ticker"])

        return share_divs['few_divs']

    def __parse_fin_response_for_classification(self, content, share_name, ticker):
        share_obj = {"name": share_name, "ticker": ticker, "net_income": [], "book_value": [], "debt": [], "roe": [], "eps": [], "p_e": [], "p_bv": []}

        soup = bs(content, 'html.parser')
        table = soup.find_all('table', {'class': 'simple-little-table financials'})

        if not table or len(table) < 1:
            return None

        rows = table[0].find_all('tr')

        for tr in rows:
            field = tr.get("field")

            if field == fin.PROFIT:  # чистая прибыль
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.PROFIT]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.PROFIT].append(value)
            elif field == fin.CAPITAL:  # собственный капитал = балансная стоимость
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.CAPITAL]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.CAPITAL].append(value)
            elif field == fin.ROE:
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and "%" in td.text and len(share_obj[fin.ROE]) <= 5:
                        share_obj[fin.ROE].append(float(td.text.replace(" ", "").split("%")[0]))
            elif field == fin.DEBT:  # долгосрочный долг
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.DEBT]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.DEBT].append(value)

            elif field == fin.EPS:  # собственный капитал = балансная стоимость
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.EPS]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.EPS].append(value)
            elif field == fin.P_E:  # собственный капитал = балансная стоимость
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.P_E]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.P_E].append(value)
            elif field == fin.P_BV:  # собственный капитал = балансная стоимость
                tds = tr.find_all('td')
                for td in tds:
                    if td.text and utils.is_number(td.text.replace(" ", "")) and len(share_obj[fin.P_BV]) < 5:
                        value = float(td.text.replace(" ", ""))
                        share_obj[fin.P_BV].append(value)

        return share_obj

    def __get_share_financials_by_ticker(self, ticker=None, share = None):
        content = self.__get_smart_lab_data_content(ticker if ticker else share['ticker'])

        if content:
            if share:
                return self.__parse_fin_response_for_classification(content, share["name"], share["ticker"])
            elif ticker:
                return self.__parse_fin_response_for_classification(content, ticker, ticker)

        return None

    def get_shares_financials(self):
        shares = self.get_shares()

        for share in shares:
            share_financial = self.__get_share_financials_by_ticker(share=share)

            if share_financial and len(share_financial[fin.CAPITAL]) == 5 and len(share_financial[fin.PROFIT]) == 5:
                self.shares_financials.append(share_financial)

                sleep(2)

        print(len(self.shares_financials))
        print("Get shares financials end")

    def __calculate_growth_indicators_by_share(self, share_fin):
        last_net_income = share_fin[fin.PROFIT][-1]
        first_net_income = share_fin[fin.PROFIT][0]

        last_book_value = share_fin[fin.CAPITAL][-1]
        first_book_value = share_fin[fin.CAPITAL][0]

        if first_net_income > 0 and last_net_income > 0 and first_book_value > 0 and last_book_value > 0:
            profit_growth = (((last_net_income / first_net_income) ** (1 / 4)) - 1) * 100
            capital_growth = (((last_book_value / first_book_value) ** (1 / 4)) - 1) * 100
            mean_roe = sum(share_fin[fin.ROE]) / len(share_fin[fin.ROE])

            return profit_growth, capital_growth, mean_roe

        return None, None, None

    def get_shares_by_class_a(self):
        shares_class_a = []

        for share_fin in self.shares_financials:
            profit, capital, roe = self.__calculate_growth_indicators_by_share(share_fin)

            if (not profit is None) and (not capital is None) and (not roe is None):
                if profit > 15 and capital > 10 and roe >= 15:
                    shares_class_a.append({
                        "name": share_fin["name"],
                        "ticker": share_fin["ticker"],
                        "profit": profit,
                        "capital": capital,
                        "mean_roe": roe
                    })

        return shares_class_a

    def get_shares_by_class_b(self):
        shares_class_b = []

        for share_fin in self.shares_financials:
            profit, capital, roe = self.__calculate_growth_indicators_by_share(share_fin)

            if (not profit is None) and (not capital is None) and (not roe is None):
                if (0 <= profit <= 20) and capital <= 15 and roe <= 15: # todo границы увеличины на 5, чтоб попадали пограничные акции
                    shares_class_b.append({
                        "name": share_fin["name"],
                        "ticker": share_fin["ticker"],
                        "profit": profit,
                        "capital": capital,
                        "mean_roe": roe
                    })

        return shares_class_b

    def get_share_financials(self, ticker):
        for share_fin in self.shares_financials:
            if ticker == share_fin["ticker"]:
                profit, capital, roe = self.__calculate_growth_indicators_by_share(share_fin)

                if (not profit is None) and (not capital is None) and (not roe is None):
                    return {
                        "name": share_fin["name"],
                        "ticker": share_fin["ticker"],
                        "profit": profit,
                        "capital": capital,
                        "mean_roe": roe
                    }

        return None

    def get_share_fin_classification_text(self, shares, class_type = "А"):
        result_text = f'Акции класса {class_type}:'

        for share in shares:
            result_text += f'\n\nИмя: {share["name"]}'
            result_text += f'\nТикер: {share["ticker"]}'
            result_text += f'\nРост прибыли: {"{:.2f}".format(share["profit"])}%'
            result_text += f'\nРост собственного капитала: {"{:.2f}".format(share["capital"])}%'
            result_text += f'\nСредняя рентабельность капитала: {"{:.2f}".format(share["mean_roe"])}%'

        result_text += "\n\n *Пока не учитывается долг компаний. В ближайшем обновлении будет"

        return result_text

    def __get_profit_avg_growth(self, share_fin):
        last_profit = share_fin[fin.PROFIT][-1]
        first_profit = share_fin[fin.PROFIT][0]

        return (((last_profit / first_profit) ** (1 / 4)) - 1) * 100

    def __get_capital_avg_growth(self, share_fin):
        last_capital = share_fin[fin.CAPITAL][-1]
        first_capital = share_fin[fin.CAPITAL][0]

        return (((last_capital / first_capital) ** (1 / 4)) - 1) * 100

    def __get_eps_growth(self, share_fin):
        last_eps = share_fin[fin.EPS][-1]
        first_eps = share_fin[fin.EPS][0]

        return (((last_eps / first_eps) ** (1/4)) - 1) * 100

    def __get_conservative_percent_growth(self, growth):
        if growth > 20:
            return 1.2
        elif 15 < growth <= 20:
            return 1.15
        elif 10 <= growth <= 15:
            return 1.1
        else:
            return 0

    def __avg_p_e(self, share_fin):
        sum_pe = sum(share_fin[fin.P_E])
        count_pe = len(share_fin[fin.P_E])

        isAnomaly = False
        anomalyIndex = -1

        for i in range(len(share_fin[fin.P_E])):
            isAnomaly = True
            anomalyIndex = i
            for j in range(len(share_fin[fin.P_E])):
                if i != j:
                    delta = abs(share_fin[fin.P_E][i] / share_fin[fin.P_E][j])
                    if 0.1 <= delta <= 10:
                        isAnomaly = False

            if isAnomaly:
                break

        if isAnomaly:
            sum_pe -= share_fin[fin.P_E][anomalyIndex]
            count_pe -= 1

        return sum_pe / count_pe

    def __get_avg_pbv(self, share_fin):
        return sum(share_fin[fin.P_BV]) / len(share_fin[fin.P_BV])

    def __parse_shares_count(self, content):
        soup = bs(content, 'html.parser')
        main_div = soup.find_all('div', {'id': 'rightside-col'})

        if not main_div or len(main_div) < 1:
            return None

        numbers = main_div[0].find_all('strong')
        if len(numbers) > 1:
            print(numbers[1].text)
            return float(numbers[1].text.split(" ")[0]) * 1_000_000

    def __get_shares_count(self, ticker):
        content = self.__get_dohod_data_content(ticker)
        if content:
            return self.__parse_shares_count(content)

        return None

    def __calc_potential_price_class_a(self, share_fin):
        profit_growth = self.__get_profit_avg_growth(share_fin)
        capital_growth = self.__get_capital_avg_growth(share_fin)

        if profit_growth >= 15 > capital_growth:
            growth = self.__get_eps_growth(share_fin)
            conservative_rate = self.__get_conservative_percent_growth(growth)
            avg_pe = self.__avg_p_e(share_fin)
            last_eps = share_fin[fin.EPS][-1]

            return (last_eps * (conservative_rate ** 4)) * avg_pe
        else:
            last_capital = share_fin[fin.CAPITAL][-1]
            last_capital_growth = last_capital * (1.2 ** 4)
            avg_pbv = self.__get_avg_pbv(share_fin)
            shares_count = self.__get_shares_count(share_fin['ticker'].lower())

            if shares_count and avg_pbv:
                potential_price = last_capital_growth * 1_000_000_000 / shares_count
                potential_price *= avg_pbv

                conservative_growth = self.__get_conservative_percent_growth(capital_growth)

                if conservative_growth > 0:
                    return potential_price / (conservative_growth ** 4)

        return None


    def __calc_potential_price_class_b(self, share_fin):
        profit_growth = self.__get_profit_avg_growth(share_fin)
        capital_growth = self.__get_capital_avg_growth(share_fin)
        avg_roe = sum(share_fin[fin.ROE]) / len(share_fin[fin.ROE])

        if profit_growth < 15 and capital_growth < 15 and avg_roe < 15:
            avg_pe = self.__avg_p_e(share_fin)

            return f'{avg_pe * 0.5} - {avg_pe * 0.7}'

        return None

    def get_potential_share_price(self, ticker):
        print(ticker)

        is_share_exist = False

        for share_fin in self.shares_financials:
            if ticker == share_fin["ticker"]:
                is_share_exist = True

                if len(share_fin[fin.EPS]) == 5 and len(share_fin[fin.P_E]) == 5:
                    shares_class_a = self.get_shares_by_class_a()
                    shares_class_b = self.get_shares_by_class_b()

                    for class_a in shares_class_a:
                        if share_fin['ticker'] == class_a['ticker']:
                            return self.__calc_potential_price_class_a(share_fin), None

                    for class_b in shares_class_b:
                        if share_fin['ticker'] == class_b['ticker']:
                            return None, self.__calc_potential_price_class_b(share_fin)

                    return self.__calc_potential_price_class_a(share_fin), self.__calc_potential_price_class_b(share_fin)

        if not is_share_exist:
            share_financial = self.__get_share_financials_by_ticker(ticker=ticker)

            if share_financial and len(share_financial[fin.CAPITAL]) == 5 and len(share_financial[fin.PROFIT]) == 5:
                if len(share_financial[fin.EPS]) == 5 and len(share_financial[fin.P_E]) == 5:
                    shares_class_a = self.get_shares_by_class_a()
                    shares_class_b = self.get_shares_by_class_b()

                    for class_a in shares_class_a:
                        if share_financial['ticker'] == class_a['ticker']:
                            return self.__calc_potential_price_class_a(share_financial), None

                    for class_b in shares_class_b:
                        if share_financial['ticker'] == class_b['ticker']:
                            return None, self.__calc_potential_price_class_b(share_financial)

                    return self.__calc_potential_price_class_a(share_financial), self.__calc_potential_price_class_b(share_financial)

        return None, None

    def get_reasonable_share_price(self, potential_price, rate):
        return potential_price / (rate ** 4)

    def get_shares(self):
        with Client(self.token) as client:
            instruments = client.instruments
            shares = []

            # цикл получает все акции, доступные для покупи и продажи, в рублях и торгуемые на основной moex бирже
            for method in ["shares"]:
                for item in getattr(instruments, method)().instruments:
                    if item.currency == "rub" \
                            and item.buy_available_flag == True \
                            and item.sell_available_flag == True \
                            and item.exchange == "MOEX_DEALER_WEEKEND":
                        shares.append(
                            {
                                "name": item.name,
                                "ticker": item.ticker,
                                "class_code": item.class_code,
                                "figi": item.figi,
                                "uid": item.uid,
                                "lot": item.lot,
                                "sector": item.sector
                            }
                        )

            return shares

    def get_share_by_ticker(self, ticker):
        shares = self.get_shares()

        for share in shares:
            if share["ticker"] == ticker:
                return share

        return None

    """
        instrument_id - figi

        CANDLE_INTERVAL_UNSPECIFIED = 0
        CANDLE_INTERVAL_1_MIN = 1
        CANDLE_INTERVAL_2_MIN = 6
        CANDLE_INTERVAL_3_MIN = 7
        CANDLE_INTERVAL_5_MIN = 2
        CANDLE_INTERVAL_10_MIN = 8
        CANDLE_INTERVAL_15_MIN = 3
        CANDLE_INTERVAL_30_MIN = 9
        CANDLE_INTERVAL_HOUR = 4
        CANDLE_INTERVAL_2_HOUR = 10
        CANDLE_INTERVAL_4_HOUR = 11
        CANDLE_INTERVAL_DAY = 5
        CANDLE_INTERVAL_WEEK = 12
        CANDLE_INTERVAL_MONTH = 13
    """

    def get_candle_by_year(self, instrument_id, interval, days=1):
        # ключ - дата, значение - массив свечей
        candles = {}
        with Client(self.token) as client:
            for candle in client.get_all_candles(
                    instrument_id=instrument_id,
                    from_=datetime.now().replace(hour=0, minute=0, second=0, tzinfo=pytz.utc) - timedelta(days=days),
                    # todo return 365, 3 for tests
                    interval=interval,
                    candle_source_type=CandleSource.CANDLE_SOURCE_UNSPECIFIED,
            ):
                # todo можно смотреть по закрытым
                if candle.time.strftime("%A") not in ["Saturday", "Sunday"]:
                    candle_full_time = utc_to_moscow(candle.time).strftime('%Y-%m-%d %H:%M:%S')
                    [candle_date, candle_time] = candle_full_time.split(" ")

                    if candle_date in candles.keys():
                        candles[candle_date].append({
                            "time": candle_time,
                            "open": float(
                                f"{candle.open.units}.{f'0{candle.open.nano // 10000000}' if len(str(candle.open.nano)) == 8 else candle.open.nano // 10000000}"),
                            "high": float(
                                f"{candle.high.units}.{f'0{candle.high.nano // 10000000}' if len(str(candle.high.nano)) == 8 else candle.high.nano // 10000000}"),
                            "low": float(
                                f"{candle.low.units}.{f'0{candle.low.nano // 10000000}' if len(str(candle.low.nano)) == 8 else candle.low.nano // 10000000}"),
                            "close": float(
                                f"{candle.close.units}.{f'0{candle.close.nano // 10000000}' if len(str(candle.close.nano)) == 8 else candle.close.nano // 10000000}")
                        })
                    else:
                        candles[candle_date] = [{
                            "time": candle_time,
                            "open": float(
                                f"{candle.open.units}.{f'0{candle.open.nano // 10000000}' if len(str(candle.open.nano)) == 8 else candle.open.nano // 10000000}"),
                            "high": float(
                                f"{candle.high.units}.{f'0{candle.high.nano // 10000000}' if len(str(candle.high.nano)) == 8 else candle.high.nano // 10000000}"),
                            "low": float(
                                f"{candle.low.units}.{f'0{candle.low.nano // 10000000}' if len(str(candle.low.nano)) == 8 else candle.low.nano // 10000000}"),
                            "close": float(
                                f"{candle.close.units}.{f'0{candle.close.nano // 10000000}' if len(str(candle.close.nano)) == 8 else candle.close.nano // 10000000}")
                        }]

        return candles

    def get_assets(self):
        assets_id = []
        with Client(self.token) as client:
            response = client.instruments.get_assets()
            for asset in response.assets:
                if asset.type == 4:
                    flag = False
                    for instrument in asset.instruments:
                        if instrument.instrument_kind == 2:
                            flag = True
                            break

                    if flag:
                        assets_id.append(asset.uid)

        return assets_id
