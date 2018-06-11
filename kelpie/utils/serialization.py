import numpy as np
import six
import datetime


class JSONableError(Exception):
    """Base class to handle errors associated with serializing data to JSON"""
    pass


def jsonable(data, ignore_failures=True):
    if data is None:
        return
    elif isinstance(data, (bool, int, float, six.string_types)):
        return data
    elif isinstance(data, datetime.datetime):
        return '{:4d}{:0>2d}{:0>2d}{:0>2d}{:0>2d}'.format(data.year, data.month, data.day, data.hour, data.minute)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        if ignore_failures:
            return
        else:
            error_message = 'Cannot serialize data type {}'.format(type(data))
            raise JSONableError(error_message)

