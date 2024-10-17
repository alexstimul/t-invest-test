from tinkoff.invest import Client
from tinkoff.invest.schemas import InstrumentExchangeType, GetAssetFundamentalsRequest
import pandas as pd

from utils.auth import get_token

class BaseInvest:
    def __init__(self):
        self.token = get_token.get_token()

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

    def df_to_exel(self, name, df):
        df.to_excel(name)


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

        # todo получать ид из акции (https://russianinvestments.github.io/investAPI/instruments/#share)
        with Client(self.token) as client:
            assets_id = []

            for asset in assets:
                instruments = client.instruments.find_instrument(
                    query=asset
                )
                print(instruments.instruments[0])
                assets_id.append(instruments.instruments[0].uid)

            request = GetAssetFundamentalsRequest(
                assets=assets_id,
            )

            r = client.instruments.get_asset_fundamentals(request=request)

            for asset in r.fundamentals:
                assets_list.append(self.__asset_dict_from_object(asset))

        assets_df = pd.DataFrame(assets_list)
        assets_df.set_index("id")

        return assets_df


def main():
    asset_client = AssetInvest()

    df = asset_client.get_asset_fundamentals(["Роснефть"])

    print(df.head())

main()