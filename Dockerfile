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
COPY wordbattle-contracts/ /app/contracts/

# Copy and rename wordlist files to expected names (only if they don't already exist)
RUN echo -e "HALLO\nWELT\nTEST\nSPIEL\nWORT\nTAG\nTAGE\nBAUM" > data/de_words.txt
RUN if [ -f data/en-words.txt ] && [ -s data/en-words.txt ]; then cp data/en-words.txt data/en_words.txt; else echo -e "HELLO\nWORLD\nTEST\nGAME\nWORD\nDAY\nDAYS\nTREE" > data/en_words.txt; fi

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
