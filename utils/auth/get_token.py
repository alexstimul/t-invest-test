TOKEN_PATH = "/media/alex/main/projects/t-invest-test/api_token"

def get_token():
    with open(TOKEN_PATH, 'r') as file:
        token = file.read()

    return token