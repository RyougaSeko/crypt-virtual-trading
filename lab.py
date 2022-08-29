import requests
from bs4 import BeautifulSoup

# URL = 'https://images.coinviewer.io/currencies/64x64/bitcoin.png'

# try: 
#     currency_info = requests.get(URL).json() 
# except:
#     print("coudn't fetch crypt-price with bitbank_api")

page_url = 'https://cryptocurrencyliveprices.com/'
r = requests.get(page_url)
soup = BeautifulSoup(r.text, features="html.parser")
print(soup.find_all("img"))
