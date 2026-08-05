import os
import urllib.parse
from util.errors import BadRequestError

def validate_ollama_url(url):
    """
    Validates that the provided Ollama URL is safe and points to a whitelisted host.
    Raises BadRequestError if invalid.
    """
    if not url:
        return
        
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        raise BadRequestError("Invalid URL format")
        
    # Strictly require http or https scheme
    if parsed.scheme not in ("http", "https"):
        raise BadRequestError("Ollama URL must use http or https scheme")
        
    # Require hostname to be present
    hostname = parsed.hostname
    if not hostname:
        raise BadRequestError("Invalid Ollama URL hostname")
        
    # Get whitelist from environment or standard default
    allowed_hosts_str = os.getenv("ALLOWED_OLLAMA_HOSTS", "localhost,host.docker.internal,127.0.0.1")
    allowed_hosts = [h.strip().lower() for h in allowed_hosts_str.split(",") if h.strip()]
    
    if hostname.lower() not in allowed_hosts:
        raise BadRequestError("Ollama host is not permitted by system administrator")
