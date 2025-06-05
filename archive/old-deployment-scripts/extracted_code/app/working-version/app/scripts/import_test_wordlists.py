from app.wordlist import import_wordlist

# Import German wordlist
import_wordlist("de", "data/de_words.txt")

# Import English wordlist if available
try:
    import_wordlist("en", "data/en_words.txt")
    print("English wordlist imported")
except Exception as e:
    print(f"English wordlist not imported: {e}")

print("Wordlists imported successfully!")