import os
import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest
from playwright.async_api import async_playwright

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()


class Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def run_ping():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), Ping)
    server.serve_forever()


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "🤖 بوت PlayStation يعمل!\n\n"
        "الأوامر المتاحة:\n"
        "/start - القائمة الرئيسية\n"
        "/status - حالة البوت\n"
        "/browser - اختبار المتصفح"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "✅ البوت يعمل ويستقبل الأوامر."
    )


async def browser_test(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = await update.effective_message.reply_text(
        "⏳ جاري اختبار المتصفح..."
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                page = await browser.new_page()
                await page.goto(
                    "https://www.playstation.com/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                title = await page.title()
            finally:
                await browser.close()

        await message.edit_text(
            f"✅ المتصفح يعمل!\nعنوان الصفحة: {title}"
        )

    except Exception as exc:
        logging.exception("Browser test failed")
        await message.edit_text(
            f"❌ فشل اختبار المتصفح: {type(exc).__name__}"
        )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    error = context.error

    if error:
        logging.error(
            "Telegram handler error: %s",
            type(error).__name__,
            exc_info=(
                type(error),
                error,
                error.__traceback__,
            ),
        )


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في إعدادات Render Environment"
        )

    threading.Thread(
        target=run_ping,
        daemon=True,
    ).start()

    normal_request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30,
        read_timeout=40,
        write_timeout=30,
        pool_timeout=30,
    )

    polling_request = HTTPXRequest(
        connection_pool_size=2,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=30,
        pool_timeout=30,
    )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(normal_request)
        .get_updates_request(polling_request)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("browser", browser_test))
    app.add_error_handler(error_handler)

    logging.info("Starting Telegram bot...")

    await app.initialize()
    await app.start()

    try:
        await app.updater.start_polling(
            poll_interval=1.0,
            timeout=20,
            drop_pending_updates=False,
        )

        logging.info("Telegram polling started")

        await asyncio.Event().wait()

    finally:
        if app.updater.running:
            await app.updater.stop()

        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
