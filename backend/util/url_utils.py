import os
import urllib.parse
DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"

from util.errors import BadRequestError

def validate_ollama_url(url):
    """
    Validates that the provided Ollama URL is safe and points to a whitelisted host.
    Raises BadRequestError if invalid.
    """
    if not url:
        return
        
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
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

    # Prevent DNS rebinding SSRF targeting cloud metadata / link-local addresses
    import socket
    try:
        ip = socket.gethostbyname(hostname)
        if ip.startswith("169.254."):
            raise BadRequestError("Ollama host resolves to a restricted IP address")
    except socket.gaierror:
        pass
