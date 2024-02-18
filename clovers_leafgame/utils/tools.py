import httpx
import asyncio
import numpy as np
from io import BytesIO


async def download_url(url: str) -> BytesIO:
    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                return BytesIO(resp.content)
            except Exception:
                await asyncio.sleep(3)
    return None


def format_number(num) -> str:
    """
    格式化金币
    """
    if num < 10000:
        return "{:,}".format(num if isinstance(num, int) else round(num, 2))
    x = str(int(num))
    if 10000 <= num < 100000000:
        y = int(x[-4:])
        if y:
            return f"{x[:-4]}万{y}"
        return f"{x[:-4]}万"
    if 100000000 <= num < 1000000000000:
        y = int(x[-8:-4])
        if y:
            return f"{x[:-8]}亿{y}万"
        return f"{x[:-8]}亿"
    if 1000000000000 <= num:
        y = int(x[-8:-4])
        z = round(int(x[:-8]) / 10000, 2)
        if y:
            return f"{z}万亿{y}万"
        return f"{z}万亿"


def gini_coef(wealths: list) -> float:
    """
    计算基尼系数
    """
    wealths.insert(0, 0)
    wealths_cum = np.cumsum(wealths)
    wealths_sum = wealths_cum[-1]
    N = len(wealths_cum)
    S = np.trapz(wealths_cum / wealths_sum, np.array(range(N)) / (N - 1))
    return 1 - 2 * S


def integer_log(number, base) -> int:
    result = 0
    while number >= base:
        number /= base
        result += 1
    return result
