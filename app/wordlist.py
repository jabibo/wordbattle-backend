from app.config import DEFAULT_WORDLIST_PATH

def load_wordlist(path=None) -> set[str]:
    """
    Load a wordlist from a file.
    
    Args:
        path: Path to the wordlist file. If None, uses the default path from config.
        
    Returns:
        A set of uppercase words from the file.
    """
    if path is None:
        path = DEFAULT_WORDLIST_PATH
        
    with open(path, encoding="utf-8") as f:
        return set(line.strip().upper() for line in f if line.strip())