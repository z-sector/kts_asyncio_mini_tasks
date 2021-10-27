import asyncio
import time
from asyncio import Queue

import pytest

from app.car_rent import (
    chain_combine_service_offers,
    chain_filter_offers,
    chain_book_car,
    PipelineContext,
    BOOKED_CARS,
)
from tests import AGGREGATOR_REQUEST, gen_offers, AGGREGATOR_RESPONSE, run_chain

pytestmark = pytest.mark.asyncio


class TestChainCombineService:
    async def test_correct_output(self, event_loop, user_id):
        inbound = Queue()
        outbound = run_chain(chain_combine_service_offers, inbound)

        inbound.put_nowait(PipelineContext(user_id, AGGREGATOR_REQUEST))

        ctx = await outbound.get()

        assert ctx.data == AGGREGATOR_RESPONSE

    async def test_time_execution(self, event_loop, user_id):
        inbound = Queue()
        outbound = run_chain(chain_combine_service_offers, inbound)

        inbound.put_nowait(PipelineContext(user_id, AGGREGATOR_REQUEST))

        await asyncio.wait_for(outbound.get(), timeout=2.0)

    async def test_gathers_count(self, event_loop):
        inbound = Queue()
        outbound = run_chain(chain_combine_service_offers, inbound)

        chunks_count = 7
        for i in range(chunks_count):
            inbound.put_nowait(PipelineContext(i + 1, AGGREGATOR_REQUEST))

        timeout = 8.0
        start = time.time()

        res = list()
        for i in range(chunks_count):

            ctx = await outbound.get()
            res.append(ctx.data)

        assert res == [AGGREGATOR_RESPONSE for _ in range(chunks_count)]

        duration = time.time() - start
        assert timeout >= duration


class TestChainFilter:
    @pytest.mark.parametrize(
        "brand, price, result",
        [
            (
                "LADA",
                None,
                [{"url": f"http://source/car?id=1", "price": 1_000, "brand": "LADA"}],
            ),
            (
                "MITSUBISHI",
                None,
                [
                    {
                        "url": f"http://source/car?id=2",
                        "price": 5_000,
                        "brand": "MITSUBISHI",
                    }
                ],
            ),
            (
                "KIA",
                None,
                [{"url": f"http://source/car?id=3", "price": 3_000, "brand": "KIA"}],
            ),
            (
                "DAEWOO",
                None,
                [{"url": f"http://source/car?id=4", "price": 2_000, "brand": "DAEWOO"}],
            ),
            (
                "PORSCHE",
                None,
                [
                    {
                        "url": f"http://source/car?id=5",
                        "price": 10_000,
                        "brand": "PORSCHE",
                    }
                ],
            ),
            (
                None,
                1_000,
                [{"url": f"http://source/car?id=1", "price": 1_000, "brand": "LADA"}],
            ),
            (
                None,
                3_000,
                [
                    {"url": f"http://source/car?id=1", "price": 1_000, "brand": "LADA"},
                    {"url": f"http://source/car?id=3", "price": 3_000, "brand": "KIA"},
                    {
                        "url": f"http://source/car?id=4",
                        "price": 2_000,
                        "brand": "DAEWOO",
                    },
                ],
            ),
            (
                "PORSCHE",
                10_000,
                [
                    {
                        "url": f"http://source/car?id=5",
                        "price": 10_000,
                        "brand": "PORSCHE",
                    }
                ],
            ),
        ],
    )
    async def test_correct_filter(self, event_loop, user_id, brand, price, result):
        inbound = Queue()
        outbound = run_chain(chain_filter_offers, inbound, brand=brand, price=price)

        inbound.put_nowait(PipelineContext(user_id, gen_offers("source")))

        ctx = await outbound.get()
        assert ctx.data == result

    async def test_time_execution(self, event_loop, user_id):
        inbound = Queue()
        outbound = run_chain(chain_filter_offers, inbound)

        inbound.put_nowait(PipelineContext(user_id, gen_offers("source")))

        await asyncio.wait_for(outbound.get(), timeout=0.1)


class TestChainBooking:
    async def test_time_execution(self, event_loop, user_id):
        inbound = Queue()
        outbound = run_chain(chain_book_car, inbound)

        inbound.put_nowait(PipelineContext(user_id, gen_offers("source")))

        await asyncio.wait_for(outbound.get(), timeout=2.5)

    async def test_1_booked_car(self, event_loop, user_id):
        inbound = Queue()
        outbound = run_chain(chain_book_car, inbound)

        inbound.put_nowait(PipelineContext(user_id, gen_offers("source")))

        ctx = await outbound.get()
        assert len(BOOKED_CARS.get(user_id)) == 1
