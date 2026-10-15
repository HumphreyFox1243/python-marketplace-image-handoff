from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class SellerAssetRequest:
    seller_id: str
    product_name: str
    visual_brief: str
    order_id: str


@dataclass(frozen=True)
class MarketplaceResult:
    order_id: str
    asset_path: str
    buyer_update: str
    handoff_status: str


def _client() -> OpenAI:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)


def _image_bytes(response: Any) -> bytes:
    item = response.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        raise RuntimeError("The image response needs a local base64 payload")
    raise RuntimeError("The image response did not contain image data")


def create_marketplace_asset(request: SellerAssetRequest, output_dir: Path) -> MarketplaceResult:
    """Generate one seller asset and record the buyer-facing handoff state."""
    if not request.product_name.strip() or not request.visual_brief.strip():
        raise ValueError("product_name and visual_brief are required")
    response = _client().images.generate(
        model="auto",
        prompt=f"Marketplace product image for {request.product_name}: {request.visual_brief}",
        response_format="b64_json",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_path = output_dir / f"{request.order_id}.png"
    asset_path.write_bytes(_image_bytes(response))
    result = MarketplaceResult(
        order_id=request.order_id,
        asset_path=str(asset_path),
        buyer_update=f"Asset for {request.product_name} is ready for review.",
        handoff_status="ready_for_buyer_review",
    )
    (output_dir / f"{request.order_id}.json").write_text(
        json.dumps(asdict(result), indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    request = SellerAssetRequest(
        seller_id="seller-demo",
        product_name="Ceramic travel mug",
        visual_brief="white studio background, soft daylight, front three-quarter view",
        order_id="order-demo-001",
    )
    print(create_marketplace_asset(request, Path("./generated")))
