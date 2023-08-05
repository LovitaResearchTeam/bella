from metadatautils import fetch_medias_from_metadata
import asyncio

async def main():
    await fetch_medias_from_metadata()

if __name__ == "__main__":
    asyncio.run(main())