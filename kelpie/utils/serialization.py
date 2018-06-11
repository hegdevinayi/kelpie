import numpy as np
import six
import datetime


class JSONableError(Exception):
    """Base class to handle errors associated with JSON-serializing data."""
    pass


def datetime_to_str(time):
    return '{:0>4d}{:0>2d}{:0>2d}{:0>2d}{:0>2d}'.format(time.year, time.month, time.day, time.hour, time.minute)


def jsonable(data, ignore_failures=True):
    if data is None:
        return
    elif isinstance(data, (bool, int, float, six.string_types)):
        return data
    elif isinstance(data, datetime.datetime):
        return datetime_to_str(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        if ignore_failures:
            return
        else:
            error_message = 'Cannot serialize data type {}'.format(type(data))
            raise JSONableError(error_message)

