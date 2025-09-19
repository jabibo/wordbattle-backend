FROM python:3.11-slim

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p data

# Copy contracts directory if it exists
# COPY wordbattle-contracts/ /app/contracts/

# Create fallback wordlist files only if real ones don't exist
RUN if [ ! -f data/de_words.txt ] || [ ! -s data/de_words.txt ]; then echo -e "HALLO\nWELT\nTEST\nSPIEL\nWORT\nTAG\nTAGE\nBAUM" > data/de_words.txt; fi
RUN if [ ! -f data/en_words.txt ] || [ ! -s data/en_words.txt ]; then echo -e "HELLO\nWORLD\nTEST\nGAME\nWORD\nDAY\nDAYS\nTREE" > data/en_words.txt; fi

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
