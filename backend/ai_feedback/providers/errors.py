class AIProviderError(Exception):
    code = "PROVIDER_ERROR"
    public_message = "AI provider request failed."

    def __init__(self, message=None, public_message=None):
        self.message = message or public_message or self.public_message
        self.public_message = public_message or self.public_message
        super().__init__(self.message)


class UnsupportedProviderError(AIProviderError):
    code = "UNSUPPORTED_PROVIDER"
    public_message = "Unsupported AI provider."


class ProviderConfigurationError(AIProviderError):
    code = "PROVIDER_CONFIGURATION_ERROR"
    public_message = "AI provider configuration is incomplete."


class ProviderAuthenticationError(AIProviderError):
    code = "PROVIDER_AUTHENTICATION_ERROR"
    public_message = "AI provider authentication failed."


class ProviderPermissionError(AIProviderError):
    code = "PROVIDER_PERMISSION_ERROR"
    public_message = "CodeAssist does not have permission to use this AI provider."


class ProviderModelError(AIProviderError):
    code = "PROVIDER_MODEL_ERROR"
    public_message = "Selected AI model is not available for this provider."


class ProviderRateLimitError(AIProviderError):
    code = "PROVIDER_RATE_LIMIT_ERROR"
    public_message = "AI provider quota or rate limit was reached."


class ProviderTimeoutError(AIProviderError):
    code = "PROVIDER_TIMEOUT_ERROR"
    public_message = "AI provider request timed out."
