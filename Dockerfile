FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p data

# Create minimal wordlist files if they don't exist
RUN echo -e "HALLO\nWELT\nTEST\nSPIEL\nWORT\nTAG\nTAGE\nBAUM" > data/de_words.txt
RUN echo -e "HELLO\nWORLD\nTEST\nGAME\nWORD\nDAY\nDAYS\nTREE" > data/en_words.txt

# Set database host for Docker
ENV DB_HOST=host.docker.internal

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
