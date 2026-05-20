# EVM RPC Picker

A powerful TUI (Terminal User Interface) tool to search for EVM chains and manage your RPC URLs securely. It helps you quickly select and set the `ETH_RPC_URL` environment variable with the fastest available RPC, whether it's public, private, or project-specific.

## Features

-   **Instant Search**: Filter over 1000+ chains by name or Chain ID.
-   **Latency Checks**: Real-time ping (using `eth_blockNumber`) to find the most responsive RPC.
-   **Custom RPC Management**: Add, edit, and manage your own RPC endpoints for any chain.
-   **Secure Storage**: Encrypt sensitive RPC URLs and store API keys securely in your system's **Keyring**.
-   **Smart Context Detection**: Automatically detects networks and URLs defined in your `foundry.toml` or `hardhat.config.js`.
-   **Favorites System**:
    *   **Project Level**: Store favorites in `.rpc-picker.toml` within your repository.
    *   **Global Level**: Store favorites in your global user config.
    *   **Favorite RPCs**: Bookmark both public chains and your own custom RPCs to easily access and test them from a dedicated unified dashboard.
-   **Filtering**: 
    *   Toggle between **Mainnet**, **Testnet**, or **All**.
    *   Quickly filter to show only your **Favorite** chains.
-   **Notes**: Attach notes to your custom RPCs — stored as plain text (public) or AES-encrypted and portable inside the config file (private, when password-protected).
-   **Sensitive Mode**: Toggle `Ctrl + S` to instantly mask all sensitive URLs and notes for screen sharing or streaming. Also available via `--privacy` / `-p` CLI flag.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
# Run directly without installation
uvx evm-rpc-picker
```

## Shell Integration

Add the following function to your `.bashrc` or `.zshrc` to easily export the selected RPC:

```bash
pick-rpc() {
    local rpc=$(uvx evm-rpc-picker)
    [ -n "$rpc" ] && export ETH_RPC_URL="$rpc"
}
```

After restarting your shell, simply run `pick-rpc`.

## Python Usage

You can also use `evm-rpc-picker` as a module in your own Python scripts:

```python
from evm_rpc_picker import pick_rpc

# This will open the TUI
rpc_url = pick_rpc()

if rpc_url:
    print(f"Selected RPC: {rpc_url}")
```

## Keyboard Shortcuts

### Main Screen
| Key | Action |
|-----|--------|
| `Tab` | **Switch Focus** (Table ↔ Personal RPCs ↔ Env Status) |
| `Enter` | **Select** highlighted chain to see RPCs |
| `Ctrl + F` | **Filter Favorites** toggle |
| `Ctrl + T` | **Filter Network Type** (All ↔ Mainnet ↔ Testnet) |
| `Ctrl + L` | **Toggle Local Favorite** (Project level) |
| `Ctrl + G` | **Toggle Global Favorite** (Global level) |
| `Ctrl + R` | **Refresh** chain data from network |
| `Ctrl + E` | **Use Current ETH_RPC_URL** (select current ENV and exit) |
| `Ctrl + U` | **Personal RPC URLs** (manage and select custom endpoints) |
| `Ctrl + B` | **Favorite RPCs** (view all bookmarked public and custom endpoints) |
| `Ctrl + S` | **Toggle Sensitive Mode** (mask all URLs and notes for screen sharing) |

### Chainlist.org chain's RPC Selection Screen
| Key | Action |
|-----|--------|
| `Enter` | **Select** RPC and exit |
| `Esc` | **Back** to main screen |
| `Ctrl + R` | **Refresh** latencies |
| `Ctrl + L` | **Toggle Local Favorite** (Project level) |
| `Ctrl + G` | **Toggle Global Favorite** (Global level) |

### Personal RPC URLs Screen
| Key | Action |
|-----|--------|
| `Enter` | **Select** RPC and exit |
| `Esc` | **Back** to main screen |
| `a` | **Add** custom RPC |
| `e` | **Edit** highlighted RPC |
| `Delete` | **Delete** highlighted RPC |
| `Ctrl + V` | **Paste & Add** (paste URL from clipboard into Add RPC modal) |
| `Ctrl + B` | **Toggle Favorite** (bookmark/unbookmark the selected custom RPC) |

### Favorite RPCs Screen
| Key | Action |
|-----|--------|
| `Enter` | **Select** RPC and exit |
| `Esc` | **Back** to main screen |
| `Ctrl + R` | **Refresh** latencies |
| `Ctrl + L` | **Toggle Local Favorite** (Project level) |
| `Ctrl + G` | **Toggle Global Favorite** (Global level) |

### Add/Edit Custom RPC Modal
| Key | Action |
|-----|--------|
| `Ctrl + S` | **Save** changes (when editing) |
| `Ctrl + G` | **Add Globally** (when adding) |
| `Ctrl + L` | **Add Locally** (when adding) |
| `Esc` | **Cancel** |

## Sensitive Mode (Streamer / Over-Shoulder Protection)

Sensitive Mode lets you instantly hide all sensitive RPC URLs and notes without closing the application — useful when sharing your screen, streaming, or recording.

### Activation

| Method | Command |
|--------|---------|
| **Runtime toggle** | `Ctrl + S` on the main screen |
| **CLI flag** | `evm-rpc-picker --privacy` or `evm-rpc-picker -p` |

### What gets masked

| Element | Normal display | Sensitive Mode |
|---------|---------------|----------------|
| URL with API key | `https://mainnet.infura.io/v3/mykey` | `https://mainnet.infura.io/••••••••` |
| URL with credentials | `https://user:pass@rpc.example.com/key` | `https://••••••••@rpc.example.com/••••••••` |
| RPC note | `my personal note` | `••••••••` |

The **host/domain** remains visible so you can still identify the provider. When Sensitive Mode is active, the header subtitle changes to **`[🙈] Sensitive Mode`** (displayed in red).

> **Note**: Sensitive Mode is display-only. Selecting an RPC still returns the real URL to the shell.

## Configuration

-   **Global Config**: `~/.config/evm-rpc-picker/config.toml`
-   **Project Config**: `.rpc-picker.toml` in your project root.
-   **Cache**: Data from `chainlist.org` is cached for 24 hours in `~/.cache/evm-rpc-picker/chains.json`.

## Secure storage

### Security and Encryption

- All sensitive API keys are securely stored in the system keyring (macOS Keychain, Windows Vault, Linux Secret Service).
- API keys must never be stored in plain text within configuration TOML files (use placeholder `{{secret:key-name}}`).
- **Encrypted & Portable Notes**:
  - Each custom RPC has a single **Note** field.
  - If a custom RPC is **not** password-protected, the note is saved as plain text in the TOML configuration (`note` field).
  - If a custom RPC **is** password-protected, both the URL and the note are securely **encrypted** using AES with the user's password and stored directly in the TOML configuration (`note_encrypted` field). This ensures sensitive notes remain private while making the project configuration fully portable between machines.
- Each password-protected custom RPC is indicated by the `rpc_password_protected` flag in the configuration and a lock icon `[🔒]` in front of the URL.
- If the keyring/password is unlocked, the app automatically measures latency for protected RPCs.

### Detailed Screen (Personal RPCs)

- Lock icon `[🔒]` in front of the URL indicates password-protected RPCs.
- If an RPC is password-protected, the app prompts for the password when you select or edit it.
- A `[🔒] Locked` label in the **Note** column indicates that the note is securely encrypted and requires the password to be decrypted and viewed.

## Development

```bash
git clone https://github.com/radeksvarz/evm-rpc-picker.git
cd evm-rpc-picker
uv sync

# Run normally
uv run evm-rpc-picker
```

### Hot Reloading (TUI Development)

For TUI development with hot reloading, open two terminals.

Terminal 1 (Console output):
```bash
uv run textual console
```

Terminal 2 (App with hot reload):
```bash
uv run textual run --dev evm_rpc_picker.tui:ChainRPCPicker
```

---

Created with 🍻 by **BeerFi Prague** web3 builders community | [Source and updates](https://github.com/radeksvarz/evm-rpc-picker)

