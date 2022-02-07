import requests


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

    r = requests.post('http://35.224.116.253:7070/search', json=payload)
    response = r.json()

    req_docs = response['data']['docs'][0]['matches']

    return req_docs
