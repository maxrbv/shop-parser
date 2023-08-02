import logging

from tqdm import tqdm

import pandas as pd

from utils import get_session, read_json, create_dir
from settings import ASSETS_DIR, SHOPS_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__file__)


SHOP_NAME = 'lidl'
STORES_URL = 'https://www.lidl.com/stores'
BASE_API_URL = 'https://mobileapi.lidl.com/v1'


class Lidl:
    def __init__(self):
        self.session = get_session()
        self.selected_stores = []
        create_dir(ASSETS_DIR)

    def __get_stores(self):
        response = self.session.get(f'{BASE_API_URL}/stores?')
        if response.status_code == 200:
            data = response.json().get("results")
            logger.info(f'Successfully got {len(data)} stores')

            # Parse all stores
            stores = []
            for store in data:
                stores.append(
                    {
                        'state': store.get('address').get('state'),
                        'city': store.get('address').get('city'),
                        'id': store.get('id')
                    }
                )

            # Choose random shop from each state
            selected_cities = []
            for store in stores:
                if store['city'] not in selected_cities:
                    selected_cities.append(store['city'])
                    self.selected_stores.append(store)
            logger.info(f'Successfully chosen {len(self.selected_stores)} stores')
        else:
            logger.info('Error getting stores')

    def __get_products(self):
        products = read_json(SHOPS_DIR / 'lidl' / 'product_ids.json')
        logger.info(f'Got {len(products)} products to parse')

        for store in tqdm(self.selected_stores):
            store['products'] = []
            for product in products:
                data = self.session.get(f'{BASE_API_URL}/items/{product["id"]}/products?storeId={store["id"]}').json()
                product_data = {
                    'name': product['name']
                }
                try:
                    product_data['price'] = data.get('results')[0].get('price').get('currentPrice').get('value')
                    product_data['in_stock'] = True
                except:
                    product_data['price'] = 0
                    product_data['in_stock'] = False

                store['products'].append(product_data)

    def __dump_xlsx(self):
        df = pd.json_normalize(self.selected_stores, record_path='products', meta=['state', 'city', 'id'])
        df.to_excel(ASSETS_DIR / SHOP_NAME / 'products.xlsx', index=False)

    def parse_data(self):
        create_dir(ASSETS_DIR / SHOP_NAME)
        self.__get_stores()
        self.__get_products()
        self.__dump_xlsx()
