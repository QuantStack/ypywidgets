import asyncio
import time

from ypywidgets import Widget


async def agetattr(widget: Widget, name: str, timeout=0.1, wait=0):
    await asyncio.sleep(wait)
    t = time.monotonic()
    while True:
        try:
            return getattr(widget, name)
        except KeyError:
            await asyncio.sleep(0)
            if time.monotonic() - t > timeout:
                raise TimeoutError(f"Timeout waiting for attribute: {name}")
