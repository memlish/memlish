import sys
sys.path.append('/app')  # noqa

import requests
from memlish.config import JINA_FLOW_PORT, SERVER_NAME


def search(text, top_k=10):
    print('text', text)

    payload = {
        "data": [
            {"text": text}
        ],
        "exec_endpoint": "/search",
        "parameters": {
            "top_k": top_k,
        },
    }

    r = requests.post(
        f'http://{SERVER_NAME}:{JINA_FLOW_PORT}/search', json=payload)
    response = r.json()

    req_docs = response['data']['docs'][0]['matches']

    return req_docs
