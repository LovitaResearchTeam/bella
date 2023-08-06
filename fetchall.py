from utils import fetch_data
import asyncio

async def main():
    await fetch_data()

if __name__ == "__main__":
    asyncio.run(main())