import difflib


def suggest(input_str: str, candidates: list[str], n: int = 3, cutoff: float = 0.6) -> list[str]:
    return difflib.get_close_matches(input_str, candidates, n=n, cutoff=cutoff)
