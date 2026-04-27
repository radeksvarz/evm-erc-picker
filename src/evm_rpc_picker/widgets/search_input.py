"""Custom search input widget with specialized focus handling."""

from textual.widgets import Input


class SearchInput(Input):
    """Input widget for searching chains with custom focus behavior."""

    BINDINGS = [
        ("enter", "submit", "Select"),
        ("escape", "app.quit", "Exit"),
        ("ctrl+r", "app.load_data", "Refresh Data"),
        ("ctrl+t", "app.toggle_filter", "Toggle Filter"),
    ]

    def on_focus(self) -> None:
        # Clear selection after focus logic has run
        def clear_selection() -> None:
            self.selection = self.selection.__class__(len(self.value), len(self.value))
            self.cursor_position = len(self.value)

        self.call_after_refresh(clear_selection)

    def on_focus(self) -> None:
        # Clear selection after focus logic has run
        def clear_selection() -> None:
            self.selection = self.selection.__class__(len(self.value), len(self.value))
            self.cursor_position = len(self.value)

        self.call_after_refresh(clear_selection)
