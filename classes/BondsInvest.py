import pandas as pd

from tinkoff.invest import Client
from tinkoff.invest.schemas import InstrumentExchangeType

from classes.BaseInvest import BaseInvest

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
