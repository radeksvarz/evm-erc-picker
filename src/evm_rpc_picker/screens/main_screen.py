from typing import Any, Dict, List

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label

from ..config import ConfigManager
from ..context import ContextDetector
from ..models import fetch_chains, get_cached_chains
from ..widgets import ChainsTable, EnvStatus, SearchInput
from .confirm_modal import ConfirmModal
from .rpc_screen import RPCScreen


class MainScreen(Screen[str]):
    """Main screen for searching and listing chains."""

    DEFAULT_CSS = """
    #search-container {
        height: auto;
        padding: 1 2;
        background: #181825;
        align: left middle;
    }

    #search-input {
        width: 1fr;
        border: solid #313244;
        background: #1e1e2e;
        color: #cdd6f4;
    }

    #filter-status {
        width: 18;
        margin-left: 2;
        background: #313244;
        color: #f5c2e7;
        text-style: bold;
        text-align: center;
        border: solid #45475a;
        content-align: center middle;
        height: 3;
    }

    #search-input:focus {
        border: solid #89b4fa;
    }

    #list-container {
        padding: 0 2;
    }

    DataTable {
        height: 1fr;
        border: solid #313244;
        background: #1e1e2e;
        color: #cdd6f4;
    }

    DataTable:focus {
        border: solid #89b4fa;
    }

    DataTable > .datatable--cursor {
        background: #89b4fa 30%;
    }

    DataTable > .datatable--header {
        background: #313244;
        color: #f5e0dc;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("enter", "submit", "Select"),
        ("tab", "focus_next", "Switch Focus"),
        ("/", "focus_search", "Search"),
        ("escape", "app.quit", "Exit"),
        ("ctrl+r", "load_data", "Refresh Data"),
        ("ctrl+t", "toggle_filter", "Toggle Filter"),
        ("space", "toggle_favorite", "Fav (Project)"),
        ("shift+space", "toggle_global_favorite", "Fav (Global)"),
        ("c", "init_project", "Init Project"),
    ]

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.chains: List[Dict[str, Any]] = []
        self.filtered_chains: List[Dict[str, Any]] = []
        self.filter_mode: str = "all"  # all, mainnet, testnet, favorites

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="search-container"):
            yield SearchInput(
                placeholder="Search by name or chain ID (e.g. Ethereum, 1, Polygon...)",
                id="search-input",
            )
            yield Label("Filter: ALL", id="filter-status")
        with Container(id="list-container"):
            table = ChainsTable(id="chain-table")
            table.can_focus = True
            yield table
        yield EnvStatus(id="env-status-widget")
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one(ChainsTable)
        table.add_columns("", "Chain Name", "ID", "Short", "Currency")
        table.cursor_type = "row"
        self.update_filter_status()
        self.query_one(SearchInput).focus()
        self.load_data()

    def update_filter_status(self) -> None:
        mode_label = self.filter_mode.upper()
        try:
            self.query_one("#filter-status", Label).update(f"Filter: {mode_label}")
        except Exception:
            pass

    def action_focus_search(self) -> None:
        self.query_one(SearchInput).focus()

    def action_load_data(self) -> None:
        self.run_worker(self.load_data(force=True))

    def action_toggle_filter(self) -> None:
        modes = ["all", "mainnet", "testnet", "favorites"]
        current_idx = modes.index(self.filter_mode)
        self.filter_mode = modes[(current_idx + 1) % len(modes)]
        self.update_filter_status()
        self.refresh_table()

    def action_toggle_favorite(self) -> None:
        table = self.query_one(ChainsTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(
            self.filtered_chains
        ):
            chain = self.filtered_chains[table.cursor_row]
            chain_id = chain.get("chainId")

            if not self.config.local_config_exists():
                self.app.push_screen(
                    ConfirmModal("Local config not found. Create .rpc-picker.toml?"),
                    self._on_init_confirm,
                )
                return

            self.config.toggle_favorite(chain_id, is_global=False)
            self.refresh_table()

    def _on_init_confirm(self, confirmed: bool) -> None:
        if confirmed:
            self.action_init_project()

    def action_toggle_global_favorite(self) -> None:
        table = self.query_one(ChainsTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(
            self.filtered_chains
        ):
            chain = self.filtered_chains[table.cursor_row]
            chain_id = chain.get("chainId")
            self.config.toggle_favorite(chain_id, is_global=True)
            self.refresh_table()

    def action_init_project(self) -> None:
        if self.config.local_config_exists():
            self.app.notify("Local config already exists.", severity="information")
        else:
            self.config.init_local_config()
            self.app.notify("Created .rpc-picker.toml", title="Project Initialized")
            self.refresh_table()

    def refresh_table(self) -> None:
        """Trigger search update to refresh table contents and indicators."""
        search_input = self.query_one(SearchInput)
        self.on_search(Input.Changed(search_input, search_input.value))

    @work
    async def load_data(self, force: bool = False) -> None:
        """Load chains data from cache or network."""
        if not force:
            cached = get_cached_chains()
            if cached:
                self.chains = cached
                self.update_table(self.chains)
                return

        self.app.notify("Fetching chain data...", title="Syncing")
        try:
            self.chains = await fetch_chains()
            self.update_table(self.chains)
        except Exception as e:
            self.app.notify(f"Error loading data: {e}", severity="error")

    def update_table(self, chains: List[Dict[str, Any]]) -> None:
        table = self.query_one(ChainsTable)
        table.clear()

        fav_global = self.config.get_favorites(project_only=False)
        fav_local = self.config.get_favorites(project_only=True)

        # Get chains mentioned in local tool configs (Foundry, etc.)
        context_names = {n.lower() for n in ContextDetector.get_context_chain_names()}
        context_ids = set()
        for c in self.chains:
            if (
                c.get("name", "").lower() in context_names
                or c.get("shortName", "").lower() in context_names
            ):
                context_ids.add(c.get("chainId"))

        # Sort chains by priority: Context/Local Fav > Global Fav > Others
        def get_priority(chain):
            cid = chain.get("chainId")
            if cid in fav_local or cid in context_ids:
                return 0
            if cid in fav_global:
                return 1
            return 2

        sorted_chains = sorted(
            chains, key=lambda x: (get_priority(x), x.get("chainId", 0))
        )
        self.filtered_chains = sorted_chains

        for i, chain in enumerate(sorted_chains):
            cid = chain.get("chainId")
            indicator = ""

            is_local = cid in fav_local or cid in context_ids
            is_global = cid in fav_global

            if is_local:
                indicator = "* [P]"
            elif is_global:
                indicator = "*"

            native = chain.get("nativeCurrency", {}).get("symbol", "N/A")
            table.add_row(
                indicator,
                chain.get("name", "Unknown"),
                str(cid),
                chain.get("shortName", "N/A"),
                native,
                key=str(i),
            )

    @on(Input.Changed, "#search-input")
    def on_search(self, event: Input.Changed) -> None:
        query = event.value.lower()

        filtered = self.chains

        # Apply network type filter
        fav_all = self.config.get_favorites()
        if self.filter_mode == "mainnet":
            filtered = [c for c in filtered if not c.get("isTestnet", False)]
        elif self.filter_mode == "testnet":
            filtered = [c for c in filtered if c.get("isTestnet", False)]
        elif self.filter_mode == "favorites":
            filtered = [c for c in filtered if c.get("chainId") in fav_all]

        # Apply search query
        if query:
            filtered = [
                c
                for c in filtered
                if query in c.get("name", "").lower()
                or query in str(c.get("chainId", ""))
            ]

        self.update_table(filtered)

    @on(Input.Submitted, "#search-input")
    def on_input_submitted(self) -> None:
        table = self.query_one(ChainsTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(
            self.filtered_chains
        ):
            chain = self.filtered_chains[table.cursor_row]
            self.app.push_screen(RPCScreen(chain), self.on_rpc_selected)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = int(event.row_key.value)
        chain = self.filtered_chains[idx]
        self.app.push_screen(RPCScreen(chain), self.on_rpc_selected)

    def on_key(self, event: Any) -> None:
        # Type-to-search: if typing printable chars outside search input, focus it
        # Only trigger if the key is not already handled by bindings
        if (
            event.character
            and len(event.character) == 1
            and event.character.isprintable()
            and self.focused
            and self.focused.id != "search-input"
        ):
            # Skip keys that are used for bindings
            if event.key in ("space", "c", "C", "enter", "tab", "escape"):
                return
            search_input = self.query_one(SearchInput)
            # Set value first, then focus (on_focus will handle cursor)
            if event.character != "/":
                search_input.value = event.character

            search_input.focus()
            event.stop()
            return

        if event.key == "tab":
            self.focus_next()
            event.stop()
            return

        if event.key == "right":
            if self.focused and self.focused.id == "chain-table":
                table = self.query_one(ChainsTable)
                if table.cursor_row is not None and 0 <= table.cursor_row < len(
                    self.filtered_chains
                ):
                    chain = self.filtered_chains[table.cursor_row]
                    self.app.push_screen(RPCScreen(chain), self.on_rpc_selected)
                event.stop()
                return

        if (
            event.key == "enter"
            and self.focused
            and self.focused.id == "env-status-widget"
        ):
            env_status = self.query_one(EnvStatus)
            if env_status.current_rpc:
                self.app.exit(env_status.current_rpc)
            event.stop()
            return

        if event.key in ("up", "down", "pageup", "pagedown"):
            if self.focused and self.focused.id == "search-input":
                table = self.query_one(ChainsTable)
                if event.key == "up":
                    table.action_cursor_up()
                elif event.key == "down":
                    table.action_cursor_down()
                elif event.key == "pageup":
                    table.action_page_up()
                elif event.key == "pagedown":
                    table.action_page_down()
                event.stop()

    def on_rpc_selected(self, rpc_url: str) -> None:
        if rpc_url:
            self.app.exit(rpc_url)
