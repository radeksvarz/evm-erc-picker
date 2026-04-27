from textual.widgets import DataTable
from textual.binding import Binding

class ChainsTable(DataTable):
    """Custom table for displaying chains."""
    
    BINDINGS = [
        Binding("home", "action_scroll_home", "Top", show=False),
        Binding("end", "action_scroll_end", "Bottom", show=False),
        Binding("enter", "select_cursor", "Select", tooltip="Select the highlighted chain"),
        Binding("escape", "app.quit", "Cancel", tooltip="Quit the RPC picker"),
        Binding("ctrl+l", "screen.toggle_favorite", "Fav (Local)", tooltip="Add/remove from local project favorites"),
        Binding("ctrl+g", "screen.toggle_global_favorite", "Fav (Global)", tooltip="Add/remove from global favorites"),
    ]
