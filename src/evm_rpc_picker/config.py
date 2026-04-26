import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from platformdirs import user_config_dir

class EncryptionManager:
    """Handles encryption and decryption of secrets using user-provided passwords."""
    
    ITERATIONS = 100_000
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive a cryptographic key from a password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=EncryptionManager.ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt(data: str, password: str) -> Tuple[str, str]:
        """Encrypt data with a password. Returns (encrypted_blob_b64, salt_b64)."""
        salt = os.urandom(16)
        key = EncryptionManager.derive_key(password, salt)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        return (
            base64.b64encode(encrypted_data).decode(),
            base64.b64encode(salt).decode()
        )

    @staticmethod
    def decrypt(encrypted_blob_b64: str, salt_b64: str, password: str) -> Optional[str]:
        """Decrypt data with a password and salt. Returns None if decryption fails."""
        try:
            salt = base64.b64decode(salt_b64)
            key = EncryptionManager.derive_key(password, salt)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(base64.b64decode(encrypted_blob_b64))
            return decrypted_data.decode()
        except Exception:
            return None

class ConfigManager:
    """Manages global and local configurations for the EVM RPC Picker."""
    
    APP_NAME = "evm-rpc-picker"
    GLOBAL_CONFIG_DIR = Path(user_config_dir(APP_NAME))
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
    LOCAL_CONFIG_FILE = Path("./.rpc-picker.json")
    
    def __init__(self):
        self.global_config: Dict[str, Any] = self._load_json(self.GLOBAL_CONFIG_FILE)
        self.local_config: Dict[str, Any] = self._load_json(self.LOCAL_CONFIG_FILE)
        
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON from a file, returning an empty dict if not found or invalid."""
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_json(self, path: Path, data: Dict[str, Any]):
        """Save JSON to a file, creating directories if needed."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            # TODO: Log or handle save errors
            pass

    # --- Favorites ---

    def get_favorites(self, project_only: bool = False) -> Set[int]:
        """Get a set of favorite chain IDs from both configs or just local."""
        favorites = set(self.local_config.get("favorites", []))
        if not project_only:
            favorites.update(self.global_config.get("favorites", []))
        return favorites

    def toggle_favorite(self, chain_id: int, is_global: bool = False):
        """Toggle a favorite chain ID in the specified config."""
        config = self.global_config if is_global else self.local_config
        path = self.GLOBAL_CONFIG_FILE if is_global else self.LOCAL_CONFIG_FILE
        
        # If toggling local and it doesn't exist, this might be handled by UI prompt
        # but here we just ensure the list exists.
        favorites = config.get("favorites", [])
        if chain_id in favorites:
            favorites.remove(chain_id)
        else:
            favorites.append(chain_id)
        
        config["favorites"] = favorites
        self._save_json(path, config)

    # --- Secrets ---

    def set_secret(self, key_name: str, secret_value: str):
        """Store a secret value in the system keyring."""
        keyring.set_password(self.APP_NAME, key_name, secret_value)

    def get_secret(self, key_name: str) -> Optional[str]:
        """Retrieve a secret value from the system keyring."""
        return keyring.get_password(self.APP_NAME, key_name)

    def delete_secret(self, key_name: str):
        """Remove a secret from the system keyring."""
        try:
            keyring.delete_password(self.APP_NAME, key_name)
        except keyring.errors.PasswordDeleteError:
            pass

    def save_rpc_secret(self, key_name: str, api_key: str, secret_note: str = "", password: Optional[str] = None):
        """Save API key and secret note to keyring, optionally encrypted with a password."""
        data = {
            "api_key": api_key,
            "secret_note": secret_note,
            "encrypted": password is not None
        }
        
        if password:
            json_str = json.dumps(data)
            blob, salt = EncryptionManager.encrypt(json_str, password)
            storage_data = {
                "blob": blob,
                "salt": salt,
                "encrypted": True
            }
            self.set_secret(key_name, json.dumps(storage_data))
        else:
            self.set_secret(key_name, json.dumps(data))

    def load_rpc_secret(self, key_name: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Load and optionally decrypt RPC secret from keyring."""
        raw_val = self.get_secret(key_name)
        if not raw_val:
            return {}
            
        try:
            data = json.loads(raw_val)
            if data.get("encrypted"):
                if not password:
                    return {"status": "needs_password", "encrypted": True}
                
                decrypted_json = EncryptionManager.decrypt(data["blob"], data["salt"], password)
                if not decrypted_json:
                    return {"status": "wrong_password", "encrypted": True}
                
                result = json.loads(decrypted_json)
                result["status"] = "ok"
                return result
            
            data["status"] = "ok"
            return data
        except Exception:
            return {"status": "error"}

    # --- Custom RPCs ---

    def get_custom_rpcs(self, chain_id: int) -> List[Dict[str, Any]]:
        """Get custom RPCs for a chain from both configs."""
        # Merge global and local custom RPCs
        global_rpcs = self.global_config.get("custom_rpcs", {}).get(str(chain_id), [])
        local_rpcs = self.local_config.get("custom_rpcs", {}).get(str(chain_id), [])
        
        # Tag them for UI differentiation
        for rpc in global_rpcs:
            rpc["source"] = "global"
        for rpc in local_rpcs:
            rpc["source"] = "project"
            
        return local_rpcs + global_rpcs

    def add_custom_rpc(self, chain_id: int, rpc_data: Dict[str, Any], is_global: bool = False):
        """Add a custom RPC to the specified config."""
        config = self.global_config if is_global else self.local_config
        path = self.GLOBAL_CONFIG_FILE if is_global else self.LOCAL_CONFIG_FILE
        
        custom_rpcs = config.get("custom_rpcs", {})
        cid_str = str(chain_id)
        if cid_str not in custom_rpcs:
            custom_rpcs[cid_str] = []
            
        custom_rpcs[cid_str].append(rpc_data)
        config["custom_rpcs"] = custom_rpcs
        self._save_json(path, config)

    def local_config_exists(self) -> bool:
        """Check if local config file exists in CWD."""
        return self.LOCAL_CONFIG_FILE.exists()

    def init_local_config(self):
        """Create an empty local config file."""
        if not self.local_config_exists():
            self._save_json(self.LOCAL_CONFIG_FILE, {"favorites": [], "custom_rpcs": {}})
            self.local_config = self._load_json(self.LOCAL_CONFIG_FILE)
