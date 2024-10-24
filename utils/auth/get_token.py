T_TOKEN_PATH = "/home/alex/projects/t-invest-test/api_token"
TG_TOKEN_PATH = "/home/alex/projects/t-invest-test/tg_token"

def get_tbank_token():
    with open(T_TOKEN_PATH, 'r') as file:
        token = file.read()

    return token

def get_tg_token():
    with open(TG_TOKEN_PATH, 'r') as file:
        token = file.read()

    return token