from datetime import datetime, timedelta
import pytz

from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.schemas import InstrumentExchangeType, GetAssetFundamentalsRequest, InstrumentIdType, CandleSource

from classes.BaseInvest import BaseInvest
from utils.utils import utc_to_moscow


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
