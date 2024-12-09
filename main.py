import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import platform
import sys


class HttpError(Exception):
    pass


class CurrencyFetcher:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"

    async def fetch_data_fom_api(self, date):
        url = f"{self.BASE_URL}?date={date}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        raise HttpError(f"Error status: {resp.status} for {url}")
            except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
                raise HttpError(f"Connection error: {url}", str(err))


class CurrencyFilter:
    @staticmethod
    def filter_data_fom_api(data, currencies):
        if not data or "exchangeRate" not in data:
            return None

        filtered_data = {}
        for item in data["exchangeRate"]:
            if item.get("currency") in currencies:
                filtered_data[item["currency"]] = {
                    "sale": item.get("saleRateNB"),
                    "purchase": item.get("purchaseRateNB")
                }
        return filtered_data


class CurrencyApp:

    def __init__(self, currency_fetcher, currency_filter):
        self.fetcher = currency_fetcher
        self.processor = currency_filter

    async def get_data_for_days(self, days, currencies):
        if days < 1 or days > 10:
            raise ValueError("Enter days from 1 to 10.")


        results = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            raw_data = await self.fetcher.fetch_data_fom_api(date)
            filtered_data = self.processor.filter_data_fom_api(raw_data, currencies)
            if filtered_data:
                results.append({date: filtered_data})
        return results


async def main(days):
    currency_fetcher = CurrencyFetcher()
    currency_filter = CurrencyFilter()
    app = CurrencyApp(currency_fetcher, currency_filter)

    try:
        rates = await app.get_data_for_days(days, ["EUR", "USD"])
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(rates, f, ensure_ascii=False, indent=4)
        print(f"Data saved to data.json")
        print(rates)
    except HttpError as err:
        print(f"HTTP error: {err}")
    except ValueError as err:
        print(f"Value error: {err}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Enter days from 1 to 10")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("Enter days from 1 to 10.")
        sys.exit(1)

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(days))
