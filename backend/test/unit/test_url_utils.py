import pytest
from util.url_utils import validate_ollama_url, DEFAULT_OLLAMA_BASE_URL
from util.errors import BadRequestError

def test_validate_ollama_url_success():
    # Valid default hosts should pass
    validate_ollama_url("http://localhost:11434")
    validate_ollama_url(DEFAULT_OLLAMA_BASE_URL)
    validate_ollama_url("https://127.0.0.1:11434/api")
    validate_ollama_url("") # None or empty should pass (noop)
    validate_ollama_url(None)

def test_validate_ollama_url_invalid_format():
    with pytest.raises(BadRequestError) as exc:
        validate_ollama_url("not-a-url")
    assert "Invalid URL" in str(exc.value) or "Ollama URL must use http or https" in str(exc.value)

def test_validate_ollama_url_invalid_scheme():
    with pytest.raises(BadRequestError) as exc:
        validate_ollama_url("file:///etc/passwd")
    assert "Ollama URL must use http or https" in str(exc.value)

def test_validate_ollama_url_not_whitelisted():
    # External IP / cloud metadata IP
    with pytest.raises(BadRequestError) as exc:
        validate_ollama_url("http://169.254.169.254/latest/meta-data/")
    assert "Ollama host is not permitted" in str(exc.value)
    
    # Public domain
    with pytest.raises(BadRequestError) as exc:
        validate_ollama_url("http://google.com:11434")
    assert "Ollama host is not permitted" in str(exc.value)

def test_validate_ollama_url_custom_whitelist(monkeypatch):
    monkeypatch.setenv("ALLOWED_OLLAMA_HOSTS", "custom-host.local,ollama.service")
    
    # Whitelisted hosts should pass
    validate_ollama_url("http://custom-host.local:11434")
    validate_ollama_url("https://ollama.service")
    
    # Previously valid hosts (now not in whitelist) should fail
    with pytest.raises(BadRequestError):
        validate_ollama_url("http://localhost:11434")
