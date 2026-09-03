FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codi del bot
COPY bot/ bot/

# Per defecte, comanda per iniciar
ENV PYTHONPATH=/app
CMD ["python", "-m", "bot.main"]
