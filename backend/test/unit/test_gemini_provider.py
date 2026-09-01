import pytest

from ai_feedback.providers.errors import (
    ProviderConfigurationError,
    ProviderModelError,
    ProviderPermissionError,
    UnsupportedProviderError,
)
from ai_feedback.providers.gemini import (
    GEMINI_PROVIDER,
    GEMINI_VERTEX_PROVIDER,
    VERTEX_AUTH_API_KEY,
    GeminiClientConfig,
    GeminiProvider,
    classify_provider_exception,
    create_gemini_client,
    validate_model,
)


class FakeTypes:
    class HttpOptions:
        def __init__(self, api_version):
            self.api_version = api_version

    class ThinkingConfig:
        def __init__(self, thinking_budget):
            self.thinking_budget = thinking_budget

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs


class FakeGenAI:
    def __init__(self):
        self.calls = []

    def Client(self, **kwargs):
        self.calls.append(kwargs)
        return {"client_kwargs": kwargs}


def test_create_gemini_client_uses_developer_api_key(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    client = create_gemini_client(
        GeminiClientConfig(provider=GEMINI_PROVIDER, api_key="gemini-key")
    )

    assert client["client_kwargs"]["api_key"] == "gemini-key"
    assert client["client_kwargs"]["http_options"].api_version == "v1"


def test_create_gemini_client_requires_developer_api_key(monkeypatch):
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )

    with pytest.raises(ProviderConfigurationError):
        create_gemini_client(GeminiClientConfig(provider=GEMINI_PROVIDER))


def test_create_gemini_vertex_adc_client_defaults_location(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    client = create_gemini_client(
        GeminiClientConfig(provider=GEMINI_VERTEX_PROVIDER, project="project-1")
    )

    assert client["client_kwargs"]["vertexai"] is True
    assert client["client_kwargs"]["project"] == "project-1"
    assert client["client_kwargs"]["location"] == "global"
    assert client["client_kwargs"]["http_options"].api_version == "v1"


def test_create_gemini_vertex_adc_requires_project(monkeypatch):
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )

    with pytest.raises(ProviderConfigurationError):
        create_gemini_client(GeminiClientConfig(provider=GEMINI_VERTEX_PROVIDER))


def test_create_gemini_vertex_api_key_mode_requires_api_key(monkeypatch):
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )

    with pytest.raises(ProviderConfigurationError):
        create_gemini_client(
            GeminiClientConfig(
                provider=GEMINI_VERTEX_PROVIDER,
                vertex_auth_mode=VERTEX_AUTH_API_KEY,
            )
        )


def test_create_gemini_vertex_api_key_mode_uses_project_location_when_present(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    client = create_gemini_client(
        GeminiClientConfig(
            provider=GEMINI_VERTEX_PROVIDER,
            api_key="vertex-key",
            project="project-1",
            location="global",
            vertex_auth_mode=VERTEX_AUTH_API_KEY,
        )
    )

    assert client["client_kwargs"]["vertexai"] is True
    assert client["client_kwargs"]["api_key"] == "vertex-key"
    assert client["client_kwargs"]["project"] == "project-1"
    assert client["client_kwargs"]["location"] == "global"
    assert client["client_kwargs"]["http_options"].api_version == "v1"


def test_create_gemini_client_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )

    with pytest.raises(UnsupportedProviderError):
        create_gemini_client(GeminiClientConfig(provider="llama"))


def test_classify_vertex_predict_permission_error_has_actionable_message():
    class FakePermissionError(Exception):
        status_code = 403

    error = classify_provider_exception(
        FakePermissionError("Permission 'aiplatform.endpoints.predict' denied")
    )

    assert isinstance(error, ProviderPermissionError)
    assert "aiplatform.endpoints.predict" in error.public_message
    assert "Vertex AI User" in error.public_message


def test_gemini_provider_generate_passes_model_prompt_and_config(monkeypatch):
    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return type("Response", (), {"text": "OK"})()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )

    result = GeminiProvider(FakeClient()).generate(
        model="gemini-2.5-flash",
        prompt="Reply OK",
        temperature=0,
        max_output_tokens=10,
        response_mime_type="application/json",
    )

    assert result == "OK"
    assert captured["model"] == "gemini-2.5-flash"
    assert captured["contents"] == "Reply OK"
    assert captured["config"].kwargs["temperature"] == 0
    assert captured["config"].kwargs["max_output_tokens"] == 10
    assert captured["config"].kwargs["response_mime_type"] == "application/json"
    assert captured["config"].kwargs["thinking_config"].thinking_budget == 0


def test_validate_model_rejects_unsupported_vertex_model():
    with pytest.raises(ProviderModelError):
        validate_model(GEMINI_VERTEX_PROVIDER, "gemini-2.0-flash")
