import asyncio
import os
from typing import TYPE_CHECKING, Any

import httpx
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static

from ..utils.privacy import mask_url
from ..utils.rpc_tester import check_rpc_latency

if TYPE_CHECKING:
    from ..tui import ChainRPCPicker


class EnvRPCTable(DataTable[Any]):
    BINDINGS = [
        Binding("home", "cursor_top", "Top", show=False),
        Binding("end", "cursor_bottom", "Bottom", show=False),
    ]

    def action_cursor_top(self) -> None:
        if self.row_count > 0:
            self.move_cursor(row=0)

    def action_cursor_bottom(self) -> None:
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)


class EnvRPCTab(Static):
    """Tab to list and test RPCs from environment variables."""

    app: "ChainRPCPicker"  # pyrefly: ignore[bad-override]

    BINDINGS = [
        Binding("ctrl+r", "refresh_data", "Refresh", show=True),
    ]

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.env_rpcs: list[dict[str, Any]] = []
        self.spinner_index = 0

    def compose(self) -> ComposeResult:
        self.table = EnvRPCTable(id="env-rpcs-table", cursor_type="row")
        yield self.table

    def on_mount(self) -> None:
        cols = self.table.add_columns("Variable", "Chain ID", "RPC URL", "Latency")
        self.col_chain_id = cols[1]
        self.col_latency = cols[3]
        self.load_data()
        self.set_interval(0.08, self.update_spinners)

    def load_data(self) -> None:
        self._load_env_vars()
        self._render_rows()
        self.refresh_data()

    def _load_env_vars(self) -> None:
        self.env_rpcs = []

        # 1. Always prioritize ETH_RPC_URL
        eth_url = os.environ.get("ETH_RPC_URL", "").strip()
        self.env_rpcs.append(
            {
                "name": "ETH_RPC_URL",
                "url": eth_url,
                "chain_id": "⏳ Checking..." if eth_url else "N/A",
                "latency": "⏳ Checking..." if eth_url else "N/A",
                "status": "testing" if eth_url else "empty",
            }
        )

        # 2. Gather other variables with "RPC" in name (excluding ETH_RPC_URL)
        for k, v in sorted(os.environ.items()):
            k_upper = k.upper()
            if "RPC" in k_upper and k_upper != "ETH_RPC_URL":
                val = v.strip()
                self.env_rpcs.append(
                    {
                        "name": k,
                        "url": val,
                        "chain_id": "⏳ Checking..." if val else "N/A",
                        "latency": "⏳ Checking..." if val else "N/A",
                        "status": "testing" if val else "empty",
                    }
                )

    def _render_rows(self) -> None:
        if not self.is_attached:
            return
        self.table.clear()
        privacy: bool = getattr(self.app, "privacy_mode", False)
        for item in self.env_rpcs:
            url = item["url"]
            masked_url = "(not set)"
            if url:
                if privacy:
                    masked_url = mask_url(url)
                elif "/v3/" in url:
                    parts = url.split("/v3/")
                    masked_url = parts[0] + "/v3/********"
                elif "/v2/" in url:
                    parts = url.split("/v2/")
                    masked_url = parts[0] + "/v2/********"
                else:
                    masked_url = url

            var_name = f"[bold #89b4fa]{item['name']}[/]"
            self.table.add_row(
                var_name,
                item["chain_id"],
                masked_url,
                item["latency"],
                key=item["name"],
            )

        if self.table.row_count > 0:
            self.table.focus()
            self.table.move_cursor(row=0)

    def update_spinners(self) -> None:
        if not self.is_attached:
            return

        # Advance spinner frame
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
        frame = self.SPINNER_FRAMES[self.spinner_index]

        # Only update rows that are still in "testing" status
        for item in self.env_rpcs:
            if item["status"] == "testing":
                spinner_text = f"[#89b4fa]{frame}[/] [dim]Checking...[/]"
                # Columns: Variable (0), Chain ID (1), URL (2), Latency (3)
                self.table.update_cell(item["name"], self.col_chain_id, spinner_text)
                self.table.update_cell(item["name"], self.col_latency, spinner_text)

    def action_refresh_data(self) -> None:
        self.refresh_data()

    async def _get_chain_id(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_chainId",
                    "params": [],
                    "id": 1,
                }
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                if "result" in data:
                    return str(int(data["result"], 16))
                return "[red]Error[/]"
        except Exception:
            return "[red]Error[/]"

    async def _check_single_item(self, item: dict[str, Any]) -> None:
        url = item["url"]
        if not url:
            return

        chain_id, latency = await asyncio.gather(self._get_chain_id(url), check_rpc_latency(url))

        item["chain_id"] = chain_id
        item["latency"] = latency
        item["status"] = "done"

        def apply_update() -> None:
            if self.is_attached:
                self.table.update_cell(item["name"], self.col_chain_id, chain_id)
                self.table.update_cell(item["name"], self.col_latency, latency)

        self.app.call_from_thread(apply_update)

    @work(exclusive=True, thread=True)
    def refresh_data(self) -> None:
        # Reset statuses for all non-empty entries
        for item in self.env_rpcs:
            if item["url"]:
                item["status"] = "testing"
                item["chain_id"] = "⏳ Checking..."
                item["latency"] = "⏳ Checking..."
            else:
                item["status"] = "empty"
                item["chain_id"] = "N/A"
                item["latency"] = "N/A"

        self.app.call_from_thread(self._render_rows)

        async def run_all_checks() -> None:
            tasks = [self._check_single_item(item) for item in self.env_rpcs if item["url"]]
            if tasks:
                await asyncio.gather(*tasks)

        asyncio.run(run_all_checks())

    @on(DataTable.RowSelected)
    def on_rpc_selected_list(self, event: DataTable.RowSelected) -> None:
        # Get selected variable
        row_key = self.table.coordinate_to_cell_key(self.table.cursor_coordinate).row_key
        var_name = str(row_key.value)

        # Find item
        item = next((x for x in self.env_rpcs if x["name"] == var_name), None)
        if item and item["url"]:
            if hasattr(self.app.screen, "_on_rpc_selected"):
                self.app.screen._on_rpc_selected(item["url"])
