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

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(self.message, id="modal-message")
            with Horizontal(id="button-container"):
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="error", id="no")

    @on(Button.Pressed, "#yes")
    def on_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def on_no(self) -> None:
        self.dismiss(False)
