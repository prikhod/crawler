from google.cloud.storage import Bucket
from redis import Redis
from selenium.webdriver.chrome.webdriver import WebDriver
from transliterate import translit
from time import sleep
import urllib.request
import os
import re
import logging
import json
from uuid import uuid4

from es_crawler.message_decode import MessageDecode
from es_crawler.shop.shop import Shop
from es_crawler.stream import Stream

NUM_TRY = 5


class Crawler:

    def __init__(self,
                 driver: WebDriver,
                 r: Redis,
                 stream: Stream,
                 consumer_group: str,
                 consumer_name: str,
                 num_others: int = 1,
                 count_builder_complete: str = '',
                 wait_others: bool = False
                 ):
        """
        :param r: Redis
        :param stream: wrapper for Redis stream
        :param consumer_group: consumer group for stream
        :param consumer_name: consumer name for stream
        :param num_others: number of other workers
        :param count_builder_complete: Redis variable for store complete builders
        :param wait_others: flag for wait other workers
        """
        self._r = r
        self._stream = stream
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._num_others = num_others
        self._wait_others = wait_others
        self._driver = driver
        self._num_try = NUM_TRY
        if self._wait_others:
            self._count_builder_complete = count_builder_complete

    @property
    def stream(self):
        return self._stream

    def process(self, url):
        pass

    def run(self):
        num_try = self._num_try
        test_count = 5
        while num_try and test_count:
            test_count = test_count - 1
            raw_msg = self.stream.pop(
                consumer_group=self._consumer_group,
                consumer_name=self._consumer_name,
                count=1
            )
            msg = MessageDecode(raw_msg)
            if msg.url:
                num_try = self._num_try
                try:
                    self.process(msg.url)
                except Exception as e:
                    # TODO think about improvement
                    # self.stream.push({'url': msg.url, 'fail_url': msg.url})
                    logging.error(f'{msg.url} are broken: {e}', exc_info=True)
                finally:
                    self.stream.ack(self._consumer_group, msg.id)

            else:
                num_try = num_try - 1
                if self._wait_others:
                    current_count = self._r.incr(self._count_builder_complete)
                    logging.info(f'current count complete: {current_count}, count builders: {self._num_others}')
                    for _ in range(10):
                        if self._num_others == current_count:
                            logging.info(f'finish job for {self._consumer_name} with all worker')
                            self._driver.quit()
                            return
                        sleep(6)
                        current_count = self._r.get(self._count_builder_complete)
                    self._r.decr(self._count_builder_complete)
                # TODO test balance function
                # self.stream.balance(self._consumer_group, self._consumer_name)
        self._driver.quit()


class CrawlerCategoryUrl(Crawler):

    def __init__(self, driver: WebDriver, run_id: int, shop: Shop, r: Redis, num_others: int):

        super().__init__(
            driver=driver,
            r=r,
            stream=Stream(r, f'category_stream_{shop.name}_{run_id}'),
            consumer_group=f'category_group_{shop.name}_{run_id}',
            consumer_name=str(uuid4()),
            num_others=num_others,
            count_builder_complete=f'count_builder_complete_{shop.name}_{run_id}',
            wait_others=True
        )
        self._run_id = run_id
        self._shop = shop
        self._r = r
        self._category_id = f'category_{shop.name}_{self._run_id}'

    def process(self, url):
        new_urls = self._shop.get_category_urls(self._driver, url)
        for url in new_urls:
            is_added = self._r.hsetnx(name=self._category_id, key=url, value='')
            if is_added:
                self.stream.push({'url': url})
        logging.info(f'{self._run_id} total category url: {self._r.hlen(self._category_id)}')


class CrawlerProductUrl(Crawler):

    def __init__(self, driver: WebDriver, run_id, shop: Shop, r: Redis):
        super().__init__(
            driver=driver,
            r=r,
            stream=Stream(r, f'product_url_stream_{shop.name}_{run_id}'),
            consumer_group=f'product_url_group_{shop.name}_{run_id}',
            consumer_name=str(uuid4()),
            wait_others=False
        )
        self._run_id = run_id
        self._shop = shop
        self._r = r
        self._product_url_id = f'product_url_{shop.name}_{self._run_id}'

    def process(self, url):
        products_urls = self._shop.get_product_urls(self._driver, url)

        for url in products_urls:
            self._r.hset(name=self._product_url_id, key=url, value='')
        logging.info(f'{self._run_id} total product url: {self._r.hlen(self._product_url_id)}')


class CrawlerProduct(Crawler):
    def __init__(self, driver: WebDriver, run_id, shop: Shop, r: Redis, bucket: Bucket, data_dir: str):
        super().__init__(
            driver=driver,
            r=r,
            stream=Stream(r, f'product_stream_{shop.name}_{run_id}'),
            consumer_group=f'product_group_{shop.name}_{run_id}',
            consumer_name=str(uuid4()),
            wait_others=False
        )
        self._run_id = run_id
        self._shop = shop
        self._bucket = bucket
        self._data_dir = data_dir

    def process(self, url):
        product_info = self._shop.get_product_info(self._driver, url)
        self.__save_goods_data(self._driver, product_info)
        logging.info(f'{self._run_id} product save from url: {url}')

    def __save_goods_data(self, driver, product_info):
        logging.info(f'saving from {driver.current_url}')
        if product_info["vendor_code"] == product_info["model_name"] == "None":
            logging.info(f'nothing save from {driver.current_url}')
            return None
        logging.info(f'{product_info}')
        img_dir = f'{product_info["vendor_code"]}_{product_info["brand"]}_{product_info["model_name"]}'[:80]
        img_dir = translit(img_dir, 'ru', reversed=True)
        img_dir = re.sub(r'\W+', '_', img_dir)
        img_dir = os.path.join(self._data_dir, 'data', img_dir)
        for name, img_url in enumerate(product_info["img_urls"]):
            name = f'{name}.jpg'
            try:
                with urllib.request.urlopen(img_url) as response:
                    blob = self._bucket.blob(os.path.join(img_dir, name))
                    blob.upload_from_string(response.read(), content_type=response.info().get_content_type())
            except Exception as e:
                logging.warning(f'# {product_info} urllib.request.urlopen: {e}', exc_info=True)
        blob = self._bucket.blob(os.path.join(os.path.join(f'{img_dir}', 'info.json')))
        blob.upload_from_string(json.dumps(product_info, ensure_ascii=False).encode('utf8'))
        logging.info(f'saved to {img_dir}')
