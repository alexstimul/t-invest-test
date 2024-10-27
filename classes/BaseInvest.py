from utils.auth import get_token

class BaseInvest:
    def __init__(self):
        self.token = get_token.get_tbank_token()

    def df_to_exel(self, name, df):
        df.to_excel(name)

    def df_to_csv(self, name, df):
        df.to_csv(name, index=None, header=True)