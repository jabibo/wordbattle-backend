# Multi-Language Wordlists

WordBattle now supports multiple languages for wordlists. This document explains how to manage wordlists in the database.

## Overview

Wordlists are stored in the database in the `wordlists` table. Each word is associated with a language code (e.g., "de" for German, "en" for English).

## Importing Wordlists

### Using the Command Line

You can import a wordlist from a text file using the `import_wordlist.py` script:

```bash
python import_wordlist.py de --path data/de_words.txt
python import_wordlist.py en --path data/en_words.txt
```

### Using the Admin API

Administrators can import wordlists using the Admin API:

```bash
# Upload a wordlist file
curl -X POST "http://localhost:8000/admin/wordlists/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "language=en" \
  -F "file=@/path/to/wordlist.txt"
```

## Managing Wordlists

### Listing Available Wordlists

```bash
# List all available wordlists
curl -X GET "http://localhost:8000/admin/wordlists" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Deleting a Wordlist

```bash
# Delete a wordlist for a specific language
curl -X DELETE "http://localhost:8000/admin/wordlists/en" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Using Wordlists in Games

When creating a game, you can specify the language to use:

```bash
# Set the language for a game
curl -X POST "http://localhost:8000/games/GAME_ID/language" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '"en"'
```

If no language is specified, the game will default to German ("de").

## Wordlist Format

Wordlists should be plain text files with one word per line. Words will be automatically converted to uppercase when imported.

Example:
```
apple
banana
cherry
date
elderberry
```

## Adding a New Language

To add support for a new language:

1. Prepare a wordlist file with words in the target language
2. Import the wordlist using the command line or Admin API
3. Create games specifying the new language code

## Default Language

If a game doesn't specify a language, or if the specified language doesn't exist in the database, the system will fall back to German ("de").