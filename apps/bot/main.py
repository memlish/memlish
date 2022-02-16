import sys
sys.path.append('/app')  # noqa

import logging
import os
from uuid import uuid4

from aiogram import Bot, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.webhook import SendMessage,  AnswerInlineQuery
from aiogram.types import InlineQuery, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import set_webhook, DEFAULT_ROUTE_NAME, Executor, _setup_callbacks
from aiogram.dispatcher.webhook import WebhookRequestHandler

import hashlib

from .search_service import search
from memlish.config import BOT_TOKEN, USE_POLLING, SHOW_K_MEMES, ESTag, WEBHOOK_SSL_CERT_PATH, WEBHOOK_URL, WEBHOOK_PATH, MEMLISH_INSTRUCTION_VIDEO_URL


logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s [worker_pid={os.getpid()}] %(message)s')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def my_hash(s):
    return str(int(hashlib.md5(str(s).encode('utf-8')).hexdigest(), 16))


async def on_startup(dp):
    if USE_POLLING:
        return
    # Get current webhook status
    webhook = await bot.get_webhook_info()

    print("Previous webhook url: ", webhook.url)

    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        await bot.delete_webhook()

        # Set new URL for webhook
        is_true = await bot.set_webhook(WEBHOOK_URL, certificate=open(str(WEBHOOK_SSL_CERT_PATH), 'rb'))
        if is_true:
            print("New webhook url: ", WEBHOOK_URL)


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    logging.warning('Bye!')


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer("Hi🖐!\nMemlish🤖 will find🔎 suitable memes🪄 for your query.\nCheck video🎥 example below!")
    await message.answer_animation(MEMLISH_INSTRUCTION_VIDEO_URL)


@dp.chosen_inline_handler(lambda chosen_inline_query: True)
async def chosen_inline_handler(chosen_inline_query: types.ChosenInlineResult):
    print({
        'es_tag': ESTag.INLINE_CHOICE,
        'update': str(chosen_inline_query),
    })


@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    query = inline_query.query

    switch_pm_text = "Video tutorial"
    switch_pm_parameter = "tutorial"

    if not query:
        return AnswerInlineQuery(inline_query.id, results=[], switch_pm_text=switch_pm_text, switch_pm_parameter=switch_pm_parameter, cache_time=300, is_personal=True)

    search_docs_res = await search(query, SHOW_K_MEMES)

    uniq_candidates_id = str(uuid4())

    results = [
        InlineQueryResultPhoto(
            id=f"{i}_{uniq_candidates_id}",
            photo_url=f"{match['tags']['image_url']}",
            thumb_url=f"{match['tags']['image_url']}",
            photo_width=100,
            photo_height=100,
        )
        for i, match in enumerate(search_docs_res)
    ]

    print({
        'es_tag': ESTag.INLINE_ANSWER,
        'update': str(inline_query),
        'template_options': [{"id": r.id, "image_url": r.photo_url} for r in results]
    })

    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    return AnswerInlineQuery(inline_query.id, results=results, cache_time=0.1, is_personal=True)


async def my_web_app():
    logging.warning(f'Hello there from {os.getpid()}')

    dispatcher = dp

    check_ip = False
    retry_after = None
    route_name = DEFAULT_ROUTE_NAME
    web_app = None
    skip_updates = True
    loop = None
    request_handler = WebhookRequestHandler

    executor = Executor(dispatcher, skip_updates=skip_updates, check_ip=check_ip, retry_after=retry_after,
                        loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)

    if USE_POLLING:
        executor.start_polling()
        web_app = executor._web_app
        return web_app
    else:
        executor._prepare_webhook(
            WEBHOOK_PATH, request_handler, route_name, web_app)

        web_app = executor._web_app
        return web_app

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
