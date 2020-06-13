import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urljoin

from loguru import logger
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page, Response
from pyppeteer_stealth import stealth

from tiktokpy.utils.client import block_resources_and_sentry


class Client:
    def __init__(self):
        self.base_url = "https://www.tiktok.com/"

    async def init_browser(self):
        params = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ],
        }

        self.browser: Browser = await launch(**params)
        logger.debug(f"🎉 Browser launched. Options: {params}")

    async def new_page(self, block_media: bool = True) -> Page:
        page: Page = await self.browser.newPage()
        await stealth(page)

        if block_media:
            await page.setRequestInterception(True)
            page.on(
                "request",
                lambda req: asyncio.create_task(
                    block_resources_and_sentry(req, ["media", "image", "font"]),
                ),
            )

        return page

    async def goto(
        self, url: str, page: Page, query_params: Optional[dict] = None, *args, **kwargs,
    ) -> Response:
        full_url = urljoin(self.base_url, url)

        if query_params:
            query_params = urlencode(query=query_params)
            full_url = f"{full_url}?{query_params}"

        return await page.goto(full_url, *args, **kwargs)

    async def screenshot(self, path: str, page: Page):
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot({"path": path})

    @classmethod
    async def create(cls):
        self = Client()
        await self.init_browser()

        return self
