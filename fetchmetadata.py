from metadatautils import fetch_metadats
import asyncio

async def main():
    await fetch_metadats()

if __name__ == "__main__":
    asyncio.run(main())