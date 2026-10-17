import os

# Configuration utilities for market‑specific ticker handling.
# Reads an environment variable ``DEFAULT_MARKET_SUFFIX``.
# If the variable is not set, the historic default ``.NS`` (India) is used.
# The helper ``apply_market_suffix`` appends the suffix only when the ticker
# does not already contain a period (e.g. "AAPL" → "AAPL.NS" if suffix is ".NS",
# but "MSFT.US" stays unchanged).

DEFAULT_MARKET_SUFFIX = os.getenv("DEFAULT_MARKET_SUFFIX", ".NS")


def apply_market_suffix(symbol: str) -> str:
    """Return *symbol* with the appropriate market suffix.

    * If ``symbol`` already contains a period (e.g. "AAPL.US"), it is returned unchanged.
    * Otherwise the ``DEFAULT_MARKET_SUFFIX`` is appended (which may be an empty string).
    """
    if "." in symbol:
        return symbol
    return f"{symbol}{DEFAULT_MARKET_SUFFIX}"
