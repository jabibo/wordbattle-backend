FROM python:3.11-slim

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p data

# Copy and rename wordlist files to expected names (only if they don't already exist)
RUN if [ -f data/de-words.txt ]; then cp data/de-words.txt data/de_words.txt; else echo -e "HALLO\nWELT\nTEST\nSPIEL\nWORT\nTAG\nTAGE\nBAUM" > data/de_words.txt; fi
RUN if [ -f data/en-words.txt ] && [ -s data/en-words.txt ]; then cp data/en-words.txt data/en_words.txt; else echo -e "HELLO\nWORLD\nTEST\nGAME\nWORD\nDAY\nDAYS\nTREE" > data/en_words.txt; fi

# Set database host for Docker
ENV DB_HOST=db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
