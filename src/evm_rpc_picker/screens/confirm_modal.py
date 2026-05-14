from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmModal(ModalScreen[bool]):
    """A simple modal screen to confirm an action."""

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }

    #modal-container {
        width: 50;
        height: auto;
        background: #1e1e2e;
        border: thick #89b4fa;
        padding: 1 2;
    }

    #modal-message {
        width: 1fr;
        content-align: center middle;
        margin-bottom: 1;
        color: #cdd6f4;
    }

    #button-container {
        width: 1fr;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "no", "Cancel"),
    ]

    def __init__(self, message: str, yes_label: str = "Yes", no_label: str = "No"):
        super().__init__()
        self.message = message
        self.yes_label = yes_label
        self.no_label = no_label

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(self.message, id="modal-message")
            with Horizontal(id="button-container"):
                yield Button(self.yes_label, variant="primary", id="yes")
                yield Button(self.no_label, variant="error", id="no")

    def action_no(self) -> None:
        """Action for No/Cancel."""
        self.dismiss(False)

    @on(Button.Pressed, "#yes")
    def on_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def on_no(self) -> None:
        self.action_no()
