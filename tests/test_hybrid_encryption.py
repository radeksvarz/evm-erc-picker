from unittest.mock import patch

import pytest

from evm_rpc_picker.config import ConfigManager


@pytest.fixture
def temp_config(tmp_path):
    """Fixture to mock config paths and return a ConfigManager instance."""
    global_dir = tmp_path / "global"
    global_dir.mkdir()
    local_file = tmp_path / "local" / ".rpc-picker.toml"
    local_file.parent.mkdir()

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


def test_add_custom_rpc_encrypted(temp_config):
    cm, _, _ = temp_config

    with patch("keyring.set_password") as mock_set:
        cm.add_custom_rpc(
            chain_id=1337,
            rpc_data={
                "url": "https://eth-mainnet.alchemy.com/v2/mysecretkey",
                "name": "Alchemy",
                "note": "Private Node",
                "encrypt": True,
                "password": "superpassword",
            },
            is_global=True,
        )
        mock_set.assert_called_once()
        args, _ = mock_set.call_args
        assert args[1] == cm.get_custom_rpcs(1337)[0]["id"]
        assert args[2] == "superpassword"

    custom_rpcs = cm.get_custom_rpcs(1337)
    assert len(custom_rpcs) == 1
    rpc = custom_rpcs[0]
    assert rpc["name"] == "Alchemy"
    assert rpc["url"] == ""  # Empty string in config URL
    assert rpc["note"] == ""  # Empty string in config Note
    assert rpc["rpc_password_protected"] is True

    # The encrypted blobs must be written in config
    assert "url_encrypted" in rpc
    assert "note_encrypted" in rpc


def test_update_custom_rpc_encrypted(temp_config):
    cm, _, _ = temp_config

    cm.add_custom_rpc(
        chain_id=1,
        rpc_data={
            "url": "http://localhost:8545",
            "name": "LocalNode",
            "note": "Initial Note",
        },
        is_global=False,
    )

    rpc_id = cm.get_custom_rpcs(1)[0]["id"]

    with patch("keyring.set_password") as mock_set:
        cm.update_custom_rpc(
            chain_id=1,
            rpc_id=rpc_id,
            rpc_data={
                "url": "https://mainnet.infura.io/v3/infurakey",
                "name": "Infura Node",
                "note": "Encrypted Note",
                "encrypt": True,
                "password": "infurapassword",
            },
            is_global=False,
        )
        mock_set.assert_called_once()
        args, _ = mock_set.call_args
        assert args[1] == rpc_id
        assert args[2] == "infurapassword"

    custom_rpcs = cm.get_custom_rpcs(1)
    rpc = custom_rpcs[0]
    assert rpc["name"] == "Infura Node"
    assert rpc["url"] == ""
    assert rpc["note"] == ""
    assert rpc["rpc_password_protected"] is True


def test_load_rpc_secret_hybrid(temp_config):
    cm, _, _ = temp_config

    with patch("keyring.set_password"):
        cm.add_custom_rpc(
            chain_id=1337,
            rpc_data={
                "url": "https://super-secure-rpc.com/api",
                "name": "Secure",
                "note": "Confidential",
                "encrypt": True,
                "password": "masterpassword",
            },
            is_global=True,
        )

    rpc_id = cm.get_custom_rpcs(1337)[0]["id"]

    # 1. No password, keyring does not have it -> Needs password
    with patch("keyring.get_password", return_value=None):
        res = cm.load_rpc_secret(rpc_id)
        assert res["status"] == "needs_password"
        assert res["encrypted"] is True

    # 2. Keyring has correct password -> Quiet Zero-Prompt Unlock
    with patch("keyring.get_password", return_value="masterpassword"):
        res = cm.load_rpc_secret(rpc_id)
        assert res["status"] == "ok"
        assert res["url"] == "https://super-secure-rpc.com/api"
        assert res["secret_note"] == "Confidential"

    # 3. Wrong password provided manually
    with patch("keyring.get_password", return_value=None):
        res = cm.load_rpc_secret(rpc_id, password="wrongpassword")
        assert res["status"] == "wrong_password"

    # 4. Correct password provided manually -> Decrypts and saves to keyring
    with (
        patch("keyring.get_password", return_value=None),
        patch("keyring.set_password") as mock_set,
    ):
        res = cm.load_rpc_secret(rpc_id, password="masterpassword")
        assert res["status"] == "ok"
        assert res["url"] == "https://super-secure-rpc.com/api"
        assert res["secret_note"] == "Confidential"
        mock_set.assert_called_once_with("evm-rpc-picker", rpc_id, "masterpassword")


def test_favorites_reference_format(temp_config):
    cm, _, _ = temp_config

    with patch("keyring.set_password"):
        cm.add_custom_rpc(
            chain_id=1,
            rpc_data={
                "url": "http://localhost:8545",
                "name": "LocalNode",
                "note": "Anvil Node",
                "encrypt": True,
                "password": "mypassword",
            },
            is_global=True,
        )

    rpc_id = cm.get_custom_rpcs(1)[0]["id"]

    # Toggling global favorite for the custom password-protected RPC
    # should toggle "secret:rpc_id" reference
    cm.toggle_favorite_rpc(f"secret:{rpc_id}", is_global=True)
    fav_global = cm.global_config.get("favorite_rpcs", [])
    assert f"secret:{rpc_id}" in fav_global
    assert "http://localhost:8545" not in fav_global

    # Untoggle
    cm.toggle_favorite_rpc(f"secret:{rpc_id}", is_global=True)
    fav_global = cm.global_config.get("favorite_rpcs", [])
    assert f"secret:{rpc_id}" not in fav_global
