import os


class RunDirSettings(object):

    def __init__(self, conf, run_id):
        self._config = conf
        self._run_id = run_id

    @property
    def data_dir(self):
        return os.path.join(self._config.data_dir, self._run_id)

    @property
    def run_id(self):
        return self._run_id

    @property
    def category_urls(self):
        return os.path.join(self.data_dir, self._config.category_urls)

    @property
    def products_urls(self):
        return os.path.join(self.data_dir, self._config.products_urls)


class Settings(object):
    def __init__(self, conf, run_id):
        self._config = conf
        self._run_dir_settings = RunDirSettings(conf, run_id)

    @property
    def config(self):
        return self._config

    @property
    def run_settings(self):
        return self._run_dir_settings
