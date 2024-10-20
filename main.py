from time import sleep

import pandas as pd
from datetime import timedelta, datetime
import pytz

from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.schemas import InstrumentExchangeType, GetAssetFundamentalsRequest, InstrumentIdType, CandleSource
from tinkoff.invest.utils import now

from utils.auth import get_token
from constants.time_columns import TIME_COLUMNS


def utc_to_moscow(utc_datetime):
    tz_moscow = pytz.timezone('Europe/Moscow')

    utc_datetime = utc_datetime.replace(tzinfo=pytz.utc)
    moscow_datetime = utc_datetime.astimezone(tz_moscow)
    return moscow_datetime

class BaseInvest:
    def __init__(self):
        self.token = get_token.get_token()

    def df_to_exel(self, name, df):
        df.to_excel(name)

    def df_to_csv(self, name, df):
        df.to_csv(name, index=None, header=True)

class BondsInvest(BaseInvest):
    def __bond_dict_from_object(self, bond):
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "name": bond.name,
            # Tорговая площадка (секция биржи).
            "exchange": bond.exchange,
            # Количество выплат по купонам в год.
            "coupon_quantity_per_year": bond.coupon_quantity_per_year,
            # Дата погашения облигации по UTC.
            "maturity_date": bond.maturity_date.date(),
            # Первоначальный номинал облигации.
            "initial_nominal": bond.initial_nominal.units,
            "initial_nominal_curr": bond.initial_nominal.currency,
            # Номинал облигации.
            "nominal": bond.nominal.units,
            "nominal_curr": bond.nominal.currency,
            # Наименование страны риска — то есть страны, в которой компания ведёт основной бизнес.
            "country_of_risk_name": bond.country_of_risk_name,
            # Сектор экономики.
            "sector": bond.sector,
            # Признак облигации с плавающим купоном.
            "floating_coupon_flag": bond.floating_coupon_flag
        }

    def __coupon_dict_from_object(self, coupon):
        return {
            "coupon_date": coupon.coupon_date.date(),
            # todo складывать копейки (лежат в поле nano. Округлять до 2-х запятых)
            "pay_one_bond": coupon.pay_one_bond.units,
            "pay_one_bond_curr": coupon.pay_one_bond.currency,
            "coupon_type": coupon.coupon_type
        }

    def get_bonds(self, max_date = None):
        bonds_list = []

        with Client(self.token) as client:
            r = client.instruments.bonds(
                instrument_exchange=InstrumentExchangeType.INSTRUMENT_EXCHANGE_UNSPECIFIED
            )

            for bond in r.instruments:
                if bond.currency == "rub":
                    if not max_date:
                        bonds_list.append(self.__bond_dict_from_object(bond))
                    elif bond.maturity_date < max_date:
                        bonds_list.append(self.__bond_dict_from_object(bond))

        bonds_df = pd.DataFrame(bonds_list)
        bonds_df.set_index("ticker")

        return bonds_df

    def get_coupons_by_figi(self, figi):
        coupons_list = []

        with Client(self.token) as client:
            coupons = client.instruments.get_bond_coupons(figi=figi)

            for coupon in coupons.events:
                coupons_list.append(self.__coupon_dict_from_object(coupon))

        coupons_df = pd.DataFrame(coupons_list)

        return coupons_df


class AssetInvest(BaseInvest):
    def __asset_dict_from_object(self, asset):
        return {
            "id": asset.asset_uid,
            # Рыночная капитализация.
            "market_capitalization": asset.market_capitalization,
            # Процент форвардной дивидендной доходности по отношению к цене акций.
            "forward_annual_dividend_yield": asset.forward_annual_dividend_yield,
            # Среднегодовой рocт выручки за 3 года.
            "three_year_annual_revenue_growth_rate": asset.three_year_annual_revenue_growth_rate,
            # Среднегодовой рocт выручки за 5 лет.
            "five_year_annual_revenue_growth_rate": asset.five_year_annual_revenue_growth_rate,
            # Дивидендная доходность за 12 месяцев.
            "dividend_yield_daily_ttm": asset.dividend_yield_daily_ttm,
            # Выплаченные дивиденды за 12 месяцев.
            "dividend_rate_ttm": asset.dividend_rate_ttm,
            # Средняя дивидендная доходность за 5 лет.
            "five_years_average_dividend_yield": asset.five_years_average_dividend_yield,
            # Среднегодовой рост дивидендов за 5 лет.
            "five_year_annual_dividend_growth_rate": asset.five_year_annual_dividend_growth_rate,
            # Рост выручки за 1 год.
            "one_year_annual_revenue_growth_rate": asset.one_year_annual_revenue_growth_rate,
            # Изменение общего дохода за 5 лет.
            "revenue_change_five_years": asset.revenue_change_five_years
        }

    def get_asset_fundamentals(self, assets=None):
        assets_list = []

        if assets is None:
            assets = []

        with Client(self.token) as client:
            request = GetAssetFundamentalsRequest(
                assets=assets,
            )

            r = client.instruments.get_asset_fundamentals(request=request)

            for asset in r.fundamentals:
                assets_list.append(self.__asset_dict_from_object(asset))

        assets_df = pd.DataFrame(assets_list)
        assets_df.set_index("id")

        return assets_df


class SharesInvest(BaseInvest):
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
    def get_candle_by_year(self, instrument_id, interval):
        # ключ - дата, значение - массив свечей
        candles = {}
        with Client(self.token) as client:
            for candle in client.get_all_candles(
                instrument_id=instrument_id,
                from_=datetime.now().replace(hour=0, minute=0, second=0, tzinfo=pytz.utc) - timedelta(days=365), # todo return 365, 3 for tests
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
                            "open": float(f"{candle.open.units}.{f'0{candle.open.nano // 10000000}' if len(str(candle.open.nano)) == 8 else candle.open.nano // 10000000}"),
                            "high": float(f"{candle.high.units}.{f'0{candle.high.nano // 10000000}' if len(str(candle.high.nano)) == 8 else candle.high.nano // 10000000}"),
                            "low": float(f"{candle.low.units}.{f'0{candle.low.nano // 10000000}' if len(str(candle.low.nano)) == 8 else candle.low.nano // 10000000}"),
                            "close": float(f"{candle.close.units}.{f'0{candle.close.nano // 10000000}' if len(str(candle.close.nano)) == 8 else candle.close.nano // 10000000}")
                        })
                    else:
                        candles[candle_date] = [{
                            "time": candle_time,
                            "open": float(f"{candle.open.units}.{f'0{candle.open.nano // 10000000}' if len(str(candle.open.nano)) == 8 else candle.open.nano // 10000000}"),
                            "high": float(f"{candle.high.units}.{f'0{candle.high.nano // 10000000}' if len(str(candle.high.nano)) == 8 else candle.high.nano // 10000000}"),
                            "low": float(f"{candle.low.units}.{f'0{candle.low.nano // 10000000}' if len(str(candle.low.nano)) == 8 else candle.low.nano // 10000000}"),
                            "close": float(f"{candle.close.units}.{f'0{candle.close.nano // 10000000}' if len(str(candle.close.nano)) == 8 else candle.close.nano // 10000000}")
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

def main():
    shares_client = SharesInvest()

    """
    "name", "ticker", "class_code", "figi", "uid", "lot", "sector"
    """
    shares = shares_client.get_shares() # возвращает 80 акций
    print(shares[0])

    shares_and_candles = []

    # todo куча циклов в цикле, обязательно придумать что-то более оптимальное
    for share in shares:
        """
        "time", "open", "high", "low", "close"
        """
        candles = shares_client.get_candle_by_year(share["figi"], CandleInterval.CANDLE_INTERVAL_5_MIN)
        print("candles getted")
        # sleep(60)
        for date in candles.keys():
            candles_by_share = {
                "figi": share["figi"],
                "class_code": share["class_code"],
                "name": share["name"],
                "ticker": share["ticker"],
                "lot": share["lot"],
                "sector": share["sector"],
                "date": date,
            }

            # перебираем все свечи за один день
            for time_column in TIME_COLUMNS:
                value = None

                for candle in candles[date]:
                    if candle["time"] == time_column:
                        # Now get only close
                        value = candle["close"]

                candles_by_share[time_column] = value

            shares_and_candles.append(candles_by_share)
        break

    shares_df = pd.DataFrame(shares_and_candles)
    print(shares_df.head(15))
    exit(0)
    shares_client.df_to_csv("shares_test.csv", shares_df)

    # assets = shares_client.get_assets()
    #
    # print(assets[0])

    # asset_client = AssetInvest()
    # assets = ["40d89385-a03a-4659-bf4e-d3ecba011782"]
    #
    # assets_df = asset_client.get_asset_fundamentals(assets[:100])
    # print(assets_df.columns)

main()