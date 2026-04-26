import json
from pathlib import Path
from unittest.mock import patch

import pytest
import keyring
from evm_rpc_picker.config import ConfigManager, EncryptionManager


@pytest.fixture
def temp_config(tmp_path):
    """Fixture to mock config paths and return a ConfigManager instance."""
    global_dir = tmp_path / "global"
    local_file = tmp_path / "local" / ".rpc-picker.toml"
    local_file.parent.mkdir()

    # We need to patch the class attributes and the platformdirs call
    with (
        patch("evm_rpc_picker.config.user_config_dir", return_value=str(global_dir)),
        patch("evm_rpc_picker.config.ConfigManager.LOCAL_CONFIG_FILE", local_file),
        patch(
            "evm_rpc_picker.config.ConfigManager.GLOBAL_CONFIG_FILE",
            global_dir / "config.toml",
        ),
    ):
        cm = ConfigManager()
        yield cm, global_dir, local_file


def test_load_save_toml(temp_config):
    cm, global_dir, _ = temp_config

    # Test saving and loading
    data = {"test": 123, "note": "Multi\nLine"}
    test_path = global_dir / "test.toml"
    cm._save_toml(test_path, data)
    loaded = cm._load_toml(test_path)
    assert loaded["test"] == 123
    assert loaded["note"] == "Multi\nLine"

    # Test loading non-existent
    assert cm._load_toml(global_dir / "missing.toml") == {}

    # Test invalid TOML
    invalid_file = global_dir / "invalid.toml"
    invalid_file.write_text("invalid = [")
    assert cm._load_toml(invalid_file) == {}


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

    with (
        patch("keyring.set_password") as mock_set,
        patch("keyring.get_password", return_value="secret") as mock_get,
        patch("keyring.delete_password") as mock_del,
    ):
        cm.set_secret("k", "v")
        mock_set.assert_called_once_with(cm.APP_NAME, "k", "v")

        assert cm.get_secret("k") == "secret"
        mock_get.assert_called_once_with(cm.APP_NAME, "k")

        cm.delete_secret("k")
        mock_del.assert_called_once_with(cm.APP_NAME, "k")

        # Test delete error
        mock_del.side_effect = keyring.errors.PasswordDeleteError("Error")
        cm.delete_secret("k")  # Should not raise


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

    with (
        patch("keyring.set_password") as mock_set,
        patch("keyring.get_password") as mock_get,
    ):
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


def test_smart_extract_key():
    # Infura v3
    url = "https://mainnet.infura.io/v3/abc123"
    base, key = ConfigManager.smart_extract_key(url)
    assert base == "https://mainnet.infura.io/v3/${API_KEY}"
    assert key == "abc123"

    # Alchemy v2
    url = "https://eth-mainnet.g.alchemy.com/v2/key456"
    base, key = ConfigManager.smart_extract_key(url)
    assert base == "https://eth-mainnet.g.alchemy.com/v2/${API_KEY}"
    assert key == "key456"

    # Generic
    url = "https://rpc.ankr.com/eth"
    base, key = ConfigManager.smart_extract_key(url)
    assert base == url
    assert key == ""


def test_add_custom_rpc_public(temp_config):
    cm, _, _ = temp_config
    rpc_data = {"url": "https://rpc.example.com", "label": "Test RPC", "note": "Public"}
    cm.add_custom_rpc(1, rpc_data, is_global=True)

    custom = cm.get_custom_rpcs(1)
    assert len(custom) == 1
    assert custom[0]["url"] == "https://rpc.example.com"
    assert custom[0]["label"] == "Test RPC"
    assert custom[0]["has_secrets"] is False
    assert cm.global_config["custom_rpcs"]["1"][0]["url"] == "https://rpc.example.com"


def test_add_custom_rpc_with_secrets(temp_config):
    cm, _, _ = temp_config
    rpc_data = {
        "url": "https://mainnet.infura.io/v3/secret123",
        "label": "Secure RPC",
        "secret_note": "My secret note",
    }
    # Mock keyring to avoid system calls
    with patch("keyring.set_password") as mock_set:
        cm.add_custom_rpc(1, rpc_data, is_global=False)

        # Verify public part
        custom = cm.get_custom_rpcs(1)
        assert len(custom) == 1
        assert custom[0]["url"] == "https://mainnet.infura.io/v3/${API_KEY}"
        assert custom[0]["has_secrets"] is True
        assert custom[0]["source"] == "project"

        # Verify secret part was called
        mock_set.assert_called_once()


def test_local_init(temp_config):
    cm, _, local_file = temp_config

    if local_file.exists():
        local_file.unlink()

    assert not cm.local_config_exists()
    cm.init_local_config()
    assert cm.local_config_exists()

    # Check that it's TOML and has comments
    content = local_file.read_text()
    assert "[favorites]" in content or "favorites =" in content
    assert "EVM RPC Picker" in content  # From comment

    # Double init should do nothing (already exists)
    cm.init_local_config()
    assert cm.local_config_exists()


def test_toml_errors(temp_config, tmp_path):
    cm, _, local_file = temp_config

    # Invalid TOML
    local_file.write_text("invalid = [")
    assert cm._load_toml(local_file) == {}

    # Save error (IOError)
    with patch("builtins.open", side_effect=IOError):
        # We use path.write_text which calls open
        with patch("pathlib.Path.write_text", side_effect=IOError):
            cm._save_toml(local_file, {"a": 1})
            # Should not raise


def test_save_toml_error(temp_config):
    cm, _, _ = temp_config
    with patch("pathlib.Path.write_text", side_effect=IOError):
        cm._save_toml(Path("any_path"), {"data": 1})
