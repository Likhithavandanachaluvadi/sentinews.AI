import os
import httpx

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

class FinnhubService:

    @staticmethod
    async def fetch_peers(symbol: str):
        url = (
            f"https://finnhub.io/api/v1/stock/peers"
            f"?symbol={symbol}&token={FINNHUB_API_KEY}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()

            return []
if __name__ == "__main__":
    import asyncio

    async def test():
        peers = await FinnhubService.fetch_peers("AAPL")
        print("PEERS =", peers)

    asyncio.run(test())