"""Main entry point for the EVM RPC Picker CLI."""

import argparse

from evm_rpc_picker.tui import ChainRPCPicker


def print_init_snippet() -> None:
    """Print the shell initialization snippet for the user's .bashrc/.zshrc."""
    snippet = """
rpc-set() {
    local rpc=$(uvx evm-rpc-picker)
    if [ -n "$rpc" ]; then
        export ETH_RPC_URL="$rpc"
    fi
}
"""
    print(snippet.strip())


def run_picker_tui(privacy: bool) -> str | None:
    """Run the TUI with proper terminal/stdout redirection handling if needed."""
    import os
    import sys

    # If stdout is not a TTY (redirected/piped) but stderr IS a TTY,
    # we redirect stdout to stderr during the TUI execution to ensure
    # the TUI renders full-screen on stderr, and then restore stdout
    # to print the final result.
    orig_stdout = sys.stdout
    orig_get_terminal_size = os.get_terminal_size
    stdout_redirected = not sys.stdout.isatty() and sys.stderr.isatty()

    if stdout_redirected:
        sys.stdout = sys.stderr

        # Intercept terminal size queries to use stderr's file descriptor
        def patched_get_terminal_size(fd=None):
            if fd is None or fd == 1 or fd == sys.stdout or fd == sys.__stdout__:
                try:
                    return orig_get_terminal_size(sys.stderr.fileno())
                except OSError:
                    pass
            try:
                if fd is not None:
                    return orig_get_terminal_size(fd)
                return orig_get_terminal_size()
            except OSError:
                return os.terminal_size((80, 24))

        os.get_terminal_size = patched_get_terminal_size

    try:
        app = ChainRPCPicker(privacy=privacy)
        # Run the app. The app.exit(result) call will return 'result' here.
        return app.run()
    finally:
        if stdout_redirected:
            sys.stdout = orig_stdout
            os.get_terminal_size = orig_get_terminal_size


def main() -> None:
    """Parse CLI arguments and run the application."""
    parser = argparse.ArgumentParser(description="EVM RPC Picker - TUI tool to select EVM RPC URLs")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Print shell initialization snippet for Bash/Zsh",
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear the local chain data cache"
    )
    parser.add_argument(
        "--privacy",
        "-p",
        action="store_true",
        help="Start in Privacy Mode (mask sensitive URLs and notes)",
    )

    args = parser.parse_args()

    if args.init:
        print_init_snippet()
        return

    if args.clear_cache:
        from evm_rpc_picker.models import clear_cache

        clear_cache()
        # We don't print anything to stdout to avoid messing up the TUI/shell capture

    result = run_picker_tui(privacy=args.privacy)

    if result:
        # Print ONLY the RPC URL to stdout so it can be captured by shell scripts
        print(result)


if __name__ == "__main__":
    main()
