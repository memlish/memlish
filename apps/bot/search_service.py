import sys
sys.path.append('/app')  # noqa

import aiohttp
import asyncio
from memlish.config import JINA_FLOW_PORT, SERVER_NAME
from memlish.io.timelog import log_duration


@log_duration
async def search(text, top_k=10):
    payload = {
        "data": [
            {"text": text}
        ],
        "exec_endpoint": "/search",
        "parameters": {
            "top_k": top_k,
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://{SERVER_NAME}:{JINA_FLOW_PORT}/search', json=payload) as response:
            response = await response.json()

    req_docs = response['data']['docs'][0]['matches']

    return req_docs
