import pytest

from ai_feedback.providers.errors import (
    AIProviderError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderModelError,
    ProviderPermissionError,
    ProviderRateLimitError,
    UnsupportedProviderError,
)
from ai_feedback.providers.gemini import (
    GEMINI_MAX_ATTEMPTS,
    GEMINI_PROVIDER,
    GEMINI_REQUEST_TIMEOUT_MS,
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
        def __init__(self, api_version, timeout=None):
            self.api_version = api_version
            self.timeout = timeout

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


def test_create_gemini_vertex_api_key_mode_rejects_region_without_project(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    with pytest.raises(ProviderConfigurationError) as exc_info:
        create_gemini_client(
            GeminiClientConfig(
                provider=GEMINI_VERTEX_PROVIDER,
                api_key="vertex-key",
                location="us-central1",
                vertex_auth_mode=VERTEX_AUTH_API_KEY,
            )
        )

    assert "GOOGLE_CLOUD_PROJECT" in exc_info.value.public_message
    assert fake_genai.calls == []


def test_create_gemini_vertex_api_key_mode_allows_global_without_project(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    client = create_gemini_client(
        GeminiClientConfig(
            provider=GEMINI_VERTEX_PROVIDER,
            api_key="vertex-key",
            location="global",
            vertex_auth_mode=VERTEX_AUTH_API_KEY,
        )
    )

    assert client["client_kwargs"]["api_key"] == "vertex-key"
    assert "project" not in client["client_kwargs"]
    assert "location" not in client["client_kwargs"]


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


def test_classify_invalid_developer_api_key_as_authentication_error():
    class FakeClientError(Exception):
        code = 400

    error = classify_provider_exception(
        FakeClientError(
            "400 INVALID_ARGUMENT. {'error': {'message': 'API key not valid. "
            "Please pass a valid API key.', 'reason': 'API_KEY_INVALID'}}"
        )
    )

    assert isinstance(error, ProviderAuthenticationError)
    assert error.public_message == "Gemini API key is not valid."


def test_classify_missing_adc_credentials_as_configuration_error():
    class DefaultCredentialsError(Exception):
        pass

    error = classify_provider_exception(
        DefaultCredentialsError("Your default credentials were not found.")
    )

    assert isinstance(error, ProviderConfigurationError)
    assert "GOOGLE_APPLICATION_CREDENTIALS" in error.public_message


def test_classify_credential_refresh_failure_as_authentication_error():
    class RefreshError(Exception):
        pass

    error = classify_provider_exception(RefreshError("invalid_grant"))

    assert isinstance(error, ProviderAuthenticationError)


def test_classify_unknown_error_stays_generic():
    error = classify_provider_exception(RuntimeError("something odd"))

    assert type(error) is AIProviderError


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


class FakeServerError(Exception):
    def __init__(self, code, message="503 UNAVAILABLE. The model is overloaded."):
        super().__init__(message)
        self.code = code


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.models = FakeModels(outcomes)


class FakeResponse:
    text = " ok "


def _patch_generation(monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (FakeGenAI(), FakeTypes),
    )
    monkeypatch.setattr(
        "ai_feedback.providers.gemini.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )
    return sleeps


def _generate(provider):
    return provider.generate(
        model="gemini-2.5-flash",
        prompt="prompt",
        temperature=0,
        max_output_tokens=100,
    )


def test_create_gemini_client_sets_request_timeout(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(
        "ai_feedback.providers.gemini._load_genai_modules",
        lambda: (fake_genai, FakeTypes),
    )

    client = create_gemini_client(
        GeminiClientConfig(provider=GEMINI_PROVIDER, api_key="gemini-key")
    )

    assert client["client_kwargs"]["http_options"].timeout == GEMINI_REQUEST_TIMEOUT_MS


def test_gemini_provider_retries_transient_error_then_succeeds(monkeypatch):
    sleeps = _patch_generation(monkeypatch)
    client = FakeClient([FakeServerError(503), FakeResponse()])

    assert _generate(GeminiProvider(client)) == "ok"
    assert client.models.calls == 2
    assert sleeps == [1]


def test_gemini_provider_retries_network_errors(monkeypatch):
    class TransportError(Exception):
        pass

    class ReadTimeout(TransportError):
        pass

    _patch_generation(monkeypatch)
    client = FakeClient([ReadTimeout("timed out"), FakeResponse()])

    assert _generate(GeminiProvider(client)) == "ok"
    assert client.models.calls == 2


def test_gemini_provider_gives_up_after_max_attempts(monkeypatch):
    sleeps = _patch_generation(monkeypatch)
    client = FakeClient([FakeServerError(429, "429 RESOURCE_EXHAUSTED quota")] * GEMINI_MAX_ATTEMPTS)

    with pytest.raises(ProviderRateLimitError):
        _generate(GeminiProvider(client))

    assert client.models.calls == GEMINI_MAX_ATTEMPTS
    assert sleeps == [1, 2]


def test_gemini_provider_does_not_retry_client_errors(monkeypatch):
    sleeps = _patch_generation(monkeypatch)
    client = FakeClient([FakeServerError(404, "404 NOT_FOUND model not found")])

    with pytest.raises(ProviderModelError):
        _generate(GeminiProvider(client))

    assert client.models.calls == 1
    assert sleeps == []


def test_gemini_provider_single_attempt_skips_retry(monkeypatch):
    sleeps = _patch_generation(monkeypatch)
    client = FakeClient([FakeServerError(503), FakeResponse()])

    with pytest.raises(AIProviderError):
        _generate(GeminiProvider(client, max_attempts=1))

    assert client.models.calls == 1
    assert sleeps == []


def test_validate_model_accepts_default_vertex_models(monkeypatch):
    monkeypatch.delenv("VERTEX_AI_MODELS", raising=False)

    for model in ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"):
        validate_model(GEMINI_VERTEX_PROVIDER, model)


def test_validate_model_rejects_retired_vertex_models(monkeypatch):
    monkeypatch.delenv("VERTEX_AI_MODELS", raising=False)

    for model in ("gemini-1.5-flash", "gemini-1.5-pro"):
        with pytest.raises(ProviderModelError):
            validate_model(GEMINI_VERTEX_PROVIDER, model)


def test_validate_model_uses_vertex_env_override(monkeypatch):
    monkeypatch.setenv("VERTEX_AI_MODELS", "gemini-next-pro")

    validate_model(GEMINI_VERTEX_PROVIDER, "gemini-next-pro")
    with pytest.raises(ProviderModelError):
        validate_model(GEMINI_VERTEX_PROVIDER, "gemini-2.5-flash")


def test_validate_model_developer_api_accepts_any_unblocked_gemini_model():
    validate_model(GEMINI_PROVIDER, "gemini-2.5-flash-lite")
    validate_model(GEMINI_PROVIDER, "gemini-next-flash")

    for model in (
        "gemini-2.0-flash",
        "gemini-2.5-flash-preview-tts",
        "gemini-embedding-001",
        "text-bison",
    ):
        with pytest.raises(ProviderModelError):
            validate_model(GEMINI_PROVIDER, model)
