# Requirements: Favorites & Secure RPC Management

This document serves as the formal assignment for implementing "Favorites", "Projects", and "Secure RPC Management" features in the `evm-rpc-picker` tool.

## 1. Project Concept and Layered Configuration
The application must support layered configuration loading:
- **Global Config:** `~/.config/evm-rpc-picker/config.toml` (universal favorites and custom RPCs).
- **Local Config:** `./.rpc-picker.toml` (specific to the current directory/project).
- **Auto-detection:** Detection of `foundry.toml` or `hardhat.config.js` to automatically load local chains and RPCs.

## 2. Main Screen (Chains)
- **Visuals:**
    - Star indicator `*` to the left of the chain name for favorites.
    - Tag `[P]` (Project) for chains found in the local config or via Foundry/Hardhat.
- **Interactions:**
    - `Space`: Toggles favorite in the local `.rpc-picker.toml`. If the file does not exist, the app prompts to create it.
    - `Shift+Space`: Toggles favorite in the global config.
    - `CTRL+T`: Enhanced filter cycle: `All -> Mainnets -> Testnets -> Favorites`.

## 3. Detailed Screen (RPCs)
- **Visuals:**
    - Source differentiation using tags `[P]` (Project) and `[G]` (Global).
    - Display of public notes (`Note`).
    - Lock icon `[🔒]` for password-protected RPCs.
- **Interactions:**
    - `Space` / `Shift+Space`: Toggle favorite RPC (Local / Global).
    - `CTRL+V`: Modal for adding a new RPC (Smart Paste with API key detection).
    - `CTRL+E`: Edit custom RPC.
    - `Enter`: Select RPC (if password-protected, the app prompts for the password at this moment).

## 4. Security and Encryption
- **System Keyring:** All sensitive data (API keys, Secret Notes) are stored in the system keyring (macOS Keychain, Windows Vault, Linux Secret Service).
- **Per-RPC Password:** Each custom RPC can optionally have its own password for additional encryption (AES) within the keyring.
- **Notes:**
    - `Note` (Public): Saved in TOML, portable between machines.
    - `Secret Note` (Private): Saved in the keyring.

## 5. Implementation Rules
- If the keyring is unlocked, the app automatically measures latency even for private RPCs.
- API keys must never be stored in plain text within configuration TOML files (use placeholder `{{secret:key-name}}`).
