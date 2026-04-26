import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListView, Static

from ..widgets import RPCListItem


class RPCScreen(ModalScreen[str]):
    """Screen to select RPC and check latency."""

    DEFAULT_CSS = """
    RPCScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #rpc-container {
        width: 80%;
        height: 80%;
        background: #1e1e2e;
        border: thick #89b4fa;
        padding: 1;
    }

    #rpc-header {
        height: auto;
        width: 100%;
    }

    #header-left {
        width: 1fr;
    }

    #header-right {
        width: auto;
        text-align: right;
        color: #6c7086;
        text-style: italic;
    }

    #rpc-list {
        height: 1fr;
        border: solid #313244;
        background: #181825;
        margin: 1 0;
    }

    .url-label {
        width: 1fr;
    }

    #rpc-footer {
        height: auto;
        align: center middle;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    RPCListItem, RPCListItem > Horizontal {
        height: 1;
        min-height: 1;
        max-height: 1;
        padding: 0 1;
    }

    RPCListItem:hover {
        background: #313244;
    }

    RPCListItem.--highlight {
        background: #89b4fa 30%;
    }

    Button {
        margin: 0 1;
        background: #313244;
        color: #cdd6f4;
        border: none;
    }

    Button:hover {
        background: #45475a;
    }

    #btn-select {
        color: #a6e3a1;
    }

    #btn-back {
        color: #f38ba8;
    }
    """

    def __init__(self, chain: Dict[str, Any]):
        super().__init__()
        self.chain = chain
        self.rpc_urls: List[Dict[str, str]] = []
        raw_rpc = chain.get("rpc", [])
        for r in raw_rpc:
            url = None
            tracking = "unspecified"
            if isinstance(r, str):
                url = r
            elif isinstance(r, dict):
                url = r.get("url")
                tracking = r.get("tracking", "unspecified")
            
            if url and not url.startswith("wss://"):
                self.rpc_urls.append({"url": url, "tracking": tracking})

    def compose(self) -> ComposeResult:
        name = self.chain.get("name", "Unknown")
        cid = self.chain.get("chainId", "N/A")
        short = self.chain.get("shortName", "N/A")
        native = self.chain.get("nativeCurrency", {}).get("symbol", "N/A")

        with Container(id="rpc-container"):
            with Horizontal(id="rpc-header"):
                yield Label(f"[bold #89b4fa]{name}[/bold #89b4fa] (ID: {cid}, Short: {short}, Currency: {native})", id="header-left")
                info_url = self.chain.get("infoURL", "")
                yield Label(f"{info_url}", id="header-right")
            yield ListView(id="rpc-list")
            with Horizontal(classes="button-row"):
                yield Button("[u]B[/u]ack [ESC]", id="btn-back", variant="error")
                yield Button("[u]R[/u]etry", id="btn-retry")
                yield Button("[u]S[/u]elect [⏎]", id="btn-select", variant="success")

    async def on_mount(self) -> None:
        await self.refresh_rpcs()

    async def refresh_rpcs(self) -> None:
        rpc_list = self.query_one("#rpc-list", ListView)
        rpc_list.clear()
        
        items = []
        for r_info in self.rpc_urls:
            item = RPCListItem(r_info["url"], tracking=r_info["tracking"])
            items.append(item)
            rpc_list.append(item)
            
        # Run latency checks in background
        self.run_worker(self.check_latencies(items))

    async def check_latencies(self, items: List[RPCListItem]) -> None:
        async with httpx.AsyncClient(timeout=2.5) as client:
            tasks = [self.ping_rpc(client, item) for item in items]
            await asyncio.gather(*tasks)
            
        # Sort by latency
        rpc_list = self.query_one("#rpc-list", ListView)
        # Get data from current items before clearing
        items_data = [(item.url, item.latency, item.tracking) for item in items]
        sorted_data = sorted(items_data, key=lambda x: (x[1] is None, x[1] or 9999))
        
        rpc_list.clear()
        for url, latency, tracking in sorted_data:
            new_item = RPCListItem(url, tracking=tracking)
            rpc_list.append(new_item)
            new_item.update_latency(latency)
        
        # Reset selection to top after sort
        await asyncio.sleep(0.05)
        if rpc_list.children:
            rpc_list.index = 0
            rpc_list.focus()

    async def ping_rpc(self, client: httpx.AsyncClient, item: RPCListItem) -> None:
        start = time.time()
        try:
            # Simple JSON-RPC call to check latency
            payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            response = await client.post(item.url, json=payload)
            if response.status_code == 200:
                latency = (time.time() - start) * 1000
                item.update_latency(latency)
            else:
                item.update_latency(None)
        except Exception:
            item.update_latency(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.dismiss(None)
        elif event.button.id == "btn-retry":
            self.run_worker(self.refresh_rpcs())
        elif event.button.id == "btn-select":
            self.action_submit()

    def action_submit(self) -> None:
        rpc_list = self.query_one("#rpc-list", ListView)
        if rpc_list.highlighted_child:
            self.dismiss(rpc_list.highlighted_child.url)

    def on_key(self, event: Any) -> None:
        if event.key in ("escape", "b", "left"):
            self.dismiss(None)
        elif event.key == "r":
            self.run_worker(self.refresh_rpcs())
        elif event.key in ("enter", "s", "right"):
            self.action_submit()
