import asyncio
import os
import re
import json
from math import ceil
import requests
from consts import CONTRACT_ADDRESS, RARE_COLS
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
        else:
            metadata_dict[metadata['title']] = {
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


async def download_media(url: str, name: str):
    loop = asyncio.get_event_loop()
    def get_media_from_address():
        response = requests.get(url, stream=True)
        with open(f'media/#{name}.jpg', 'wb') as out_file:
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
        coroutines = [download_media(metadata['media'], name) for name, metadata in metadata_dict.items()]
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
    
    cols = ['number'] + RARE_COLS
    metadata_df = pd.DataFrame([[k, *v['rare_parameteres'].values()] for k, v in metadata_dict.items()], columns=cols)

    rarity_df = pd.DataFrame()
    rarity_df['number'] = metadata_df['number']
    for col in RARE_COLS:
        rarity_df[col] = metadata_df[col]
        rarity_df[f"rarity_{col}"] = metadata_df[col].map(metadata_df[col].value_counts(normalize=True)) * 100
        rarity_df[f"rank_{col}"] = rarity_df[f"rarity_{col}"].rank(method='min')
    rarity_df = rarity_df.assign(total=lambda x: sum(x[f'rarity_{col}'] for col in RARE_COLS)/len(RARE_COLS))
    rarity_df['rank_total'] = rarity_df['total'].rank(method='min')
    rarity_df.to_csv("rarity.csv", index=False)


def get_collection_data():
    url = 'https://injective.talis.art/api/graphql'
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    data = {
        'operationName': 'GetCollectionStats',
        'variables': {
            'input': {
                'id': '648de728463a4965932b2bb0',
                'env': 'mainnet',
                'chain': 'injective'
            }
        },
        'query': 'query GetCollectionStats($input: CollectionStatsInput!) {\n  collectionStats(input: $input) {\n    ownerCount\n    tokenCount\n    floorPrice\n    ceilingPrice\n    volumeInLast7Days\n    doesCurrentUserOwnAllTokens\n    __typename\n  }\n}'
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()['data']['collectionStats']



def get_getfamilies():
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    json_data = {
        'operationName': 'GetFamilies',
        'variables': {
            'input': {
                'networks': None,
                'filter': {
                    'isGeneric': {
                        'eq': False,
                    },
                    'isHidden': {
                        'eq': False,
                    },
                    'isBlocked': {
                        'eq': False,
                    },
                },
            },
        },
        'query': 'query GetFamilies($input: FamiliesInput!) {\n  families(input: $input) {\n    families {\n      id\n      collection_id\n      name\n      artist {\n        id\n        profilePic\n        username\n        isArtist\n        wallet {\n          injAddress\n          __typename\n        }\n        __typename\n      }\n      isGeneric\n      maxSupply\n      miniaturePicture\n      symbol\n      coverPicture\n      mediaType\n      description\n      traits {\n        key\n        values\n        __typename\n      }\n      traits2 {\n        key\n        values {\n          value\n          ratio\n          count\n          __typename\n        }\n        __typename\n      }\n      hasBeenWhitelisted\n      env\n      chain\n      previews {\n        id\n        token_id\n        media\n        mediaThumbnail\n        title\n        mediaType\n        __typename\n      }\n      miniatureDimensions {\n        width\n        height\n        __typename\n      }\n      coverPictureDimensions {\n        width\n        height\n        __typename\n      }\n      tokenCount\n      candy {\n        id\n        name\n        initiator {\n          id\n          __typename\n        }\n        contract\n        price\n        currency\n        limitByWallet\n        limitByTransaction\n        startingDate\n        endingDate\n        reserveTokens\n        randomSeed\n        randomNumberPicked\n        randomSignature\n        lastRandomNumber\n        createdAt\n        updatedAt\n        withdrawnTokens\n        isSoldOut\n        phases {\n          id\n          name\n          startingDate\n          endingDate\n          privacy\n          mintLimit\n          duration\n          __typename\n        }\n        __typename\n      }\n      isHidden\n      isBlocked\n      isPrintEnabled\n      shouldDisplayRarity\n      isBadge\n      badgePicture\n      badgeUri\n      badgeType\n      createdAt\n      updatedAt\n      volumeInLast7Days\n      floorPrice\n      ownerCount\n      totalVolume\n      __typename\n    }\n    count\n    __typename\n  }\n}',
    }

    response = requests.post('https://injective.talis.art/api/graphql', headers=headers, json=json_data)

    print(response.content)
    return response.json()