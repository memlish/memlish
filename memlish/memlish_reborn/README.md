# memlish_reborn

Telegram inline bot that overlays your text on a semantically-matched meme template.

Type `@your_bot_username your text here` in any chat — get ranked meme results with your text drawn on them.

## Quickstart

```bash
uv sync --extra dev
uv run python scripts/fetch_templates.py --limit 30     # download meme templates
uv run python scripts/build_index.py                    # encode with CLIP → data/embeddings.npy
uv run pytest                                           # verify everything
BOT_TOKEN=... MEMLISH_STAGING_CHAT_ID=... uv run python -m memlish_reborn.bot
```

## Required env vars

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `MEMLISH_STAGING_CHAT_ID` | Chat ID where the bot uploads rendered memes to get persistent `file_id`s. Create a private channel, add the bot as admin, get the chat ID (e.g. via `@userinfobot` after forwarding a message). |

## Optional env vars

| Variable | Default | Purpose |
|---|---|---|
| `MEMLISH_CLIP_MODEL` | `openai/clip-vit-base-patch32` | Any HF CLIP checkpoint |
| `MEMLISH_DEVICE` | `cpu` | Set to `cuda` if you have a GPU |
| `MEMLISH_TOP_K` | `15` | How many results per inline query |
| `MEMLISH_DATA_DIR` | `./data` | Where templates/embeddings/file_ids live |

## How it works

1. **Offline**: `build_index.py` encodes each template image with CLIP → `embeddings.npy` (N × 512) + `metadata.json`.
2. **Online**: on each inline query, embed the text → numpy matmul for top-k → render text overlay with PIL → upload each to the staging chat to get a `file_id` (cached in `data/file_ids.json`) → return `InlineQueryResultCachedPhoto` list.

No public URL hosting, no SSL, no MongoDB, no FAISS. One process, one container.

## Layout

```
src/memlish_reborn/
├── config.py          env vars, paths
├── embed.py           CLIP wrapper (HF transformers)
├── index.py           numpy-matmul top-k search
├── draw.py            PIL Impact-font text overlay
├── file_id_cache.py   persistent (template+text) → file_id map
└── bot.py             Aiogram 3 inline + chosen handlers, long polling
scripts/
├── fetch_templates.py download templates from imgflip API
└── build_index.py     encode templates → embeddings.npy
tests/                 unit + semantic integration tests
```

## Docker

```bash
docker build -t memlish_reborn .
docker run --rm -e BOT_TOKEN=... -e MEMLISH_STAGING_CHAT_ID=... \
  -v "$PWD/data:/data" memlish_reborn
```

Templates + `embeddings.npy` must exist under `/data` before the bot starts.
