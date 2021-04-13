import os
import re

import yaml


class Config:
    def __init__(self, cfg):
        self._run_id = cfg['crawling']['run_id']
        self._shop = cfg['crawling']['shop']
        self._count_builder = cfg['crawling'][self._shop]['count_builder']
        self._start_url = cfg['crawling'][self._shop]['start_url']
        self._data_dir = os.path.join(self._shop, cfg['paths']['data_dir'])
        self._info_file = os.path.join(self._shop, cfg['paths']['info_file'])
        self._category_urls = cfg['paths']['category_urls']
        self._products_urls = cfg['paths']['products_urls']
        self._driver = cfg['paths']['driver']
        self._log_file = cfg['log']['file']
        self._logging_level = cfg['log']['level']
        self._bucket_name = cfg['storage']['google']['bucket_name']
        self._bucket_timeout = cfg['storage']['google']['timeout']

        self._redis_host = cfg['storage']['redis']['host']
        self._redis_port = cfg['storage']['redis']['port']
        self._redis_ttl = cfg['storage']['redis']['ttl']

    @property
    def shop(self):
        return self._shop

    @property
    def run_id(self):
        return self._run_id

    @property
    def start_url(self):
        return self._start_url

    @property
    def data_dir(self):
        return self._data_dir

    @property
    def info_file(self):
        return self._info_file

    @property
    def category_urls(self):
        return self._category_urls

    @property
    def products_urls(self):
        return self._products_urls

    @property
    def driver(self):
        return self._driver

    @property
    def log_file(self):
        return self._log_file

    @property
    def logging_level(self):
        return self._logging_level

    @property
    def bucket_name(self):
        return self._bucket_name

    @property
    def bucket_timeout(self):
        return self._bucket_timeout

    @property
    def count_builder(self):
        return self._count_builder

    @property
    def redis_host(self):
        return self._redis_host

    @property
    def redis_port(self):
        return self._redis_port

    @property
    def redis_ttl(self):
        return self._redis_ttl


def parse_config(filename):
    pattern = re.compile('^"?\\$\\{([^}^{]+)\\}"?$')

    def _path_constructor(loader, node):
        value = node.value
        match = pattern.match(value)
        env_var = match.group().strip('"${}')
        return os.environ.get(env_var) + value[match.end():]

    yaml.add_implicit_resolver('env', pattern, None, yaml.SafeLoader)
    yaml.add_constructor('env', _path_constructor, yaml.SafeLoader)

    with open(filename, "r") as f:
        cfg = yaml.load(f, Loader=yaml.SafeLoader)
    conf = Config(cfg)
    return conf
