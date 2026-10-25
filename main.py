import os
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from playwright.async_api import async_playwright

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود في Render Environment")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "🤖 بوت PlayStation يعمل على Render.\n\n"
        "الأوامر:\n"
        "/start - تشغيل البوت\n"
        "/browser - اختبار المتصفح\n"
        "/status - حالة البوت"
    )


async def browser_test(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "⏳ أختبر تشغيل Chromium..."
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True
            )

            page = await browser.new_page()

            await page.goto(
                "https://www.playstation.com/",
                wait_until="domcontentloaded",
                timeout=45000,
            )

            title = await page.title()

            await browser.close()

        await update.effective_message.reply_text(
            "✅ المتصفح يعمل!\n"
            f"عنوان الصفحة: {title}"
        )

    except Exception as exc:
        logging.exception("Browser test failed")

        await update.effective_message.reply_text(
            "❌ تعذر تشغيل المتصفح.\n"
            f"الخطأ: {type(exc).__name__}"
        )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "✅ البوت متصل ويستقبل الأوامر."
    )


async def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("browser", browser_test)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logging.info("Telegram bot started")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
