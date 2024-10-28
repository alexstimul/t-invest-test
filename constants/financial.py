TICKER_PATTERN = '__TICKER__'
SMART_LAB_URL = f'https://smart-lab.ru/q/{TICKER_PATTERN}/f/y/'

SMART_LAB_REQUEST_HEADER = {'accept': '*/*',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(HTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

PROFIT = 'net_income'
CAPITAL = 'book_value'
ROE = 'roe'
DEBT = 'debt'