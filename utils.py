import asyncio
import json
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
    pages = []

    coroutines = [get_contract_txs_with_skip(100*i) for i in range(number_of_pages, number_of_pages - pages_no, -1)]
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    for task in done:
        pages.append(await task)
    pages.append(first_page)
    return pages


async def get_all_metadatas():
    pages = await get_all_contract_txs()
    mints = []
    for page in pages:
        for d in page['data']:
            for m in d['messages']:
                ms = m['value']['msg']
                try:
                    ms.keys()
                except:
                    ms = json.loads(ms)
                if 'mint' in ms.keys():
                    mints.append(ms)
    mint_metadata_uris = [m['mints']['metadata_uri'] for m in mints]
    mint_metadata_urls = [get_ipfs_from_address(uri) for uri in mint_metadata_uris]
    async def get_data(url: str):
        loop = asyncio.get_event_loop()
        def get_response():
            response = requests.get(url)
            return response
        response_future = loop.run_in_executor(None, get_response)
        response = await response_future
        return response.json()
    coroutines = [get_data(url) for url in mint_metadata_urls]
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    metadatas = []
    for task in done:
        metadatas.append(await task)
    return metadatas
