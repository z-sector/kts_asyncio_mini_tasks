import asyncio
from asyncio import Queue, Event
from collections import defaultdict
from typing import Optional, Any, Dict, Set, List, TypedDict

from app.const import MAX_PARALLEL_AGG_REQUESTS_COUNT, WORKERS_COUNT


class PipelineContext:
    def __init__(self, user_id: int, data: Optional[Any] = None):
        self._user_id = user_id
        self.data = data

    @property
    def user_id(self):
        return self._user_id


CURRENT_AGG_REQUESTS_COUNT = 0
BOOKED_CARS: Dict[int, Set[str]] = defaultdict(set)


def clear_booked_cars():
    BOOKED_CARS.clear()


class Offer(TypedDict):
    url: str
    price: int
    brand: str


async def get_offers(source: str) -> List[Offer]:
    await asyncio.sleep(1)
    return [
        {"url": f"http://{source}/car?id=1", "price": 1_000, "brand": "LADA"},
        {"url": f"http://{source}/car?id=2", "price": 5_000, "brand": "MITSUBISHI"},
        {"url": f"http://{source}/car?id=3", "price": 3_000, "brand": "KIA"},
        {"url": f"http://{source}/car?id=4", "price": 2_000, "brand": "DAEWOO"},
        {"url": f"http://{source}/car?id=5", "price": 10_000, "brand": "PORSCHE"},
    ]


async def get_offers_from_sourses(sources: List[str]) -> List[Offer]:
    global CURRENT_AGG_REQUESTS_COUNT
    if CURRENT_AGG_REQUESTS_COUNT >= MAX_PARALLEL_AGG_REQUESTS_COUNT:
        await asyncio.sleep(10.0)
    CURRENT_AGG_REQUESTS_COUNT += 1
    # TODO реализовать получение всех предложений
    responses: List[List[dict]] = await asyncio.gather(*[get_offers(s) for s in sources])
    CURRENT_AGG_REQUESTS_COUNT -= 1

    out = list()
    # TODO корректно оформить данные в out
    for r in responses:
        out.extend(r)

    return sorted(out, key=lambda x: x['url'])


async def worker_combine_service_offers(
        inbound: asyncio.Queue, outbound: asyncio.Queue, sem: asyncio.Semaphore
):
    while True:
        ctx: PipelineContext = await inbound.get()
        async with sem:
            ctx.data = await get_offers_from_sourses(ctx.data)
        await outbound.put(ctx)


# TODO
async def chain_combine_service_offers(inbound: Queue, outbound: Queue, **kw):
    sem = asyncio.Semaphore(MAX_PARALLEL_AGG_REQUESTS_COUNT)
    await asyncio.gather(
        *[worker_combine_service_offers(inbound, outbound, sem) for _ in range(WORKERS_COUNT)]
    )


# TODO
async def chain_filter_offers(
        inbound: Queue,
        outbound: Queue,
        brand: Optional[str] = None,
        price: Optional[int] = None,
        **kw,
):
    while True:
        cxt = await inbound.get()
        cxt.data = [
            o
            for o in cxt.data
            if (brand is None or o.get("brand") == brand) and (price is None or o.get("price") <= price)
        ]
        await outbound.put(cxt)


async def cancel_book_request(user_id: int, offer: dict):
    await asyncio.sleep(1)
    BOOKED_CARS[user_id].remove(offer.get("url"))


async def book_request(user_id: int, offer: dict, event: Event) -> dict:
    try:
        await asyncio.sleep(1)
        BOOKED_CARS[user_id].add(offer.get("url"))

        if event.is_set():
            event.clear()
        else:
            await event.wait()
    except asyncio.CancelledError:
        await cancel_book_request(user_id, offer)

    return offer


# TODO

async def worker_book_car(inbound: asyncio.Queue, outbound: asyncio.Queue):
    while True:
        cxt = await inbound.get()
        event = asyncio.Event()
        event.set()

        done, pending = await asyncio.wait(
            [asyncio.create_task(book_request(cxt.user_id, o, event)) for o in cxt.data],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for d in done:
            cxt.data = d.result()

        for p in pending:
            p.cancel()

        await asyncio.gather(*pending)

        await outbound.put(cxt)


async def chain_book_car(inbound: Queue, outbound: Queue, **kw):
    await asyncio.gather(
        *[asyncio.create_task(worker_book_car(inbound, outbound)) for _ in range(WORKERS_COUNT)]
    )


# TODO
def run_pipeline(inbound: Queue) -> Queue:
    agg_outbound = asyncio.Queue()
    filter_outbound = asyncio.Queue()
    book_outbound = asyncio.Queue()

    asyncio.create_task(chain_combine_service_offers(inbound, agg_outbound))
    asyncio.create_task(chain_filter_offers(agg_outbound, filter_outbound))
    asyncio.create_task(chain_book_car(filter_outbound, book_outbound))

    return book_outbound
