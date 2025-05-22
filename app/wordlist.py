def load_wordlist(path="data/de_words.txt") -> set[str]:
    with open(path, encoding="utf-8") as f:
        return set(line.strip().upper() for line in f if line.strip())
