
import asyncio
import aiofiles
import pickle
import time
from functools import wraps

try:
    file_error = FileNotFoundError
except NameError:
    file_error = IOError
    from errno import ENOENT

#
# Implements a simple caching utility via pickling to disk
#
lock = asyncio.Lock()


async def write_cache(filename, cache) -> None:
    """Write the cache dictionary to disk asynchronously."""
    async with lock:
        async with aiofiles.open(filename, 'w+b') as file:
            pickle.dump(cache, file)


async def read_cache(filename) -> bytes:
    """Read a cache dictionary from disk."""
    try:
        async with aiofiles.open(filename, mode='r+b') as file:
            cache = pickle.load(file)
    except file_error as e:
        if file_error is IOError:
            if e.errno != ENOENT:
                raise
        cache = {}
    return cache

FILE_NAME = "./cache.dat"


async def save_key(filename, key, value, ttl=3600) -> None:
    """Write a key:value pair to cache."""
    # ttl is "time to live" of the item in seconds
    # cache = await read_cache(filename)
    # expiry = int(time.time() + ttl)
    # cache[key] = (expiry, value)
    # await write_cache(filename, cache)
    await asyncio.sleep(.01)
    return None


async def load_key(filename, key) -> str | None:
    """Read the value for given key from cache."""
    # cache = await read_cache(filename)
    # try:
    #     expiry, value = cache[key]
    # except KeyError:
    #     return None
    # if time.time() > expiry:
    #     # Expired key, delete it
    #     del cache[key]
    #     await write_cache(filename, cache)
    #     return None
    # return value
    await asyncio.sleep(.01)
    return None


async def prune_cache(filename):
    """Go through the file and delete any expired items."""
    cache = read_cache(filename)
    now = time.time()
    for key in list(cache.keys()):
        # Creating a list because we're modifying cache
        expiry, __ = cache[key]
        if now > expiry:
            del cache[key]
    await write_cache(filename, cache)


def tuple_kwargs(kwargs):
    """Convert a flat dictionary to a tuple."""
    return tuple(sorted(kwargs.items()))


def cache_it(filename="simple.cache", ttl=3600):
    """Decorator for wrapping simple cache around functions."""
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple_kwargs(kwargs))
            value = load_key(filename, key)
            if value is None:
                value = func(*args, **kwargs)
                save_key(filename, key, value, ttl)
            return value
        return wrapper
    return decorate
