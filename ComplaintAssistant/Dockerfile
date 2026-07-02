FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py config.py ./

EXPOSE 8000

# Default: serve via ADK web (swap CMD for CLI mode)
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]
