# pyredisbloomfilter

python bloom filter based on redis

## python version
python2.7.x and python 3.5+ is supported 

## redis client requirements
basic dependency redis-py 

if your redis is in cluster mode, you must import rediscluter from package redis-py-cluster by yourself

> note: redis-py-cluster does not support pipeline with transaction

## install
~~~shell script
pip install redis-bloom-filter
~~~

## how to use
~~~python
import redis

import redisbloomfilter

name = "bloomfilter"
number_of_insertion = 10000000
error_rate = 0.00001
redis_client = redis.StrictRedis()

bloom_filter = redisbloomfilter.RedisBloomFilter(name, number_of_insertion, error_rate, redis_client)
try:
    bloom_filter.initialize()
except redis.RedisError:
    print('occurs redis error')
    raise
except redisbloomfilter.BloomFilterException:
    print('bloom filter exception')
    raise 
bloom_filter.put("abc")
bloom_filter.contains("abc")
~~~





