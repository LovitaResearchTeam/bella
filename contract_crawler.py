import asyncio
import requests
import argparse
from pyinjective.async_client import AsyncClient
from pyinjective.client.model.pagination import PaginationOption
from pyinjective.composer import Composer
from pyinjective.core.network import Network
import base64
import json
import pandas as pd

def decode_base64_to_json(base64_string):
    """
    Decode a base64-encoded string and convert it to a JSON object.

    Args:
        base64_string (str): The base64-encoded string to decode.

    Returns:
        dict: The decoded JSON object.
    """
    # Decode the base64 string to bytes
    decoded_bytes = base64.b64decode(base64_string)
    
    # Convert bytes to string
    decoded_str = decoded_bytes.decode('utf-8')
    
    # Parse the string into a JSON object
    json_data = json.loads(decoded_str)
    
    return json_data

async def get_meta(minter_address: str, contract_address: str) -> list:
    """
    Fetch metadata URIs associated with a specific minter and contract address.

    Args:
        minter_address (str): The minter address to fetch transactions from.
        contract_address (str): The contract address to filter transactions.

    Returns:
        list: A list of metadata URIs.
    """
    page_size = 5  # Number of transactions to fetch per request
    network = Network.mainnet()  # Define the network as mainnet
    client = AsyncClient(network, insecure=False)  # Initialize the async client
    composer = Composer(network=network.string())  # Initialize the composer with the network string

    # Set pagination options with a limit of `page_size`
    pagination = PaginationOption(limit=page_size)
    
    execute_contract_messages = []

    # Initial request to fetch transactions
    txs = await client.fetch_account_txs(address=minter_address, pagination=pagination)
    messages = []

    # Decode and collect messages from transactions
    for tx in txs['data']:
        msgs = decode_base64_to_json(tx['messages'])
        messages.extend(msgs)

    # Filter and extract contract execution messages
    execute_contract_messages.extend(
        [
            json.loads(msg['value']['msg'])
            for msg in messages
            if msg['type'] == "/injective.wasmx.v1.MsgExecuteContractCompat"
            and msg['value']['contract'] == contract_address
        ]
    )

    skip = page_size

    # Paginate through transactions if more are available
    while len(txs['data']) == page_size:
        pagination = PaginationOption(limit=page_size, skip=skip)
        skip += page_size
        txs = await client.fetch_account_txs(address=minter_address, pagination=pagination)
        messages = []
        for tx in txs['data']:
            msgs = decode_base64_to_json(tx['messages'])
            messages.extend(msgs)

        execute_contract_messages.extend(
            [
                json.loads(msg['value']['msg'])
                for msg in messages
                if msg['type'] == "/injective.wasmx.v1.MsgExecuteContractCompat"
                and msg['value']['contract'] == contract_address
            ]
        )

    # Extract metadata URIs from the filtered messages
    metadata_uri = [m['mint']['metadata_uri'] for m in execute_contract_messages if 'mint' in m]
    
    return metadata_uri

def get_ipfs_from_address(ipfs_address: str) -> str:
    """
    Convert an IPFS URI to a standard HTTP URL.

    Args:
        ipfs_address (str): The IPFS address (e.g., ipfs://...).

    Returns:
        str: The corresponding HTTP URL (e.g., https://ipfs.io/ipfs/...).
    """
    return ipfs_address.replace("ipfs://", "https://ipfs.io/ipfs/")

async def get_all_metadatas(minter_address: str, contract_address: str):
    """
    Fetch all metadata associated with a specific minter and contract address,
    and save the metadata to a CSV file.

    Args:
        minter_address (str): The minter address to fetch transactions from.
        contract_address (str): The contract address to filter transactions.

    Returns:
        list: A list of metadata JSON objects.
    """
    # Fetch the list of metadata URIs
    mint_metadata_uris = await get_meta(minter_address, contract_address)
    
    # Convert IPFS URIs to HTTP URLs
    mint_metadata_urls = [get_ipfs_from_address(uri) for uri in mint_metadata_uris]

    async def get_data(url: str):
        """
        Fetch data from a URL asynchronously.

        Args:
            url (str): The URL to fetch data from.

        Returns:
            dict: The JSON response from the URL.
        """
        loop = asyncio.get_event_loop()

        def get_response():
            response = requests.get(url)
            return response

        response_future = loop.run_in_executor(None, get_response)
        response = await response_future
        return response.json()

    metadatas = []
    batch_size = 40  # Number of URLs to process in each batch

    # Process URLs in batches to avoid overwhelming the server
    for i in range(0, len(mint_metadata_urls), batch_size):
        batch_urls = mint_metadata_urls[i:i + batch_size]
        coroutines = [get_data(url) for url in batch_urls]
        tasks = [asyncio.create_task(coro) for coro in coroutines]
        done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        for task in done:
            metadatas.append(await task)

        # Sleep for 1 second between batches to prevent rate limiting
        if i + batch_size < len(mint_metadata_urls):
            await asyncio.sleep(1)
    
    # Save the collected metadata to a CSV file
    df = pd.DataFrame(metadatas)
    df.to_csv('metadatas.csv', index=False)

    return metadatas

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Fetch metadata for a given minter and contract address.")
    parser.add_argument("minter_address", type=str, help="The minter address.")
    parser.add_argument("contract_address", type=str, help="The contract address.")
    args = parser.parse_args()

    # Run the main function with the provided addresses
    asyncio.run(get_all_metadatas(args.minter_address, args.contract_address))