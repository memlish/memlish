from __future__ import annotations

import asyncio
import io
import logging
import uuid
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    ChosenInlineResult,
    InlineQuery,
    InlineQueryResultCachedPhoto,
    InlineQueryResultPhoto,
    Message,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from PIL import Image

from memlish_reborn.config import (
    BOT_TOKEN,
    DELIVERY_MODE,
    FILE_IDS_PATH,
    PUBLIC_BASE_URL,
    RENDERED_DIR,
    STAGING_CHAT_ID,
    TOP_K,
    USE_POLLING,
    WEBAPP_HOST,
    WEBAPP_PORT,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
    WEBHOOK_URL,
)
from memlish_reborn.draw import add_text
from memlish_reborn.file_id_cache import FileIdCache
from memlish_reborn.index import MemeIndex, Match, get_index
from memlish_reborn.rendered_cache import RenderedCache

log = logging.getLogger(__name__)

router = Router()

WELCOME = (
    "Hey! I make memes from your text.\n\n"
    "Type @{bot_username} <your text> in any chat — I'll return ranked meme templates "
    "with your text drawn on them. Tap one to send."
)


def _render_meme(match: Match, text: str) -> bytes:
    img = Image.open(match.path)
    rendered = add_text(img, text)
    buf = io.BytesIO()
    rendered.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def _get_or_upload_file_id(
    bot: Bot,
    cache: FileIdCache,
    staging_chat_id: int,
    match: Match,
    text: str,
) -> str | None:
    cached = cache.get(match.filename, text)
    if cached is not None:
        return cached
    try:
        png_bytes = await asyncio.to_thread(_render_meme, match, text)
        photo = BufferedInputFile(png_bytes, filename=f"{match.filename}.jpg")
        message = await bot.send_photo(chat_id=staging_chat_id, photo=photo)
        file_id = message.photo[-1].file_id
        cache.set(match.filename, text, file_id)
        return file_id
    except Exception as e:
        log.warning("upload failed for %s: %s", match.filename, e)
        return None


@router.message(Command("start", "help"))
async def cmd_start(message: Message, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(WELCOME.format(bot_username=me.username or "memlish_bot"))


@router.inline_query()
async def handle_inline(inline: InlineQuery, bot: Bot) -> None:
    query = (inline.query or "").strip()
    if not query:
        await inline.answer(results=[], cache_time=1, is_personal=False)
        return

    index = get_index()
    matches = await asyncio.to_thread(index.search, query, TOP_K)
    if not matches:
        await inline.answer(results=[], cache_time=5)
        return

    if DELIVERY_MODE == "url":
        results = await _build_url_results(matches, query)
    else:
        results = await _build_file_id_results(bot, matches, query)

    await inline.answer(results=results, cache_time=60, is_personal=False)


async def _build_file_id_results(
    bot: Bot, matches: list[Match], query: str
) -> list[InlineQueryResultCachedPhoto]:
    staging_chat_id = _staging_chat_id()
    if staging_chat_id is None:
        log.error("MEMLISH_STAGING_CHAT_ID not configured — cannot upload rendered memes")
        return []

    cache = _get_cache()
    file_ids = await asyncio.gather(
        *(
            _get_or_upload_file_id(bot, cache, staging_chat_id, m, query)
            for m in matches
        )
    )
    return [
        InlineQueryResultCachedPhoto(
            id=str(uuid.uuid4()),
            photo_file_id=fid,
            title=m.name,
        )
        for m, fid in zip(matches, file_ids)
        if fid is not None
    ]


async def _build_url_results(
    matches: list[Match], query: str
) -> list[InlineQueryResultPhoto]:
    if not PUBLIC_BASE_URL:
        log.error("MEMLISH_PUBLIC_BASE_URL/WEBHOOK_HOST not set — cannot serve URL results")
        return []

    rendered = _get_rendered_cache()

    async def _ensure(m: Match) -> tuple[Match, str] | None:
        try:
            await asyncio.to_thread(
                rendered.get_or_render, m.filename, query, lambda: _render_meme(m, query)
            )
            return m, rendered.key(m.filename, query)
        except Exception as e:
            log.warning("render failed for %s: %s", m.filename, e)
            return None

    pairs = await asyncio.gather(*(_ensure(m) for m in matches))

    results: list[InlineQueryResultPhoto] = []
    for pair in pairs:
        if pair is None:
            continue
        m, key = pair
        url = f"{PUBLIC_BASE_URL}/img/{key}.jpg"
        results.append(
            InlineQueryResultPhoto(
                id=str(uuid.uuid4()),
                photo_url=url,
                thumbnail_url=url,
                title=m.name,
            )
        )
    return results


@router.chosen_inline_result()
async def handle_chosen(result: ChosenInlineResult) -> None:
    log.info(
        "chosen_inline query=%r result_id=%s user=%s",
        result.query,
        result.result_id,
        result.from_user.id if result.from_user else None,
    )


def _staging_chat_id() -> int | None:
    if not STAGING_CHAT_ID:
        return None
    try:
        return int(STAGING_CHAT_ID)
    except ValueError:
        return None


_cache_singleton: FileIdCache | None = None
_rendered_singleton: RenderedCache | None = None


def _get_cache() -> FileIdCache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = FileIdCache(FILE_IDS_PATH)
    return _cache_singleton


def _get_rendered_cache() -> RenderedCache:
    global _rendered_singleton
    if _rendered_singleton is None:
        _rendered_singleton = RenderedCache(RENDERED_DIR)
    return _rendered_singleton


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def _warmup() -> None:
    # Force index + model load on startup so the first user query is fast.
    log.info("warming up index + CLIP model")
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(get_index)
    if DELIVERY_MODE == "url":
        _get_rendered_cache()


async def _serve_image(request: web.Request) -> web.StreamResponse:
    name = request.match_info["name"]
    if not name.endswith(".jpg") or "/" in name or ".." in name:
        raise web.HTTPNotFound()
    path = RENDERED_DIR / name
    if not path.is_file():
        raise web.HTTPNotFound()
    return web.FileResponse(
        path,
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )


async def _set_webhook(bot: Bot) -> None:
    if not WEBHOOK_URL:
        raise SystemExit("WEBHOOK_HOST env var is required when USE_POLLING is false")
    log.info("setting webhook to %s", WEBHOOK_URL)
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )


async def main_polling() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = build_dispatcher()
    dp.startup.register(_warmup)
    await dp.start_polling(bot)


def run_webhook() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = build_dispatcher()
    dp.startup.register(_warmup)

    async def _on_startup(**_kwargs) -> None:
        await _set_webhook(bot)

    dp.startup.register(_on_startup)

    app = web.Application()
    app.router.add_get("/img/{name}", _serve_image)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET or None,
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    log.info("starting aiohttp on %s:%s (path=%s)", WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_PATH)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var is required")
    if DELIVERY_MODE not in ("file_id", "url"):
        raise SystemExit(f"MEMLISH_DELIVERY must be 'file_id' or 'url', got {DELIVERY_MODE!r}")
    if DELIVERY_MODE == "file_id" and not STAGING_CHAT_ID:
        raise SystemExit("MEMLISH_STAGING_CHAT_ID is required when MEMLISH_DELIVERY=file_id")
    if DELIVERY_MODE == "url" and not PUBLIC_BASE_URL:
        raise SystemExit(
            "MEMLISH_PUBLIC_BASE_URL (or WEBHOOK_HOST) is required when MEMLISH_DELIVERY=url"
        )
    if USE_POLLING:
        asyncio.run(main_polling())
    else:
        run_webhook()


if __name__ == "__main__":
    main()
