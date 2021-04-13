from redis import Redis


class Stream:
    def __init__(self, r: Redis, name: str):
        self._r = r
        self._name = name

    @property
    def name(self):
        return self._name

    def push(self, msg):
        self._r.xadd(self._name, msg)

    def pop(self, consumer_group, consumer_name, count=1):
        return self._r.xreadgroup(
            groupname=consumer_group,
            consumername=consumer_name,
            streams={self._name: '>'},
            count=count
        )

    def ack(self, consumer_group, msg_id):
        self._r.xack(self._name, consumer_group, msg_id)

    def balance(self, consumer_group, consumer_name):
        # XPENDING and XCLAIM change to XAUTOCLAIM
        result_pending = self._r.xpending(self._name, consumer_group)
        if result_pending:
            result = self._r.xclaim(
                name=self._name,
                groupname=consumer_group,
                consumername=consumer_name,
                min_idle_time=30000,
                message_ids=[result_pending['min'].decode('utf-8')]
            )
            self._r.xadd(self._name, {'url': result[0][1][b'url'].decode('utf-8')})
            self._r.xack(self._name, consumer_group, result[0][0])
