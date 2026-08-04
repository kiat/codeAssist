import os
from dataclasses import dataclass
from typing import Literal

from ai_feedback.providers.errors import (
    AIProviderError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderModelError,
    ProviderPermissionError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UnsupportedProviderError,
)


GEMINI_PROVIDER = "gemini"
GEMINI_VERTEX_PROVIDER = "gemini_vertex"
VERTEX_AUTH_ADC = "adc"
VERTEX_AUTH_API_KEY = "api_key"
DEFAULT_VERTEX_LOCATION = "global"

SUPPORTED_MODELS = {
    GEMINI_PROVIDER: {
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    },
    GEMINI_VERTEX_PROVIDER: {
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    },
}

PREFERRED_MODEL_ORDER = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


@dataclass(frozen=True)
class GeminiClientConfig:
    provider: Literal["gemini", "gemini_vertex"]
    api_key: str | None = None
    project: str | None = None
    location: str | None = None
    vertex_auth_mode: Literal["adc", "api_key"] | None = None


def get_supported_models(provider):
    models = SUPPORTED_MODELS.get(provider, set())
    return sorted(
        models,
        key=lambda model: (
            PREFERRED_MODEL_ORDER.index(model)
            if model in PREFERRED_MODEL_ORDER
            else len(PREFERRED_MODEL_ORDER),
            model,
        ),
    )


def validate_model(provider, model):
    if model not in SUPPORTED_MODELS.get(provider, set()):
        raise ProviderModelError(
            f"Model '{model}' is not supported for {provider}.",
            "Selected AI model is not supported for this provider.",
        )


def _load_genai_modules():
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ProviderConfigurationError(
            "Google Gen AI SDK is not installed.",
            "Google Gen AI SDK is not installed on the server.",
        ) from exc

    return genai, types


def create_gemini_client(config: GeminiClientConfig):
    genai, types = _load_genai_modules()
    http_options = types.HttpOptions(api_version="v1")

    if config.provider == GEMINI_PROVIDER:
        if not config.api_key:
            raise ProviderConfigurationError("Gemini Developer API key is required.")

        return genai.Client(
            api_key=config.api_key,
            http_options=http_options,
        )

    if config.provider == GEMINI_VERTEX_PROVIDER:
        auth_mode = config.vertex_auth_mode or VERTEX_AUTH_ADC

        if auth_mode == VERTEX_AUTH_API_KEY:
            if not config.api_key:
                raise ProviderConfigurationError("Vertex AI API key is required.")

            return genai.Client(
                vertexai=True,
                api_key=config.api_key,
                http_options=http_options,
            )

        if auth_mode != VERTEX_AUTH_ADC:
            raise ProviderConfigurationError(
                f"Unsupported Vertex AI auth mode: {auth_mode}."
            )

        if not config.project:
            raise ProviderConfigurationError(
                "Google Cloud project is required for Vertex AI."
            )

        return genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location or DEFAULT_VERTEX_LOCATION,
            http_options=http_options,
        )

    raise UnsupportedProviderError(config.provider)


def _get_thinking_budget(model):
    model_id = (model or "").lower()
    if "gemini-2.5-flash" in model_id:
        return 0
    if "gemini-2.5-pro" in model_id:
        return 128
    return None


def _create_generate_content_config(
    *,
    model,
    temperature,
    max_output_tokens,
    response_mime_type=None,
):
    _, types = _load_genai_modules()
    config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }

    if response_mime_type:
        config["response_mime_type"] = response_mime_type

    thinking_budget = _get_thinking_budget(model)
    if thinking_budget is not None:
        config["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget
        )

    return types.GenerateContentConfig(**config)


def classify_provider_exception(exc):
    if isinstance(exc, AIProviderError):
        return exc

    status_code = (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
        or getattr(getattr(exc, "response", None), "status_code", None)
    )
    message = str(exc)
    normalized = message.lower()

    if status_code == 429 or "quota" in normalized or "rate limit" in normalized:
        return ProviderRateLimitError(message)

    if status_code in {401, 403} and (
        "unauthenticated" in normalized
        or "credential" in normalized
        or "api key" in normalized
        or "auth" in normalized
    ):
        return ProviderAuthenticationError(message)

    if status_code == 403 or "permission" in normalized or "iam" in normalized:
        return ProviderPermissionError(message)

    if status_code in {400, 404} and (
        "model" in normalized
        or "not found" in normalized
        or "invalid argument" in normalized
    ):
        return ProviderModelError(message)

    if "timeout" in normalized or "timed out" in normalized:
        return ProviderTimeoutError(message)

    return AIProviderError(message)


class GeminiProvider:
    def __init__(self, client):
        self.client = client

    def generate(
        self,
        *,
        model,
        prompt,
        temperature,
        max_output_tokens,
        response_mime_type=None,
    ):
        try:
            config = _create_generate_content_config(
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type=response_mime_type,
            )

            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            raise classify_provider_exception(exc) from exc

        return (getattr(response, "text", None) or "").strip()


def build_developer_api_config(api_key):
    return GeminiClientConfig(
        provider=GEMINI_PROVIDER,
        api_key=api_key,
    )


def build_vertex_config(location=None):
    auth_mode = os.getenv("VERTEX_AI_AUTH_MODE", VERTEX_AUTH_ADC)
    return GeminiClientConfig(
        provider=GEMINI_VERTEX_PROVIDER,
        api_key=os.getenv("VERTEX_AI_API_KEY"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=location or os.getenv("GOOGLE_CLOUD_LOCATION") or DEFAULT_VERTEX_LOCATION,
        vertex_auth_mode=auth_mode,
    )


def has_vertex_configuration():
    auth_mode = os.getenv("VERTEX_AI_AUTH_MODE", VERTEX_AUTH_ADC)
    if auth_mode == VERTEX_AUTH_API_KEY:
        return bool(os.getenv("VERTEX_AI_API_KEY"))
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
