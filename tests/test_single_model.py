from fastapi.testclient import TestClient

from chathexo.main import app
from chathexo.settings import settings


def test_models_endpoint_is_removed():
    response = TestClient(app).get("/chathexo-api/models")

    assert response.status_code == 404


def test_chat_request_rejects_model_override():
    response = TestClient(app).post(
        "/chathexo-api/chat",
        json={"query": "你好", "model": "local-Kimi-K2.6"},
    )

    assert response.status_code == 422


def test_backend_uses_fixed_model():
    assert settings.model == "gpt-5.6-sol-azure"
    assert not hasattr(settings, "default_model")
    assert not hasattr(settings, "available_models")
