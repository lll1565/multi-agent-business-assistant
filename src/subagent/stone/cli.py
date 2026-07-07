"""Backward-compatible CLI shim — prefer ``subagent.stone.runtime.cli``."""

from subagent.stone.runtime.cli import main

if __name__ == "__main__":
    main()
