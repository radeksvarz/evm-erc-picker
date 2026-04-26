import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import keyring
from evm_rpc_picker.config import ConfigManager, EncryptionManager

@pytest.fixture
def temp_config(tmp_path):
    """Fixture to mock config paths and return a ConfigManager instance."""
    global_dir = tmp_path / "global"
    local_file = tmp_path / "local" / ".rpc-picker.json"
    local_file.parent.mkdir()
    
    # We need to patch the class attributes and the platformdirs call
    with patch("evm_rpc_picker.config.user_config_dir", return_value=str(global_dir)), \
         patch("evm_rpc_picker.config.ConfigManager.LOCAL_CONFIG_FILE", local_file), \
         patch("evm_rpc_picker.config.ConfigManager.GLOBAL_CONFIG_FILE", global_dir / "config.json"):
        cm = ConfigManager()
        yield cm, global_dir, local_file

def test_load_save_json(temp_config):
    cm, global_dir, local_file = temp_config
    
    # Test saving and loading
    data = {"test": 123}
    test_path = global_dir / "test.json"
    cm._save_json(test_path, data)
    assert cm._load_json(test_path) == data
    
    # Test loading non-existent
    assert cm._load_json(global_dir / "missing.json") == {}
    
    # Test invalid JSON
    invalid_file = global_dir / "invalid.json"
    invalid_file.write_text("invalid json")
    assert cm._load_json(invalid_file) == {}

def test_favorites(temp_config):
    cm, _, _ = temp_config
    
    # Global toggle
    cm.toggle_favorite(1, is_global=True)
    assert 1 in cm.get_favorites()
    assert 1 in cm.get_favorites(project_only=False)
    assert 1 not in cm.get_favorites(project_only=True)
    
    # Local toggle
    cm.toggle_favorite(137, is_global=False)
    assert 137 in cm.get_favorites()
    assert 137 in cm.get_favorites(project_only=True)
    
    # Untoggle
    cm.toggle_favorite(1, is_global=True)
    assert 1 not in cm.get_favorites()

def test_keyring_integration(temp_config):
    cm, _, _ = temp_config
    
    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password", return_value="secret") as mock_get, \
         patch("keyring.delete_password") as mock_del:
        
        cm.set_secret("k", "v")
        mock_set.assert_called_once_with(cm.APP_NAME, "k", "v")
        
        assert cm.get_secret("k") == "secret"
        mock_get.assert_called_once_with(cm.APP_NAME, "k")
        
        cm.delete_secret("k")
        mock_del.assert_called_once_with(cm.APP_NAME, "k")
        
        # Test delete error
        mock_del.side_effect = keyring.errors.PasswordDeleteError("Error")
        cm.delete_secret("k") # Should not raise

def test_encryption_manager():
    password = "pass"
    data = "my-api-key"
    
    blob, salt = EncryptionManager.encrypt(data, password)
    assert blob != data
    
    decrypted = EncryptionManager.decrypt(blob, salt, password)
    assert decrypted == data
    
    # Wrong password
    assert EncryptionManager.decrypt(blob, salt, "wrong") is None
    
    # Invalid blob
    assert EncryptionManager.decrypt("invalid", salt, password) is None
    
    # Invalid salt
    assert EncryptionManager.decrypt(blob, "invalid_salt", password) is None

def test_rpc_secrets(temp_config):
    cm, _, _ = temp_config
    
    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password") as mock_get:
        
        # 1. Standard (not encrypted)
        cm.save_rpc_secret("rpc1", "key1", "note1")
        args, _ = mock_set.call_args
        saved_data = json.loads(args[2])
        assert saved_data["api_key"] == "key1"
        assert not saved_data["encrypted"]
        
        mock_get.return_value = json.dumps(saved_data)
        loaded = cm.load_rpc_secret("rpc1")
        assert loaded["api_key"] == "key1"
        assert loaded["status"] == "ok"
        
        # 2. Encrypted
        cm.save_rpc_secret("rpc2", "key2", "note2", password="p")
        args, _ = mock_set.call_args
        storage_data = json.loads(args[2])
        assert storage_data["encrypted"]
        
        # Load without password
        mock_get.return_value = json.dumps(storage_data)
        loaded = cm.load_rpc_secret("rpc2")
        assert loaded["status"] == "needs_password"
        
        # Load with correct password
        loaded = cm.load_rpc_secret("rpc2", password="p")
        assert loaded["api_key"] == "key2"
        assert loaded["secret_note"] == "note2"
        assert loaded["status"] == "ok"
        
        # Load with wrong password
        loaded = cm.load_rpc_secret("rpc2", password="wrong")
        assert loaded["status"] == "wrong_password"
        
        # Load missing
        mock_get.return_value = None
        assert cm.load_rpc_secret("missing") == {}
        
        # Load invalid json in keyring
        mock_get.return_value = "invalid"
        assert cm.load_rpc_secret("invalid") == {"status": "error"}

def test_custom_rpcs(temp_config):
    cm, _, _ = temp_config
    
    rpc = {"name": "test"}
    cm.add_custom_rpc(1, rpc, is_global=True)
    cm.add_custom_rpc(1, {"name": "local"}, is_global=False)
    
    rpcs = cm.get_custom_rpcs(1)
    assert len(rpcs) == 2
    # One from global, one from project
    assert any(r.get("source") == "global" for r in rpcs)
    assert any(r.get("source") == "project" for r in rpcs)

def test_local_init(temp_config):
    cm, _, local_file = temp_config
    
    if local_file.exists():
        local_file.unlink()
        
    assert not cm.local_config_exists()
    cm.init_local_config()
    assert cm.local_config_exists()
    
    # Double init should do nothing (already exists)
    cm.init_local_config()
    assert cm.local_config_exists()

def test_save_error(temp_config):
    cm, _, _ = temp_config
    # Mock open to raise IOError to test exception handling in _save_json
    with patch("builtins.open", side_effect=IOError):
        cm._save_json(Path("any_path"), {"data": 1})
        # Should complete without raising
