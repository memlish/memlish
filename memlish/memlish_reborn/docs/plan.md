# Memlish Reborn — Simplification Plan

Goal: same user-facing behavior (inline TG bot that overlays text on a semantically matched meme template), but with ~10× less code and zero infra beyond a single container.

## Guiding principles

1. **Single process, single container.** No bot/server split, no Jina, no MongoDB, no nginx.
2. **Drop EOL / heavy deps.** No Jina, no Aiogram 2, no original `openai/CLIP` repo, no AWS.
3. **Flat files beat databases** at 100k × 768 floats (~300 MB). `.npy` + `.json` is enough.
4. **Polling over webhook** for the MVP. No TLS, no domain, no reverse proxy.
5. **Avoid hosting images** by caching Telegram `file_id`s — no public URL needed.
6. **Fewer templates at first.** Start with ~500–2000 curated templates; scale up once the loop is proven.

## What gets cut vs. kept

| Original | Reborn |
|---|---|
| Jina AsyncFlow + 6 executors | One `search()` function, ~80 lines |
| MongoDB embedding store | `embeddings.npy` + `metadata.parquet` |
| FAISS-GPU IndexFlat | `numpy` matmul + `argpartition` (sub-10 ms at 100k) |
| AWS Translate preprocessing | Multilingual CLIP (e.g. `sentence-transformers/clip-ViT-B-32-multilingual-v1`) |
| nginx + SSL + S3 static serving | Telegram `file_id` cache → `InlineQueryResultCachedPhoto` |
| Webhook + SSL certs | Long polling |
| Aiogram 2.15 | **Aiogram 3** (modern API, async-native) |
| `openai/CLIP` git install + Torch 1.10 | `open_clip_torch` or HF `transformers` CLIP, current Torch |
| Fluentd → external ES | `logging` to stdout, Docker captures it |
| Two docker-compose files + Dockerfile.cuda | One `Dockerfile`, `docker compose up` optional |
| `SHOW_K_MEMES = 50` | Start with **10–20** (keeps per-query upload cost sane) |

Kept: CLIP-based text↔image matching, PIL text drawer (Impact + black outline + resize + wrap-with-ellipsis), the two-stage `inline_handler` + `chosen_inline_handler` pattern (useful as a click-through signal even without ES).

## Target layout

```
memlish_reborn/
├── docs/
│   ├── project_description.md
│   └── plan.md
├── src/memlish_reborn/
│   ├── config.py          # env vars, paths, k
│   ├── embed.py           # CLIP wrapper: encode_text / encode_images
│   ├── index.py           # load npy, topk search
│   ├── draw.py            # add_text_to_image (PIL, Impact, outline)
│   ├── file_id_cache.py   # upload rendered PNG → get file_id → persist
│   └── bot.py             # aiogram v3 inline + chosen handlers
├── scripts/
│   ├── build_index.py     # encode all templates → embeddings.npy
│   └── fetch_templates.py # pull a curated set of imgflip templates
├── data/                  # gitignored
│   ├── templates/*.png
│   ├── embeddings.npy
│   ├── metadata.parquet   # filename, width, height, (optional) caption
│   └── file_ids.json      # {rendered_hash: telegram_file_id}
├── tests/
│   ├── test_index.py      # determinism, topk correctness
│   └── test_draw.py       # text fits, outline present
├── Dockerfile
├── pyproject.toml
└── README.md
```

## The `file_id` trick (the key infra simplification)

Telegram inline mode requires each `InlineQueryResultPhoto` to reference an image — either a URL or an already-uploaded `file_id`. Uploading is free and the `file_id` is persistent, so:

1. On each inline query, render the N memes in parallel with PIL.
2. For each rendered PNG, compute `sha256(template_id + text)`. Look up in `file_ids.json`.
3. On miss: `bot.send_photo(staging_chat_id, photo=BytesIO(png))`, grab `message.photo[-1].file_id`, save.
4. Return `InlineQueryResultCachedPhoto(file_id=...)` for every result.

Result: **no public URL, no nginx, no TLS, no S3**. Cost: one Telegram upload per unique (template, text) pair (first time only). Cache naturally grows for popular queries.

Risk to verify early: Telegram rate limits (~30 msg/sec to a single chat). At N=20 results per query, one query = 20 uploads. Mitigate by (a) lowering N, (b) sharing a pool of staging chats, (c) falling back to `InlineQueryResultPhoto` with a locally-hosted aiohttp URL if rate-limited.

## Phased build

**Phase 0 — bootstrap (½ day).** `pyproject.toml`, pick CLIP variant (recommend `open_clip` ViT-B/32 multilingual — smaller, faster, handles non-EN queries natively), pick template set.

**Phase 1 — offline index (1 day).** `scripts/fetch_templates.py` downloads ~1k templates. `scripts/build_index.py` encodes all images, saves `embeddings.npy` + `metadata.parquet`. Verify: loading + 1 query returns visually sensible top-5.

**Phase 2 — search + draw (1 day).** `index.py::search(query, k)` → list of matches. `draw.py::add_text_to_image(path, text)` → PIL.Image. Pure-library, no bot coupling. Add tests.

**Phase 3 — bot MVP (1 day).** Aiogram 3, long polling, one inline handler. Use `file_id` cache. Run locally with BOT_TOKEN, test in a real chat.

**Phase 4 — polish (½ day).** `/start` + `/help` with the existing tutorial video URL, chosen-inline logging to stdout, basic perf log (encode ms, search ms, draw ms, upload ms).

**Phase 5 — package (½ day).** Dockerfile (CPU-only is fine for ViT-B/32 — the whole thing runs on a laptop), single `docker compose` file, `.env.example`, README with 5-line quickstart.

Stretch: GPU flag, larger template set, re-add URL hosting path as a fallback, persistent `file_ids.json` in SQLite instead of JSON.

## Acceptance criteria

- `docker compose up` with just `BOT_TOKEN` set → working bot.
- Inline query returns ≥10 matched+drawn results in <3 s cold, <1 s warm.
- No MongoDB, no nginx, no SSL cert generation step.
- Repo builds and tests pass on a fresh clone with `uv sync && pytest`.

## Open questions for the user

- **Template set**: reuse the old 100k imgflip corpus if we still have it, or start curated (~1k)? Affects index size + initial dev speed.
- **Multilingual**: keep multi-lang support day-one, or EN-only MVP and add multilingual CLIP later?
- **GPU**: target CPU-only (runs anywhere) or assume a GPU host?
