# -*- coding: utf-8 -*-
"""
Python Bloom Filter Based on Redis

"""
import math
import threading

import mmh3
import redis

from . import exceptions

MAX_LONG_VALUE = 0x7fffffffffffffff
MAX_BITS_IN_ONE_STRING_SLOT = 2 ** 32


def lower_eight_parts_of_mmh3(mmh3_value):
    return mmh3_value & 0xffffffffffffffff


def height_eight_parts_of_mmh3(mmh3_value):
    return mmh3_value >> 64


def number_of_bits(number_of_insertion, error_rate):
    """
    compute number of bits need for element size inserts with error rate
    :param number_of_insertion: all inserts
    :param error_rate: error rate
    :return: bits number
    """
    if error_rate == 0:
        error_rate = 0.0000000000000001
    return int((-number_of_insertion * math.log(error_rate) / (math.log(2) * math.log(2)))) & MAX_LONG_VALUE


def number_of_hash_functions(number_of_insertion, bits_number):
    """
    compute number of hash functions for insertion size and bit number
    :param number_of_insertion: all inserts
    :param bits_number: bit number
    :return: number of hash functions
    """
    return max(1, int(round(float(bits_number) / number_of_insertion * math.log(2))))


def bit_offsets(key, number_of_hash_funcs, bits_number):
    """
    compute all offsets for key insertion
    :param key: key need to be inserted
    :param number_of_hash_funcs: number of hash functions
    :param bits_number: bits number
    :return: offset list
    """
    key_hash = mmh3.hash128(key, seed=0, signed=False)
    lower_hash = lower_eight_parts_of_mmh3(key_hash)
    height_hash = height_eight_parts_of_mmh3(key_hash)
    offsets = []
    combined_hash = lower_hash
    for _ in range(number_of_hash_funcs):
        offsets.append((combined_hash & MAX_LONG_VALUE) % bits_number)
        combined_hash += height_hash
    return offsets


class RedisBloomFilter(object):
    """
    bloom filter based on redis
    <p>if all inserts number is greater than MAX_BITS_IN_ONE_STRING_SLOT, then will use multi string instance</p>
    """

    REDIS_KEY_NUMBER_OF_INSERTION = 'number_of_insertion'
    REDIS_KEY_ERROR_RATE = 'error_rate'
    REDIS_KEY_INSERTIONS = 'insertions'

    def __init__(self, name, number_of_insertion, error_rate, redis_client, auto_use_exists=True, with_transaction=True):
        """
        set params
        :param name: the name of bloom filter, different bloom filter must have different name
        :param number_of_insertion: expected total unique insertions
        :param error_rate: error rate
        :param redis_client: redis client instance
        :param auto_use_exists: if already has a bloom filter has same name , reuse it
        :param with_transaction: if start transaction for set bits value.
                the only operation of bits is to set bit value = 1, so with no transaction may be ok for you and
                improve performance
        """
        self.name = name
        self.number_of_insertion = number_of_insertion
        self.error_rate = error_rate
        self.redis_client = redis_client
        self.auto_use_exists = auto_use_exists
        self.with_transaction = with_transaction
        self.bits_number = 0
        self.number_of_hashes = 0
        self.slot_number = 0
        self._inited = False
        self._destroyed = False
        self._stat_lock = threading.Lock()

    def _slot_name_of_index(self, index):
        return '{%s}_%s' % (self.name, index)

    def _stat_key_name(self):
        return '{%s}' % self.name

    def _slot_number(self):
        return int((self.bits_number + MAX_BITS_IN_ONE_STRING_SLOT - 1) / MAX_BITS_IN_ONE_STRING_SLOT)

    def _stat_check(self):
        with self._stat_lock:
            if not self._inited:
                raise exceptions.BloomFilterMustInitializeFirst()
            if self._destroyed:
                raise exceptions.BloomFilterAlreadyDestroyed()

    def _pipeline(self, force_transaction=False):
        try:
            return self.redis_client.pipeline(transaction=(self.with_transaction|force_transaction))
        except:
            # not support transaction
            return self.redis_client.pipeline()

    def initialize(self):
        """
        try to init bloom filter configs
        :raise BloomFilterParameterWrong if bloom setting in redis error
        :raise MissingBloomFilterSlot if some data slot is missing
        :raise redis.exceptions.RedisError if any redis error
        """
        with self._stat_lock:
            if self._inited:
                return
            # get bloom filter configs from redis, if not exist try to create
            number_of_insertion = self.redis_client.hget(self._stat_key_name(), self.REDIS_KEY_NUMBER_OF_INSERTION)
            already_exists = number_of_insertion is not None
            if already_exists and not self.auto_use_exists:
                raise exceptions.BloomFilterAlreadyExists()
            if already_exists:
                error_rate = self.redis_client.hget(self._stat_key_name(), self.REDIS_KEY_ERROR_RATE)
                if number_of_insertion is None or error_rate is None:
                    raise exceptions.BloomFilterParameterWrong()
                self.number_of_insertion = int(number_of_insertion)
                self.error_rate = float(error_rate)

            self.bits_number = number_of_bits(self.number_of_insertion, self.error_rate)
            self.number_of_hashes = number_of_hash_functions(self.number_of_insertion, self.bits_number)
            self.slot_number = self._slot_number()

            # if already exist, try to check all slot exists
            if already_exists:
                for i in range(self.slot_number):
                    if not self.redis_client.exists(self._slot_name_of_index(i)):
                        raise exceptions.BloomFilterMissingSlots()
            else:
                # try to save settings to redis and pre apply memory
                pipeline = self._pipeline(force_transaction=True)
                # remove old
                pipeline.delete(self._stat_key_name())
                for i in range(self.slot_number):
                    pipeline.delete(self._slot_name_of_index(i))
                # set stat data
                pipeline.hset(self._stat_key_name(), self.REDIS_KEY_NUMBER_OF_INSERTION, self.number_of_insertion)
                pipeline.hset(self._stat_key_name(), self.REDIS_KEY_ERROR_RATE, self.error_rate)
                # apply memory
                slots, offset = divmod(self.bits_number, MAX_BITS_IN_ONE_STRING_SLOT)
                for i in range(slots):
                    pipeline.setbit(self._slot_name_of_index(i), MAX_BITS_IN_ONE_STRING_SLOT - 1, 0)
                if offset > 0:
                    pipeline.setbit(self._slot_name_of_index(slots), offset, 0)
                pipeline.execute(raise_on_error=True)
            self._inited = True

    def put(self, key, retry_on_error=True):
        """
        put key to bloom filter
        :param key: key string
        :param retry_on_error retry if occurs redis error
        :return: True if set success else False, none or empty string returns True
        """
        self._stat_check()
        if key is None or key == '':
            return True
        offsets = bit_offsets(key, self.number_of_hashes, self.bits_number)
        newer = False
        while True:
            pipeline = self._pipeline()
            for offset in offsets:
                slot_index, slot_offset = divmod(offset, MAX_BITS_IN_ONE_STRING_SLOT)
                pipeline.setbit(self._slot_name_of_index(slot_index), slot_offset, 1)
            try:
                bit_changes = pipeline.execute(raise_on_error=True)
                # may loss some change for redis error retry or partly execute successfully. so count() is not accurate
                for bit_change in bit_changes:
                    if bit_change == 0:
                        newer = True
                        break
            except redis.RedisError:
                if retry_on_error:
                    continue
                else:
                    return False
            break
        if newer:
            # no retry here
            try:
                self.redis_client.hincrby(self._stat_key_name(), self.REDIS_KEY_INSERTIONS)
            except redis.RedisError:
                pass
        return True

    def contains(self, key, retry_on_error=True):
        """
        if key is already put into bloom filter
        :param key: key string
        :param retry_on_error retry if occurs redis error
        :return: True if contains else False, None or empty string returns True
        """
        self._stat_check()
        if key is None or key == '':
            return True
        offsets = bit_offsets(key, self.number_of_hashes, self.bits_number)
        bits = []
        while True:
            pipeline = self._pipeline()
            for offset in offsets:
                slot_index, slot_offset = divmod(offset, MAX_BITS_IN_ONE_STRING_SLOT)
                pipeline.getbit(self._slot_name_of_index(slot_index), slot_offset)
            try:
                bits = pipeline.execute(raise_on_error=True)
            except redis.RedisError:
                if retry_on_error:
                    continue
                else:
                    return False
            break
        for bit in bits:
            if bit != 1:
                return False
        return True

    def count(self):
        """
        :return: total number of elements that has been inserted. may not be accurate
        """
        self._stat_check()
        num = self.redis_client.hget(self._stat_key_name(), self.REDIS_KEY_INSERTIONS)
        return int(num) if num is not None else -1

    def destroy(self):
        """remove all data"""
        self._stat_check()
        with self._stat_lock:
            self._destroyed = True
            while True:
                pipeline = self._pipeline(force_transaction=True)
                pipeline.delete(self._stat_key_name())
                for i in range(self.slot_number):
                    pipeline.delete(self._slot_name_of_index(i))
                try:
                    pipeline.execute(raise_on_error=True)
                except redis.RedisError:
                    continue
                break

    def __contains__(self, item):
        return self.contains(item, retry_on_error=True)
