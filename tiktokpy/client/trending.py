import asyncio
from typing import List

from loguru import logger
from tqdm import tqdm

from tiktokpy.client import Client
from tiktokpy.utils.client import catch_response_and_store


class Trending:
    def __init__(self, client: Client):
        self.client = client

    async def feed(self, amount: int, lang: str = "en"):
        page = await self.client.new_page()

        logger.debug('📨 Request "Trending" page')

        result: List[dict] = []

        pbar = tqdm(total=amount, desc=f"📈 Getting trending {lang.upper()}")

        page.on(
            "response", lambda res: asyncio.create_task(catch_response_and_store(res, result)),
        )
        _ = await self.client.goto(
            "/trending", params={"lang": lang}, page=page, options={"waitUntil": "networkidle0"},
        )
        logger.debug('📭 Got response from "Trending" page')

        while len(result) < amount:

            logger.debug("🖱 Trying to scroll to last video item")
            await page.evaluate(
                """
                document.querySelector('.video-feed-item:last-child')
                    .scrollIntoView();
            """,
            )
            await page.waitFor(1_000)

            elements = await page.JJ(".video-feed-item")
            logger.debug(f"🔎 Found {len(elements)} items for clear")

            pbar.n = min(len(result), amount)
            pbar.refresh()

            if len(elements) < 500:
                logger.debug("🔻 Too less for clearing page")
                continue

            await page.JJeval(
                ".video-feed-item:not(:last-child)",
                pageFunction="(elements) => elements.forEach(el => el.remove())",
            )
            logger.debug(f"🎉 Cleaned {len(elements) - 1} items from page")
            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result[:amount]
