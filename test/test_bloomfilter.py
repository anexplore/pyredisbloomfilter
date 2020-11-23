# -*- coding: utf-8 -*-
import unittest

import redis

import src.bloomfilter as bf
import src.exceptions as ep


class BloomFilterTest(unittest.TestCase):

    redis_host = ''
    redis_port = 6379
    redis_db = 0
    redis_client = None
    name = 'bloom_for_test'
    bloom_filter = None
    insertions = 10000
    error_rate = 0.001

    def setup_redis_client(self):
        self.redis_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=self.redis_db)

    def setUp(self):
        self.setup_redis_client()
        self.bloom_filter = bf.RedisBloomFilter(self.name, self.insertions, self.error_rate, self.redis_client)
        self.bloom_filter.initialize()

    def tearDown(self):
        self.bloom_filter.destroy()

    def test_bit_offsets(self):
        key = "abcefg"
        offsets = bf.bit_offsets(key, self.bloom_filter.number_of_hashes, self.bloom_filter.bits_number)
        self.assertTrue(len(offsets) == self.bloom_filter.number_of_hashes, 'offsets must be equal with number of hashes')
        for offset in offsets:
            self.assertGreater(offset, -1, 'offset must be greater than -1')

    def test_bloom_do_not_reuse_exists(self):
        anther_bloom_filter = bf.RedisBloomFilter(self.name, self.insertions, self.error_rate,
                                                  self.redis_client, auto_use_exists=False)
        self.assertRaises(ep.BloomFilterAlreadyExists, anther_bloom_filter.initialize)

    def test_put_none_or_empty(self):
        self.assertTrue(self.bloom_filter.put(None), 'put none must be true')
        self.assertTrue(self.bloom_filter.put(''), 'put empty must be true')

    def test_contains_none_or_empty(self):
        self.assertTrue(self.bloom_filter.contains(None), 'contains none is true')
        self.assertTrue(self.bloom_filter.contains(''), 'contains empty is true')

    def test_put_and_contains(self):
        key = 'hello test'
        not_exists_key = 'hello test gone'
        self.assertTrue(self.bloom_filter.put(key), 'put must success')
        self.assertTrue(self.bloom_filter.contains(key), 'must contains exists')
        self.assertFalse(self.bloom_filter.contains(not_exists_key),
                         'no exists key may not be report exists for only one data')
        self.assertTrue(key in self.bloom_filter, '__contains__ must work')

    def test_count(self):
        key = 'hello test'
        self.assertTrue(self.bloom_filter.put(key))
        self.assertTrue(self.bloom_filter.count() > 0)


if __name__ == '__main__':
    unittest.main()