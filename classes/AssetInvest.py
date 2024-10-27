import pandas as pd

from tinkoff.invest import Client
from tinkoff.invest.schemas import GetAssetFundamentalsRequest

from classes.BaseInvest import BaseInvest


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