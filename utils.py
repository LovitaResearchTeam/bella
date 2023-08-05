import asyncio
from math import ceil
import requests
from consts import CONTRACT_ADDRESS


def get_ipfs_from_address(ipfs_address: str) -> str:
    return ipfs_address.replace("ipfs://", "https://ipfs.io/ipfs/")


async def get_contract_txs_with_skip(skip: int=0):
    url = "https://products.exchange.grpc-web.injective.network/api/explorer/v1/contractTxs/" + CONTRACT_ADDRESS
    params = {"skip": skip} if skip else {}
    loop = asyncio.get_event_loop()
    def get_response():
        response = requests.get(url, params=params)
        return response
    response_future = loop.run_in_executor(None, get_response)
    response = await response_future
    return response.json()


async def get_all_contract_txs(pages_no: int=None):
    first_page = await get_contract_txs_with_skip()
    total = first_page['paging']['total']
    number_of_pages = ceil(total/100) - 1
    if pages_no is None:
        pages_no = number_of_pages
    pages = [first_page]
    for i in range(number_of_pages - 1, number_of_pages - pages_no - 1, -1):
        pages.append(await get_contract_txs_with_skip(100*i))
    return pages


async def get_all_contract_txs2(pages_no: int=None):
    first_page = await get_contract_txs_with_skip()
    total = first_page['paging']['total']
    number_of_pages = ceil(total/100) - 1
    if pages_no is None:
        pages_no = number_of_pages
    pages = []

    coroutines = [get_contract_txs_with_skip(100*i) for i in range(number_of_pages - 1, number_of_pages - pages_no - 1, -1)]
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    for task in done:
        pages.append(await task)
    pages.append(first_page)
    return pages


async def get_all_contract_txs3(pages_no: int=None):
    first_page = await get_contract_txs_with_skip()
    total = first_page['paging']['total']
    number_of_pages = ceil(total/100) - 1
    if pages_no is None:
        pages_no = number_of_pages
    coroutines = [get_contract_txs_with_skip(100*i) for i in range(number_of_pages - 1, number_of_pages - pages_no - 1, -1)]
    pages = [await coro async for coro in coroutines]
    pages.append(first_page)
    return pages
