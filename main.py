from hypothesis.extra.pandas import column
from tinkoff.invest import Client
from tinkoff.invest.schemas import InstrumentExchangeType, GetBondCouponsRequest
import pandas as pd

from utils.auth import get_token

def get_client(token):
    with Client(token) as client:
        print(client.users.get_accounts())

def get_bonds(token):
    bonds_list = []
    coupons_list = []

    with Client(token) as client:
        # r = client.instruments.bonds(
        #     instrument_exchange=InstrumentExchangeType.INSTRUMENT_EXCHANGE_UNSPECIFIED
        # )
        # for bond in r.instruments:
        #     if bond.currency == "rub":
        #         bonds_list.append({
        #             "figi": bond.figi,
        #             "ticker": bond.ticker,
        #             "name": bond.name,
        #             "exchange": bond.exchange, # Tорговая площадка (секция биржи).
        #             "coupon_quantity_per_year": bond.coupon_quantity_per_year, # Количество выплат по купонам в год.
        #             "maturity_date": bond.maturity_date.date(), # Дата погашения облигации по UTC.
        #             "initial_nominal": bond.initial_nominal.units, # Первоначальный номинал облигации.
        #             "initial_nominal_curr": bond.initial_nominal.currency,
        #             "nominal": bond.nominal.units, # Номинал облигации.
        #             "nominal_curr": bond.nominal.currency,
        #             "country_of_risk_name": bond.country_of_risk_name, # Наименование страны риска — то есть страны, в которой компания ведёт основной бизнес.
        #             "sector": bond.sector, # Сектор экономики.
        #             "floating_coupon_flag": bond.floating_coupon_flag # Признак облигации с плавающим купоном.
        #         })
        #
        # request = GetBondCouponsRequest(
        #     instrument_id=bond.uid
        # )
        coupons = client.instruments.get_bond_coupons(figi="TCS00A107E08")

        for coupon in coupons.events:
            coupons_list.append({
                "coupon_date": coupon.coupon_date.date(),
                "pay_one_bond": coupon.pay_one_bond.units,
                "pay_one_bond_curr": coupon.pay_one_bond.currency,
                "coupon_type": coupon.coupon_type
            })

    # df = pd.DataFrame(bonds_list)
    # df.set_index("ticker")

    df = pd.DataFrame(coupons_list)
    print(df.head())

    # return df

def main():
    token = get_token.get_token()

    get_client(token)

    print("**************************************************************")

    df = get_bonds(token)

    # print(df.head())
    # print(df.shape)
    #
    # df.to_excel("Облигации 1.xlsx")

main()