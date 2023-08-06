import asyncio
import os
import re
import json
from math import ceil
import requests
from consts import CONTRACT_ADDRESS
import shutil
import pandas as pd


def get_ipfs_from_address(ipfs_address: str) -> str:
    return ipfs_address.replace("ipfs://", "https://ipfs.io/ipfs/")


async def retreive_contract_txs_with_skip(skip: int=0):
    url = "https://products.exchange.grpc-web.injective.network/api/explorer/v1/contractTxs/" + CONTRACT_ADDRESS
    params = {"skip": skip} if skip else {}
    loop = asyncio.get_event_loop()
    def get_response():
        response = requests.get(url, params=params)
        return response
    response_future = loop.run_in_executor(None, get_response)
    response = await response_future
    return response.json()


async def retreive_all_contract_txs(pages_no: int=None):
    first_page = await retreive_contract_txs_with_skip()
    total = first_page['paging']['total']
    number_of_pages = ceil(total/100) - 1
    if pages_no is None:
        pages_no = number_of_pages
    pages = []

    coroutines = [retreive_contract_txs_with_skip(100*i) for i in range(number_of_pages, number_of_pages - pages_no, -1)]
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    for task in done:
        pages.append(await task)
    pages.append(first_page)
    return pages


async def get_all_metadatas():
    pages = await retreive_all_contract_txs()
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
    mint_metadata_uris = [m['mint']['metadata_uri'] for m in mints]
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


async def fetch_metadats():
    metadata_dict = {}
    metadatas = await get_all_metadatas()
    pattern = r'#(\d+)'
    for metadata in metadatas:
        match = re.search(pattern, metadata['title'])
        if match:
            number = match.group(1)
        else:
            print(metadata)
            print("number can't be derived")
        metadata_dict[number] = {
            'title': metadata['title'],
            'description': metadata['description'],
            'rare_parameteres': {
                'background': metadata['background'],
                'face': metadata['face'],
                'body': metadata['body'],
                'weapon': metadata['weapon'],
                'head': metadata['head'],
                'necklace': metadata['necklace'],
            },
            'media': get_ipfs_from_address(metadata['media']),
            'tags': metadata['tags']
        }
    with open("metadata.json", 'w') as f:
        json.dump(metadata_dict, f)


async def download_media(url: str, number: int):
    loop = asyncio.get_event_loop()
    def get_media_from_address():
        response = requests.get(url, stream=True)
        with open(f'media/#{number}.jpg', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return
    download_future = loop.run_in_executor(None, get_media_from_address)
    await download_future
    return


async def fetch_medias_from_metadata():
    if 'media' not in os.listdir():
        os.mkdir('media')
    with open("metadata.json") as f:
        metadata_dict = json.load(f)
        coroutines = [download_media(metadata['media'], number) for number, metadata in metadata_dict.items()]
        tasks = [asyncio.create_task(coro) for coro in coroutines]
        done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        for task in done:
            await task


async def fetch_data():
    await fetch_metadats()
    await fetch_medias_from_metadata()


def fetch_rarities():
    with open("metadata.json") as f:
        metadata_dict = json.load(f)
    rare_cols = ['background', 'face', 'body', 'weapon', 'head', 'necklace']
    cols = ['number'] + rare_cols
    metadata_df = pd.DataFrame([[k, *v['rare_parameteres'].values()] for k, v in metadata_dict.items()], columns=cols)

    rarity_df = pd.DataFrame()
    rarity_df['number'] = metadata_df['number']
    for col in rare_cols:
        rarity_df[col] = metadata_df[col].map(metadata_df[col].value_counts(normalize=True)) * 100
        rarity_df[f"rank_{col}"] = rarity_df[col].rank(method='min')
    rarity_df = rarity_df.assign(total=lambda x: sum(x[col] for col in rare_cols)/len(rare_cols))
    rarity_df['rank_total'] = rarity_df['total'].rank(method='min')
    rarity_df.to_csv("rarity.csv", index=False)