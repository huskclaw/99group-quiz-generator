import httpx
import pytest

import generator
from settings import Settings


@pytest.mark.parametrize("health,models,expected", [
    (200, {"data": [{"id": "gemma-4-12b"}]}, (True, "Local model ready")),
    (503, {}, (False, "Model is loading")),
    (200, {"data": [{"id": "different-model"}]}, (False, "Configured model is not loaded")),
    (200, {"unexpected": "payload"}, (False, "Local model offline")),
])
def test_readiness_requires_health_and_matching_model(monkeypatch, health, models, expected):
    client_class = httpx.Client
    def handle(request):
        return httpx.Response(health, json={"status": "ok"}) if request.url.path == "/health" else httpx.Response(200, json=models)
    monkeypatch.setattr(generator.httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handle)))
    assert generator.check_server(Settings()) == expected
