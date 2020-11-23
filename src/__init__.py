# -*- coding: utf-8 -*-

from .bloomfilter import RedisBloomFilter
from .exceptions import (
    BloomFilterException,
    BloomFilterMustInitializeFirst,
    BloomFilterAlreadyExists,
    BloomFilterAlreadyDestroyed,
    BloomFilterParameterWrong,
    BloomFilterAlreadyInitialized,
    BloomFilterMissingSlots
)

__version__ = '1.0.0'

__dict__ = [
    "RedisBloomFilter",
    'BloomFilterException',
    'BloomFilterMustInitializeFirst',
    'BloomFilterAlreadyExists',
    'BloomFilterAlreadyDestroyed',
    'BloomFilterParameterWrong',
    'BloomFilterAlreadyInitialized',
    'BloomFilterMissingSlots'
]