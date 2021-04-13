import logging
from abc import abstractmethod

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver


class Shop:
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def get_product_info(self, driver: WebDriver, url: str):
        pass

    @abstractmethod
    def get_category_urls(self, driver: WebDriver, url: str):
        pass

    @abstractmethod
    def get_product_urls(self, driver: WebDriver, url: str):
        pass

    @staticmethod
    def try_find(func, argument):
        try:
            result = func(argument).text
        except NoSuchElementException as e:
            logging.warning(f'something not found, {e}', exc_info=True)
            return 'None'
        except Exception as e:
            logging.error(f"{argument} not found?, error: {e}", exc_info=True)
            return 'None'
        return result
