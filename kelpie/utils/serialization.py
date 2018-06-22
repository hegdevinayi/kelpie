import numpy
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
    elif isinstance(data, list):
        return [jsonable(v) for v in data]
    elif isinstance(data, datetime.datetime):
        return datetime_to_str(data)
    elif isinstance(data, numpy.ndarray):
        return jsonable(data.tolist())
    elif isinstance(data, (numpy.integer, numpy.floating, numpy.bool_)):
        return numpy.asscalar(data)
    elif isinstance(data, dict):
        json_data = {}
        for k, v in data.items():
            json_data[k] = jsonable(v)
        return json_data
    else:
        if ignore_failures:
            return
        else:
            error_message = 'Cannot serialize data type {}'.format(type(data))
            raise JSONableError(error_message)

