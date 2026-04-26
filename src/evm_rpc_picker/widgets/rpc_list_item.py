from typing import Optional
from textual.containers import Container
from textual.widgets import Label, ListItem

class RPCListItem(ListItem):
    DEFAULT_CSS = """
    RPCListItem {
        height: 1;
        padding: 0 1;
    }
    .rpc-row-grid {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 5 12;
        height: 1;
    }
    .privacy-symbol {
        width: 100%;
        text-align: center;
    }
    .latency-label {
        width: 100%;
        text-align: right;
        color: #fab387;
    }
    """
    def __init__(self, url: str, tracking: str = "unspecified"):
        super().__init__()
        self.url = url
        self.tracking = tracking.lower()
        self.latency: Optional[float] = None
        self.latency_label = Label("--- ms", classes="latency-label")

    def compose(self):
        # Final ASCII Privacy symbols with specific prefixes
        if self.tracking == "none":
            privacy_symbol = "[green]#SEC[/green]"
        elif self.tracking == "yes":
            privacy_symbol = "[red]!TRK[/red]"
        elif self.tracking == "limited":
            privacy_symbol = "[yellow]~LIM[/yellow]"
        else:
            privacy_symbol = "[dim]?UNK[/dim]"

        with Container(classes="rpc-row-grid"):
            yield Label(self.url, classes="url-label")
            yield Label(privacy_symbol, classes="privacy-symbol")
            yield self.latency_label

    def update_latency(self, latency_ms: Optional[float]) -> None:
        self.latency = latency_ms
        if latency_ms is None:
            self.latency_label.update("[red]ERR[/red]")
        else:
            color = "#00ff00" if latency_ms < 200 else "#ffff00" if latency_ms < 500 else "#ff0000"
            self.latency_label.update(f"[{color}]{latency_ms:.0f} ms[/{color}]")
