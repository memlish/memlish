# Memlish — Project Description

## What it is

A Telegram bot that generates memes on the fly via **inline mode**.
User types `@memlish_bot <query>` in any chat → bot returns ~50 ranked meme images where the query text is drawn over a semantically matching template. User taps one to send it.

Original repo: `github.com/memlish/memlish` (circa 2024, Python 3, CUDA).

## Core idea

1. **Offline**: pre-embed ~100k ImgFlip meme templates with CLIP into a FAISS index (cached in MongoDB).
2. **Online**: embed the user's query with the same CLIP encoder → FAISS top-k search → draw query text on each matched template → return as Telegram inline photo results.

The match is semantic (image↔text via CLIP), not keyword-based. That's the whole trick.

## End-to-end request flow

```
User types @memlish_bot funny cat
        │
        ▼
Aiogram inline_handler (apps/bot)
        │  HTTP POST {text, top_k=50}
        ▼
Jina AsyncFlow server (apps/jina.server)
  ├─ DocPreFormatter     copy text → tags.text_to_draw
  ├─ AwsTranslator       non-EN → EN (AWS Translate)
  ├─ OpenAICLIPTextEnc.  text → 768-D embedding (CLIP ViT-L/14)
  ├─ FaissIndexer        top-k over 100k template embeddings
  ├─ TextDrawer          PIL overlay (Impact font + outline), writes PNG
  └─ DocPostFormatter    rewrite local paths → public S3/nginx URLs
        │
        ▼
Bot returns List[InlineQueryResultPhoto] with image URLs
```

Inline result `cache_time` is tiny (~0.5 s) in dev, meant to bump in prod.
`chosen_inline_handler` logs which result the user actually picked (ES tag `INLINE_CHOICE`) for analytics.

## Tech stack

| Layer | Choice |
|---|---|
| Bot framework | **Aiogram 2.15** (webhook via aiohttp + gunicorn, port 7654; polling fallback) |
| Pipeline orchestration | **Jina 2.6.4** AsyncFlow of executors |
| Text/image encoder | **OpenAI CLIP** ViT-L/14 (git install) |
| Vector search | **FAISS-GPU 1.7.2**, IndexFlat, inner product |
| Embedding cache | **MongoDB** (collection `02_lclip_imgflip_template_image_100k_embeddings`, pickled numpy) |
| Language detection | **fasttext** (176 langs) + **spaCy** sentence split (underused) |
| Translation | **AWS Translate** via boto3 |
| Image ops | **Pillow** — Impact font, black outline, resize to 256×256, auto-wrap w/ ellipsis |
| Edge | **nginx** — TLS termination, reverse proxy to bot, static serving of generated memes |
| Infra | Docker Compose (bot, jina server, mongo, jupyter), CUDA base image, fluentd → ES logs |

## Repo layout (what matters)

```
memlish/
├── apps/
│   ├── bot/main.py                  # Aiogram inline + chosen handlers
│   ├── bot/search_service.py        # HTTP client to jina server
│   └── jina.server/main.py          # Flow wiring, loads executors
├── memlish/
│   ├── config.py                    # paths, env vars, SHOW_K_MEMES=50
│   ├── lang_detector.py             # FasttextLanguageDetector
│   ├── executors/
│   │   ├── openai_clip.py           # CLIP text encoder executor
│   │   ├── index.py                 # FaissIndexer (load from mongo, search)
│   │   ├── cache.py                 # mongo embedding read/write helpers
│   │   ├── text_drawer.py           # TextDrawer (ThreadPoolExecutor, 50 parallel)
│   │   ├── docs_formatter.py        # pre/post format executors
│   │   ├── transalator.py           # AwsTranslator
│   │   └── bert.py                  # alt SBERT encoder (unused in main flow)
│   └── image_processing/
│       ├── text_drawer.py           # DefaultTextDrawer.add_text_to_image
│       └── fonts/impact.ttf
├── infrastructure/
│   ├── mongodb/docker-compose.yml
│   └── nginx/                       # conf + certs/{cert.pem,private.key}
├── docker-compose.tgbot.yml
├── docker-compose.jina.server.yml
├── docker-compose.jupyter.yml
├── Dockerfile.cuda
└── docs/                            # vm/env/aws/docker/mongo/logs setup guides
```

## Data & assets

- **Templates**: `/data/imgflip/v1/images/` — ~100k PNGs.
- **Generated**: `/data/imgflip/drown_images/{uuid}/*.png` — served by nginx under `/static_memes/`.
- **Embeddings**: pre-computed in MongoDB; FAISS index persisted in Jina executor workspace.
- **Public URL base**: `https://{SERVER_NAME}/static_memes/`.
- **Tutorial video**: `s3://memlish.head.public/memlish/memlish_instruction.mp4` (sent on `/start`).

## Config / required env

`BOT_TOKEN`, `SERVER_NAME` (FQDN for webhook + URLs), `JINA_FLOW_PORT`, `MONGODB_CONNECTION_STRING`, AWS creds (boto3 default chain), `USE_POLLING`, `DEBUG_MODE`.
SSL cert + key mounted at `/certs/cert.pem`, `/certs/private.key`.

## Notable / worth preserving

- **Pre-embed once, query cheap** — online path is just 1 CLIP forward + FAISS search + N PIL draws.
- **CLIP matches text queries against image embeddings directly** — no template captions needed.
- **Translate-before-embed** lets non-English queries work even though CLIP is EN-heavy.
- **Parallel draw** — TextDrawer fans out 50 overlays via thread pool; keeps inline latency low.
- **Stateless bot, stateful server** — bot is a thin webhook; heavy RAM (~18 GB: CLIP + FAISS + images) lives in the jina server container.
- **Two-stage analytics** — `INLINE_ANSWER` on query, `INLINE_CHOICE` on pick → click-through signal for ranking.

## Rough pain points for a rewrite

- Jina 2.x is EOL; executors + AsyncFlow API are gone in current Jina. Pipeline should be plain async Python (or a modern orchestrator).
- Aiogram 2.x is legacy; v3 has a different API.
- CLIP ViT-L/14 via the original `openai/CLIP` git repo is dated — open-clip or transformers `CLIPModel` is the modern path.
- MongoDB-as-embedding-store is overkill; a single FAISS file + metadata parquet is simpler.
- CUDA 1.10 PyTorch pinning blocks upgrades; requires full dep refresh.
- No tests, no CI, assets hard-coded to `/data/imgflip/`.
