from selenium.webdriver import ChromeOptions, Chrome
from es_crawler.config import parse_config
from es_crawler.crawler import CrawlerProduct, CrawlerCategoryUrl, CrawlerProductUrl
from es_crawler.settings import Settings
from es_crawler.shop.hm import HM
from es_crawler.shop.lamoda import Lamoda
from es_crawler.shop.ostin import Ostin
from google.cloud import storage
import logging
import argparse
import redis


def build_driver(path_driver):
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--disable-blink-features")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument("--window-size=1920,1080")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 " \
                 "(KHTML, like Gecko) Chrome/89.0.4280.66 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    driver = Chrome(executable_path=path_driver, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
              const newProto = navigator.__proto__
              delete newProto.webdriver
              navigator.__proto__ = newProto
              """
    })
    return driver


def make_shop(name):
    shops = {
        'hm': HM,
        'lamoda': Lamoda,
        'ostin': Ostin
    }
    return shops[name]()


def make_crawler(settings: Settings, step: str):
    _redis = redis.Redis(host=settings.config.redis_host, port=settings.config.redis_port, db=0)
    shop = make_shop(settings.config.shop)
    driver = build_driver(settings.config.driver)
    if step == 'category_url':
        return CrawlerCategoryUrl(
            driver=driver,
            run_id=settings.run_settings.run_id,
            shop=shop,
            r=_redis,
            num_others=settings.config.count_builder
        )
    elif step == 'product_url':
        return CrawlerProductUrl(
            driver=driver,
            run_id=settings.run_settings.run_id,
            shop=shop,
            r=_redis
        )
    elif step == 'product':
        return CrawlerProduct(
            driver=driver,
            run_id=settings.run_settings.run_id,
            shop=shop,
            r=_redis,
            bucket=storage_client.bucket(settings.config.bucket_name),
            data_dir=settings.run_settings.data_dir
        )
    else:
        raise Exception(f'Wrong step name: {step}')


def run(settings, step):
    c = make_crawler(settings, step)
    c.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config file")
    parser.add_argument("-s", "--step", help="step crawling: category_url, product_url, product")
    args = parser.parse_args()
    config = parse_config(args.config)

    logging.basicConfig(level=config.logging_level, filename=config.log_file, filemode='a',
                        format='%(asctime)s : %(levelname)s : %(message)s')
    storage_client = storage.Client()
    run(Settings(config, config.run_id), args.step)

