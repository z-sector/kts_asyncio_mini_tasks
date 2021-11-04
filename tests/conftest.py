import asyncio

import pytest

from app.car_rent import clear_booked_cars


def send_ok_result():
    result_url = urllib.parse.urlparse(os.environ["RESULT_URL"])
    conn = http.client.HTTPSConnection(result_url.netloc)
    payload = ""
    headers = {
        "X-Progress-Token": os.environ["PROGRESS_TOKEN"],
    }
    conn.request("POST", "/api/v2.chunk.set_mercury_task_result", payload, headers)
    res = conn.getresponse()

    print('\n')
    if res.status == 200:
        print("=== success result has been saved successfully ===")
    else:
        data = res.read()
        print(data.decode("utf-8"))


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        try:
            send_ok_result()
        except:
            pass


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clear_globar_var():
    clear_booked_cars()


@pytest.fixture
def user_id() -> int:
    return 1
