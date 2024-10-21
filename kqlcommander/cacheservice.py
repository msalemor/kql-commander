import asyncio


async def cache(key, json_data):
    await asyncio.sleep(.01)
    print("saving to cache:", key, json_data)


async def get_cache(key: str) -> str:
    await asyncio.sleep(.01)
    return None
