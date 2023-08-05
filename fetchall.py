from utils import fetch_all
import asyncio

async def main():
    await fetch_all()

if __name__ == "__main__":
    asyncio.run(main())