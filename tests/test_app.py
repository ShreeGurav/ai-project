from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_page_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "HelpMate AI" in response.text


def test_chat_requires_azure_configuration() -> None:
    with patch.dict("os.environ", {}, clear=True):
        response = client.post("/chat", json={"message": "How long is shipping?"})

    assert response.status_code == 503
    assert "AZURE_OPENAI_ENDPOINT" in response.json()["detail"]


def test_chat_uses_configured_azure_openai() -> None:
    class FakeMessage:
        content = "Standard shipping usually takes 3–5 business days."

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletion:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs: object) -> FakeCompletion:
            assert kwargs["model"] == "support-model"
            assert kwargs["temperature"] == 0.2
            return FakeCompletion()

    class FakeChat:
        completions = FakeCompletions()

    class FakeAzureOpenAI:
        def __init__(self, **kwargs: str) -> None:
            assert kwargs["azure_endpoint"] == "https://example.openai.azure.com"

        chat = FakeChat()

    environment = {
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT": "support-model",
    }
    with patch.dict("os.environ", environment, clear=True), patch(
        "app.main.AzureOpenAI", FakeAzureOpenAI
    ):
        response = client.post("/chat", json={"message": "How long is shipping?"})

    assert response.status_code == 200
    assert "3–5 business days" in response.json()["answer"]


def test_chat_rejects_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
