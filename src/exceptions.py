# -*- coding: utf-8 -*-


class BloomFilterException(Exception):
    pass


class BloomFilterAlreadyExists(BloomFilterException):
    """
    the specific bloom filter identified by name already exists
    """
    pass


class BloomFilterParameterWrong(BloomFilterException):
    pass


class BloomFilterMissingSlots(BloomFilterException):
    pass


class BloomFilterAlreadyDestroyed(BloomFilterException):
    pass


class BloomFilterAlreadyInitialized(BloomFilterException):
    pass


class BloomFilterMustInitializeFirst(BloomFilterException):
    pass

