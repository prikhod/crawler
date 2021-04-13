import logging


class MessageDecode:
    def __init__(self, msg):
        try:
            self._url = msg[0][1][0][1][b'url'].decode('utf-8')
            self._id = msg[0][1][0][0].decode('utf-8')
        except Exception as e:
            logging.warning(f'empty url or id from msg: {msg}, error: {e}', exc_info=True)
            self._url = None
            self._id = None

    @property
    def url(self):
        return self._url

    @property
    def id(self):
        return self._id
