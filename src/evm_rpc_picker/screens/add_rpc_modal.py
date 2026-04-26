from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, TextArea


class AddRPCModal(ModalScreen[dict]):
    """Modal to add a new custom RPC."""

    DEFAULT_CSS = """
    AddRPCModal {
        align: center middle;
    }

    #add-rpc-container {
        width: 60;
        height: auto;
        background: #1e1e2e;
        border: thick #89b4fa;
        padding: 1 2;
    }

    .field-label {
        margin-top: 1;
        color: #6c7086;
    }

    Input {
        margin-bottom: 1;
        background: #181825;
        border: solid #313244;
    }

    Input:focus, TextArea:focus {
        border: solid #89b4fa;
    }

    TextArea {
        height: 3;
        background: #181825;
        border: solid #313244;
    }

    Checkbox {
        margin: 1 0;
    }

    #button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, initial_url: str = ""):
        super().__init__()
        self.initial_url = initial_url

    def compose(self) -> ComposeResult:
        with Vertical(id="add-rpc-container"):
            yield Label("[bold #cdd6f4]Add Custom RPC[/bold #cdd6f4]")

            yield Label("RPC URL", classes="field-label")
            yield Input(self.initial_url, placeholder="https://...", id="url-input")

            yield Label("Label (Optional)", classes="field-label")
            yield Input(placeholder="My Private Node", id="label-input")

            yield Label("Public Note", classes="field-label")
            yield TextArea(id="note-input")

            yield Label("Secret Note (Keyring)", classes="field-label")
            yield TextArea(id="secret-note-input")

            yield Checkbox("Encrypt with password?", id="encrypt-check")

            yield Label("Password (only if Encrypt is checked)", classes="field-label")
            yield Input(password=True, id="password-input")

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Save", variant="success", id="save")

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def on_save(self) -> None:
        url = self.query_one("#url-input", Input).value
        if not url:
            self.app.notify("URL is required", severity="error")
            return

        data = {
            "url": url,
            "label": self.query_one("#label-input", Input).value,
            "note": self.query_one("#note-input", TextArea).text,
            "secret_note": self.query_one("#secret-note-input", TextArea).text,
            "encrypt": self.query_one("#encrypt-check", Checkbox).value,
            "password": self.query_one("#password-input", Input).value,
        }
        self.dismiss(data)
