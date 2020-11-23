# -*- coding: utf-8 -*-
from __future__ import print_function

import redis

import redisbloomfilter

name = "bloom_filter"
number_of_insertion = 10000000
error_rate = 0.00001
redis_client = redis.StrictRedis()

bloom_filter = redisbloomfilter.RedisBloomFilter(name, number_of_insertion, error_rate, redis_client)
try:
    # call initialize first
    bloom_filter.initialize()
except redis.RedisError:
    print('occurs redis error')
    raise
except redisbloomfilter.BloomFilterException:
    # if auto_reuse_exists is False and alreay has one in redis, this will raise BloomFilterAlreadyExists
    # if bloom filter data in redis are deleted by hand, may raise BloomFilterParameterWrong or BloomFilterMissingSlots
    print('bloom filter exception')
    raise
print('put %s' % bloom_filter.put("abc"))
print('contains %s' % bloom_filter.contains("abc"))
print('count %s' % bloom_filter.count())
# call destroy will delete all bloom filter data in redis
bloom_filter.destroy()