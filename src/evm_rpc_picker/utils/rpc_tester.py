import time

import httpx


async def check_rpc_latency(url: str, timeout: float = 2.0) -> str:
    """Check the latency of an RPC endpoint by calling eth_blockNumber."""
    if url.startswith("wss://") or url.startswith("ws://"):
        return "[yellow]WSS[/]"

    if "${API_KEY}" in url:
        return "[red]Locked[/]"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1,
            }
            start_time = time.monotonic()
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

            # Ensure it's a valid RPC response
            data = resp.json()
            if "result" not in data and "error" not in data:
                return "[red]Error[/]"

            elapsed = (time.monotonic() - start_time) * 1000

            # Color coding
            if elapsed < 100:
                return f"[green]{elapsed:.0f} ms[/]"
            elif elapsed < 300:
                return f"[yellow]{elapsed:.0f} ms[/]"
            else:
                return f"[red]{elapsed:.0f} ms[/]"
    except Exception:
        return "[red]Error[/]"
