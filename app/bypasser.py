"""Engine Playwright xử lý chuyển hướng thông thường của Link4m.
Không dùng stealth, không giải CAPTCHA và không vượt cơ chế xác minh truy cập.
"""
from __future__ import annotations
import asyncio
import logging
import time
from urllib.parse import urlsplit
from playwright.async_api import async_playwright, Error as PlaywrightError
from app.config import BYPASS_TIMEOUT_SECONDS, MAX_STEPS, NAVIGATION_TIMEOUT_MS
from app.security import is_public_http_url

logger = logging.getLogger(__name__)

class LinkBypasser:
    async def bypass(self, url: str) -> dict:
        started = time.perf_counter()
        browser = None
        context = None
        try:
            logger.info("Bắt đầu xử lý Link4m")
            async with asyncio.timeout(BYPASS_TIMEOUT_SECONDS):
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
                    )
                    context = await browser.new_context(
                        viewport={"width": 1366, "height": 768},
                        locale="vi-VN",
                        accept_downloads=False,
                    )

                    # Kiểm tra mọi request phát sinh trong browser, kể cả redirect.
                    async def guard_route(route):
                        if await is_public_http_url(route.request.url):
                            await route.continue_()
                        else:
                            await route.abort("blockedbyclient")

                    await context.route("**/*", guard_route)
                    page = await context.new_page()
                    page.set_default_timeout(5_000)
                    await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)

                    for _ in range(MAX_STEPS):
                        current = page.url
                        parsed = urlsplit(current)
                        host = (parsed.hostname or "").lower().rstrip(".")
                        if parsed.scheme in {"http", "https"} and host not in {"link4m.net", "www.link4m.net"}:
                            if await is_public_http_url(current):
                                elapsed = round(time.perf_counter() - started, 2)
                                logger.info("Hoàn tất xử lý Link4m sau %.2fs", elapsed)
                                return self._result(True, current, elapsed, None)
                            return self._result(False, None, time.perf_counter() - started,
                                                "Đích chuyển hướng không an toàn.", "UNSAFE_DESTINATION")

                        # Chỉ click các nút điều hướng phổ biến; không xử lý CAPTCHA/anti-bot.
                        candidates = page.locator("button, input[type='submit'], a")
                        count = min(await candidates.count(), 30)
                        clicked = False
                        for index in range(count):
                            element = candidates.nth(index)
                            try:
                                if not await element.is_visible() or not await element.is_enabled():
                                    continue
                                label = (await element.inner_text(timeout=700)).strip().lower()
                                value = (await element.get_attribute("value") or "").strip().lower()
                                text = label or value
                                if any(word in text for word in ("tiếp tục", "continue", "get link", "lấy link")):
                                    await element.click(timeout=3_000)
                                    clicked = True
                                    try:
                                        await page.wait_for_load_state("domcontentloaded", timeout=8_000)
                                    except PlaywrightError:
                                        pass
                                    break
                            except PlaywrightError:
                                continue
                        if not clicked:
                            break

                    elapsed = round(time.perf_counter() - started, 2)
                    return self._result(False, None, elapsed,
                                        "Không tìm thấy URL đích. Trang có thể yêu cầu thao tác hoặc xác minh thủ công.",
                                        "NO_DESTINATION")
        except TimeoutError:
            elapsed = round(time.perf_counter() - started, 2)
            return self._result(False, None, elapsed, "Đã vượt quá thời gian xử lý tối đa.", "TIMEOUT")
        except PlaywrightError as exc:
            elapsed = round(time.perf_counter() - started, 2)
            logger.warning("Lỗi Playwright: %s", exc)
            return self._result(False, None, elapsed, "Không thể tải hoặc xử lý trang Link4m.", "BROWSER_ERROR")
        except Exception:
            elapsed = round(time.perf_counter() - started, 2)
            logger.exception("Lỗi không mong đợi trong bypass")
            return self._result(False, None, elapsed, "Đã xảy ra lỗi nội bộ khi xử lý link.", "INTERNAL_ERROR")
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    logger.debug("Không thể đóng browser context", exc_info=True)
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    logger.debug("Không thể đóng browser", exc_info=True)

    @staticmethod
    def _result(success: bool, destination: str | None, elapsed: float,
                message: str | None, code: str | None = None) -> dict:
        error = None if success else {"code": code or "ERROR", "message": message or "Có lỗi xảy ra."}
        return {"success": success, "bypassed_url": destination,
                "time_taken": round(elapsed, 2), "error": error}
