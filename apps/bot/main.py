import logging
import os
from uuid import uuid4

from aiogram import Bot, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.webhook import SendMessage,  AnswerInlineQuery
from aiogram.types import InlineQuery, InlineQueryResultPhoto

from .search_service import search


def _get_bool(key: str) -> bool:
    return os.environ.get(key, 'False').lower() in ('true', '1', 't')


BOT_TOKEN = os.environ['BOT_TOKEN']
SERVER_NAME = os.environ['SERVER_NAME']
USE_POLLING = _get_bool('USE_POLLING')

PUBLIC_FILES_URL = f"http://{SERVER_NAME}/static_memes/"

logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s [worker_pid={os.getpid()}] %(message)s')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    pass


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    logging.warning('Bye!')


@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    query = inline_query.query

    if not query:
        return

    search_docs_res = search(query, 10)

    results = [
        InlineQueryResultPhoto(
            id=str(uuid4()),
            photo_url=f"{PUBLIC_FILES_URL}{match['id']}",
            thumb_url=f"{PUBLIC_FILES_URL}{match['id']}",
            photo_width=100,
            photo_height=100,
        )
        for match in search_docs_res
    ]
    print({
        'update': str(inline_query),
        'template_options': [r.id for r in results]
    })

    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    return AnswerInlineQuery(inline_query.id, results=results, cache_time=1, is_personal=True)


async def my_web_app():
    logging.warning(f'Hello there from {os.getpid()}')

    from aiogram.utils.executor import set_webhook, DEFAULT_ROUTE_NAME, Executor, _setup_callbacks
    from aiogram.dispatcher.webhook import WebhookRequestHandler

    dispatcher = dp
    webhook_path = f'/{BOT_TOKEN}'  # TODO: do we really need it?

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
            webhook_path, request_handler, route_name, web_app)

        web_app = executor._web_app
        return web_app

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
