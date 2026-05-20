"""Tests for utils/privacy.py – 100% branch coverage."""

from evm_rpc_picker.utils.privacy import mask_url


class TestMaskUrlEmpty:
    """Edge cases for empty / blank inputs."""

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert mask_url("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string is stripped and treated as empty (no scheme)."""
        assert mask_url("   ") == "••••••••"


class TestMaskUrlNoScheme:
    """URLs without a :// separator should be fully masked."""

    def test_bare_hostname(self) -> None:
        assert mask_url("localhost") == "••••••••"

    def test_just_path(self) -> None:
        assert mask_url("/some/path") == "••••••••"


class TestMaskUrlNoPath:
    """URLs with scheme + host but no path should keep scheme://host."""

    def test_http_localhost_no_path(self) -> None:
        assert mask_url("http://localhost:8545") == "http://localhost:8545"

    def test_https_host_no_path(self) -> None:
        assert mask_url("https://mainnet.example.com") == "https://mainnet.example.com"

    def test_trailing_slash_only(self) -> None:
        """A trailing slash with no path after it counts as empty path – no masking needed."""
        assert mask_url("https://host.example.com/") == "https://host.example.com"


class TestMaskUrlWithPath:
    """URLs with a scheme, host, and non-empty path should mask the path."""

    def test_infura_v3_key(self) -> None:
        assert (
            mask_url("https://mainnet.infura.io/v3/secretkey")
            == "https://mainnet.infura.io/••••••••"
        )

    def test_alchemy_key(self) -> None:
        assert (
            mask_url("https://eth-mainnet.alchemyapi.io/v2/myapikey")
            == "https://eth-mainnet.alchemyapi.io/••••••••"
        )

    def test_generic_path(self) -> None:
        assert mask_url("https://rpc.example.com/apitoken") == "https://rpc.example.com/••••••••"

    def test_deep_path(self) -> None:
        """Only the first path segment boundary matters – full path is masked."""
        assert mask_url("https://host.io/v3/key/extra/segments") == "https://host.io/••••••••"

    def test_ws_scheme(self) -> None:
        assert mask_url("wss://mainnet.infura.io/ws/v3/key") == "wss://mainnet.infura.io/••••••••"


class TestMaskUrlWithCredentials:
    """URLs with user:password@ in the authority should mask the credentials."""

    def test_user_password_with_path(self) -> None:
        assert (
            mask_url("https://user:password@server.example.com/apikey")
            == "https://••••••••@server.example.com/••••••••"
        )

    def test_user_password_no_path(self) -> None:
        assert mask_url("https://user:secret@rpc.example.com") == "https://••••••••@rpc.example.com"

    def test_user_only_at_sign(self) -> None:
        """Only a username (no colon) before @ sign."""
        assert (
            mask_url("https://token@rpc.example.com/path")
            == "https://••••••••@rpc.example.com/••••••••"
        )

    def test_http_credentials(self) -> None:
        assert (
            mask_url("http://admin:pass@192.168.1.1:8545/rpc")
            == "http://••••••••@192.168.1.1:8545/••••••••"
        )
