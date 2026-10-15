from pathlib import Path

import pytest

from marketplace_service import SellerAssetRequest, create_marketplace_asset


class FakeImages:
    def generate(self, **kwargs):
        assert kwargs["model"] == "auto"
        assert "Ceramic travel mug" in kwargs["prompt"]
        assert kwargs["response_format"] == "b64_json"
        return type("Response", (), {"data": [type("Item", (), {"b64_json": "aGVsbG8="})()]})()


class FakeClient:
    images = FakeImages()


def test_generation_marks_order_ready(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr("marketplace_service._client", lambda: FakeClient())
    result = create_marketplace_asset(
        SellerAssetRequest("seller-1", "Ceramic travel mug", "studio shot", "order-7"),
        tmp_path,
    )
    assert result.handoff_status == "ready_for_buyer_review"
    assert result.buyer_update.endswith("ready for review.")
    assert (tmp_path / "order-7.png").read_bytes() == b"hello"


def test_blank_brief_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="visual_brief"):
        create_marketplace_asset(SellerAssetRequest("s", "Mug", " ", "o"), tmp_path)
