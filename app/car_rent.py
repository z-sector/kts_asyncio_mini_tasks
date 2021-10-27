import asyncio
from asyncio import Queue, Event
from collections import defaultdict
from typing import Optional, Any, Dict, Set

from app.const import MAX_PARALLEL_AGG_REQUESTS_COUNT


class PipelineContext:
    def __init__(self, user_id: int, data: Optional[Any] = None):
        self._user_id = user_id
        self.data = data

    @property
    def user_id(self):
        return self._user_id


CURRENT_AGG_REQUESTS_COUNT = 0
BOOKED_CARS: Dict[int, Set[str]] = defaultdict(set)


async def get_offers(source: str) -> list[dict]:
    await asyncio.sleep(1)
    return [
        {"url": f"http://{source}/car?id=1", "price": 1_000, "brand": "LADA"},
        {"url": f"http://{source}/car?id=2", "price": 5_000, "brand": "MITSUBISHI"},
        {"url": f"http://{source}/car?id=3", "price": 3_000, "brand": "KIA"},
        {"url": f"http://{source}/car?id=4", "price": 2_000, "brand": "DAEWOO"},
        {"url": f"http://{source}/car?id=5", "price": 10_000, "brand": "PORSCHE"},
    ]


async def get_offers_from_sourses(sources: list[str]) -> list[dict]:
    global CURRENT_AGG_REQUESTS_COUNT
    if CURRENT_AGG_REQUESTS_COUNT >= MAX_PARALLEL_AGG_REQUESTS_COUNT:
        await asyncio.sleep(10.0)

    CURRENT_AGG_REQUESTS_COUNT += 1
    # TODO реализовать получение всех предложений
    CURRENT_AGG_REQUESTS_COUNT -= 1

    out = list()
    # TODO корректно оформить данные в out

    return out


# TODO
async def chain_combine_service_offers(inbound: Queue, outbound: Queue, **kw):
    pass


# TODO
async def chain_filter_offers(
    inbound: Queue,
    outbound: Queue,
    brand: Optional[str] = None,
    price: Optional[int] = None,
    **kw,
):
    pass


async def cancel_book_request(user_id: int, offer: dict):
    await asyncio.sleep(1)
    BOOKED_CARS[user_id].remove(offer.get("url"))


async def book_request(user_id: int, offer: dict, event: Event) -> dict:
    await asyncio.sleep(1)
    BOOKED_CARS[user_id].add(offer.get("url"))

    return offer


# TODO
async def chain_book_car(inbound: Queue, outbound: Queue, **kw):
    pass


# TODO
def run_pipeline(inbound: Queue) -> Queue:
    pass
