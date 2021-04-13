from time import sleep
from itertools import cycle
from selenium.webdriver.common.keys import Keys
import logging
import datetime

from es_crawler.shop.shop import Shop


class Ostin(Shop):
    def __init__(self):
        super().__init__("ostin")
        lst = [{
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/83.0.4103.97 Safari/537.36"},
            {
                "userAgent": "Mozilla/5.0 (X11; CrOS x86_64 10066.0.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/87.0.4280.66 Safari/537.36"},
            {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/78.0.3904.97 Safari/537.36 OPR/65.0.3467.48"},
            {
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/87.0.4280.66 Safari/537.36"}]
        self.userAgent = cycle(lst)

    def get_product_info(self, driver, url):
        self.prepare_driver(driver, url)
        sleep(2)
        brand = "Ostin"
        price_currency = self.try_find(driver.find_element_by_css_selector,
                                       '.o-product__price')
        if price_currency != 'None':
            price = ''.join(price_currency.split(" ")[:-1])
            currency = price_currency.split(" ")[-1]
        else:
            price = 'None'
            currency = 'None'

        goods_data = {
            "date": datetime.datetime.now().__str__(),
            "version": "0.0.2",
            "product_url": driver.current_url,
            "vendor_code": self.try_find(driver.find_element_by_css_selector, '.col .d-inline-block'),
            "brand": brand,
            "model_name": self.try_find(driver.find_element_by_css_selector, ".o-product__title"),
            "price": price,
            "currency": currency,
            "category": [x.text for x in
                         driver.find_elements_by_css_selector('.breadcrumbs__item .text-grey2')],
            "img_urls": [x.get_attribute("src") for x in driver.find_elements_by_css_selector(
                '.o-product-images__image img')],
            "composition": self.try_find(driver.find_element_by_xpath,
                                         '//text()[normalize-space() = "Состав"] /following::div[1]'),
            "description": self.try_find(driver.find_element_by_css_selector,
                                         '.o-product__description div').replace('\n', '.'),
            "alsobuy": list(set(map(lambda x: x.get_attribute('href'),
                                    driver.find_elements_by_css_selector(
                                        '.product-card')))),
            "similar": []
        }
        return goods_data

    def get_product_urls(self, driver, url):
        previous_len = 0
        self.prepare_driver(driver, url)
        sleep(3)
        while True:
            body = driver.find_element_by_css_selector('body')
            for _ in range(30):
                body.send_keys(Keys.PAGE_DOWN)
                sleep(0.5)
            try:
                urls = set(map(lambda x: x.get_attribute('href').split("?")[0],
                               driver.find_elements_by_css_selector('.product-card')))
            except Exception:
                return None
            logging.info(f' previous_len: {previous_len}, len(urls):{len(urls)}')
            if len(urls) == previous_len:
                return urls
            else:
                previous_len = len(urls)

    def get_category_urls(self, driver, url):
        self.prepare_driver(driver, url)
        sleep(5)
        urls = list(set(map(lambda x: x.get_attribute('href'),
                        driver.find_elements_by_css_selector('.subnavigation__link-container a'))))
        logging.info(f'get_category_urls save from {driver.current_url}\n len: {len(urls)}')
        urls.extend(list(set(map(lambda x: x.get_attribute('href'),
                                 driver.find_elements_by_css_selector(
                                     '.categories__name')))))
        logging.info(f'get_category_urls save from {driver.current_url}\n len: {len(urls)}')
        return set(urls)

    def prepare_driver(self, driver, url):
        driver.execute_cdp_cmd('Network.setUserAgentOverride', next(self.userAgent))
        driver.get(url)

