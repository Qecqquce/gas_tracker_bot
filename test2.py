import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s -'
                              '%(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(filename="logger.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


url = 'https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=3PGU9XKJHQZEP3UUQUPAN6I2TMDSH3UEG8'
logger.info('start get_eth_price')
response = requests.get(url)
logger.info('2 get_eth_price')

if response.status_code == 200:
    data = response.text
    print(data)
else:
    print('Request failed with status code:', response.status_code)
