import os
import time
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
GEMINI_REQUEST_TIMEOUT_MS = 60_000
GEMINI_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
GEMINI_MAX_ATTEMPTS = 3
GEMINI_RETRY_BACKOFF_SECONDS = 1

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
    http_options = types.HttpOptions(
        api_version="v1",
        timeout=GEMINI_REQUEST_TIMEOUT_MS,
    )

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

            client_kwargs = {
                "vertexai": True,
                "api_key": config.api_key,
                "http_options": http_options,
            }
            location = config.location or DEFAULT_VERTEX_LOCATION
            if config.project:
                client_kwargs["project"] = config.project
                client_kwargs["location"] = location
            elif location != DEFAULT_VERTEX_LOCATION:
                raise ProviderConfigurationError(
                    "Vertex AI location override requires GOOGLE_CLOUD_PROJECT "
                    "in API-key mode.",
                    "A Vertex AI location other than global requires "
                    "GOOGLE_CLOUD_PROJECT in the server configuration.",
                )

            return genai.Client(**client_kwargs)

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


def _get_status_code(exc):
    return (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
        or getattr(getattr(exc, "response", None), "status_code", None)
    )


def is_transient_provider_error(exc):
    """Returns True for provider failures worth retrying (overload, rate limit, network)."""
    if isinstance(exc, AIProviderError):
        return False

    if _get_status_code(exc) in GEMINI_TRANSIENT_STATUS_CODES:
        return True

    # httpx timeouts and connection failures all derive from TransportError.
    return any(
        cls.__name__ == "TransportError" for cls in type(exc).__mro__
    )


def get_retry_delay(attempt):
    """Returns the exponential backoff delay before the next Gemini retry."""
    return GEMINI_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))


def classify_provider_exception(exc):
    if isinstance(exc, AIProviderError):
        return exc

    status_code = _get_status_code(exc)
    message = str(exc)
    normalized = message.lower()
    exception_name = type(exc).__name__

    # google-auth errors are matched by name so the SDK stays an optional import.
    if exception_name == "DefaultCredentialsError":
        return ProviderConfigurationError(
            message,
            "Vertex AI credentials were not found on the server. Set "
            "GOOGLE_APPLICATION_CREDENTIALS to a service account key file or "
            "configure Application Default Credentials.",
        )

    if exception_name == "RefreshError":
        return ProviderAuthenticationError(message)

    # The Developer API reports a bad key as 400 INVALID_ARGUMENT, not 401.
    if "api key not valid" in normalized or "api_key_invalid" in normalized:
        return ProviderAuthenticationError(
            message,
            "Gemini API key is not valid.",
        )

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
        if "aiplatform.endpoints.predict" in normalized:
            return ProviderPermissionError(
                message,
                "Vertex AI permission denied. Grant a role with "
                "aiplatform.endpoints.predict, such as Vertex AI User or "
                "Vertex AI Express User, and ensure the Vertex AI API is enabled.",
            )

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
    def __init__(self, client, max_attempts=GEMINI_MAX_ATTEMPTS):
        self.client = client
        self.max_attempts = max(1, max_attempts)

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
        except Exception as exc:
            raise classify_provider_exception(exc) from exc

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                break
            except Exception as exc:
                if attempt < self.max_attempts and is_transient_provider_error(exc):
                    print(
                        f"GEMINI_RETRY: {type(exc).__name__} on attempt "
                        f"{attempt}/{self.max_attempts}; retrying",
                        flush=True,
                    )
                    time.sleep(get_retry_delay(attempt))
                    continue
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
