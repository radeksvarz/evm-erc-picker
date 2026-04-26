import pytest
from evm_rpc_picker.encryption import EncryptionManager


def test_encryption_decryption_cycle():
    password = "secret-password"
    data = "sensitive-data"
    
    # Encrypt
    encrypted_blob, salt = EncryptionManager.encrypt(data, password)
    assert encrypted_blob != data
    assert salt is not None
    
    # Decrypt
    decrypted = EncryptionManager.decrypt(encrypted_blob, salt, password)
    assert decrypted == data


def test_decryption_with_wrong_password():
    password = "secret-password"
    wrong_password = "wrong-password"
    data = "sensitive-data"
    
    encrypted_blob, salt = EncryptionManager.encrypt(data, password)
    
    # Decrypt with wrong password should return None
    decrypted = EncryptionManager.decrypt(encrypted_blob, salt, wrong_password)
    assert decrypted is None


def test_decryption_with_invalid_data():
    password = "secret-password"
    salt = "invalid-salt"
    encrypted_blob = "invalid-blob"
    
    # Should return None instead of raising exception
    decrypted = EncryptionManager.decrypt(encrypted_blob, salt, password)
    assert decrypted is None


def test_derive_key_consistency():
    password = "test"
    salt = b"static-salt-16bytes"
    
    key1 = EncryptionManager.derive_key(password, salt)
    key2 = EncryptionManager.derive_key(password, salt)
    
    assert key1 == key2
    assert isinstance(key1, bytes)
