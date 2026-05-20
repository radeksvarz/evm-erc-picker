"""Privacy utility helpers for masking sensitive RPC URLs."""


def mask_url(url: str) -> str:
    """Mask sensitive paths, API keys or tokens in an RPC URL.

    Keeps the scheme and host part only, replacing credentials and paths with
    privacy symbols. For example:
    - https://mainnet.infura.io/v3/1234 -> https://mainnet.infura.io/••••••••
    - https://user:password@server/apikey -> https://••••••••@server/••••••••
    - http://localhost:8545 -> http://localhost:8545
    """
    if not url:
        return ""
    url = url.strip()

    # Handle standard protocols
    if "://" not in url:
        return "••••••••"

    parts = url.split("://", 1)
    scheme = parts[0]
    rest = parts[1]

    subparts = rest.split("/", 1)
    host_part = subparts[0]

    # Mask user:password credentials if present (user:pass@host)
    if "@" in host_part:
        host = host_part.split("@", 1)[1]
        host_display = f"••••••••@{host}"
    else:
        host_display = host_part

    if len(subparts) > 1 and subparts[1]:
        return f"{scheme}://{host_display}/••••••••"
    return f"{scheme}://{host_display}"
