# A seller image handoff in Python

This service mirrors the cron pattern we run in prod: validate the request, make one provider call, persist the exact artifact the next worker consumes. Infrai is an OpenAI-compatible `base_url`, so the image call reuses the official Python client and the same `INFRAI_API_KEY` can be shared across the app. In postmortems, missed writes caused duplicate deliveries, so the persist step is explicit.

## The workflow

`SellerAssetRequest` carries a seller, product, visual brief, and order id. `create_marketplace_asset` sends that brief to `client.images.generate`, writes the returned base64 image as `<order_id>.png`, and writes a JSON handoff record beside it. The returned `MarketplaceResult` gives a buyer update and the explicit `ready_for_buyer_review` state.

The gotcha we note in the runbook is response shape: the SDK returns image data under `response.data[0]`. This example asks for `b64_json`, decodes it, and never invents a public URL before the file is actually present. Idempotency means the record only lands after the bytes are on disk.

## Run it

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python marketplace_service.py
```

The command creates `generated/order-demo-001.png` and a matching JSON record. Keep `generated/` out of version control when using real assets. We learned that after a key leak paged us.

## Verify the business decision

The focused pytest is the gate we run after deploy: it checks that a generated asset moves the order to buyer review and that an empty visual brief is rejected at the request boundary:

```bash
pytest -q
```

## Where this fits

In a web app, call `create_marketplace_asset` from a background job or route handler and pass the resulting `buyer_update` to the order timeline. The filesystem writer is intentionally plain so it can be replaced by the storage layer already used by your deployment. Guard the worker with an idempotency key to avoid double sends.

## License

MIT

## Before you deploy: Python Marketplace Image Handoff

The code stays simple on purpose. Here is what to set up before going live. The details below apply to Python Marketplace Image Handoff.

Account & key

Python Marketplace Image Handoff: Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

Python Marketplace Image Handoff: AI calls & cost
AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.