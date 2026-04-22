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
    Message,
)
from PIL import Image

from memlish_reborn.config import (
    BOT_TOKEN,
    FILE_IDS_PATH,
    STAGING_CHAT_ID,
    TOP_K,
)
from memlish_reborn.draw import add_text
from memlish_reborn.file_id_cache import FileIdCache
from memlish_reborn.index import MemeIndex, Match, get_index

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
    cache = _get_cache()

    matches = await asyncio.to_thread(index.search, query, TOP_K)
    if not matches:
        await inline.answer(results=[], cache_time=5)
        return

    staging_chat_id = _staging_chat_id()
    if staging_chat_id is None:
        log.error("MEMLISH_STAGING_CHAT_ID not configured — cannot upload rendered memes")
        await inline.answer(results=[], cache_time=5)
        return

    file_ids = await asyncio.gather(
        *(
            _get_or_upload_file_id(bot, cache, staging_chat_id, m, query)
            for m in matches
        )
    )

    results = [
        InlineQueryResultCachedPhoto(
            id=str(uuid.uuid4()),
            photo_file_id=fid,
            title=m.name,
        )
        for m, fid in zip(matches, file_ids)
        if fid is not None
    ]
    await inline.answer(results=results, cache_time=60, is_personal=False)


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


def _get_cache() -> FileIdCache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = FileIdCache(FILE_IDS_PATH)
    return _cache_singleton


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def _warmup() -> None:
    # Force index + model load on startup so the first user query is fast.
    log.info("warming up index + CLIP model")
    await asyncio.to_thread(get_index)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var is required")
    bot = Bot(token=BOT_TOKEN)
    dp = build_dispatcher()
    dp.startup.register(_warmup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
