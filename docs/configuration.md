# Configuration & Deployment

This document covers configuration options and deployment strategies for Logic-Guard-Layer.

## Table of Contents

- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Configuration File](#configuration-file)
  - [Settings Class](#settings-class)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
  - [Docker](#docker)
  - [Systemd Service](#systemd-service)
  - [Nginx Reverse Proxy](#nginx-reverse-proxy)
  - [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Configuration

### Environment Variables

Logic-Guard-Layer uses environment variables for configuration. These can be set directly or via a `.env` file.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key |
| `OPENROUTER_MODEL` | No | `tngtech/deepseek-r1t2-chimera:free` | LLM model to use |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | API base URL |
| `MAX_CORRECTION_ITERATIONS` | No | `5` | Max self-correction iterations |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |

### Configuration File

Create a `.env` file in the project root:

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Optional - LLM Settings
OPENROUTER_MODEL=tngtech/deepseek-r1t2-chimera:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional - Pipeline Settings
MAX_CORRECTION_ITERATIONS=5

# Optional - Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### Settings Class

The configuration is managed via Pydantic Settings:

```python
# src/logic_guard_layer/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "tngtech/deepseek-r1t2-chimera:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Pipeline
    max_correction_iterations: int = 5

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
```

#### Accessing Settings

```python
from logic_guard_layer.config import settings

# Use settings
print(f"Model: {settings.openrouter_model}")
print(f"Max iterations: {settings.max_correction_iterations}")
```

---

## Development Setup

### Prerequisites

- Python 3.11+
- pip
- OpenRouter API key

### Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd logic-guard-layer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your API key

# 5. Run development server
python run.py --reload
```

### Development Commands

```bash
# Run with auto-reload
python run.py --reload

# Run with debug logging
python run.py --reload --debug

# Run on custom port
python run.py --port 3000 --reload

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=logic_guard_layer --cov-report=html

# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/
```

### IDE Configuration

#### VS Code

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

#### PyCharm

1. Set Python interpreter to venv
2. Enable pytest as test runner
3. Configure Black as formatter
4. Add `.env` to run configurations

---

## Production Deployment

### Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ src/
COPY pyproject.toml .

# Install package
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "logic_guard_layer.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  logic-guard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-tngtech/deepseek-r1t2-chimera:free}
      - MAX_CORRECTION_ITERATIONS=${MAX_CORRECTION_ITERATIONS:-5}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add Redis for caching
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "6379:6379"
```

#### Build and Run

```bash
# Build image
docker build -t logic-guard-layer .

# Run container
docker run -d \
  --name logic-guard \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY=sk-or-v1-xxx \
  logic-guard-layer

# Or use docker-compose
docker-compose up -d
```

### Systemd Service

Create `/etc/systemd/system/logic-guard.service`:

```ini
[Unit]
Description=Logic-Guard-Layer Validation Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/logic-guard-layer
Environment="PATH=/opt/logic-guard-layer/venv/bin"
EnvironmentFile=/opt/logic-guard-layer/.env
ExecStart=/opt/logic-guard-layer/venv/bin/uvicorn logic_guard_layer.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable logic-guard
sudo systemctl start logic-guard

# Check status
sudo systemctl status logic-guard

# View logs
sudo journalctl -u logic-guard -f
```

### Nginx Reverse Proxy

`/etc/nginx/sites-available/logic-guard`:

```nginx
upstream logic_guard {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name logic-guard.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name logic-guard.example.com;

    ssl_certificate /etc/letsencrypt/live/logic-guard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/logic-guard.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://logic_guard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout for long-running validations
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # SSE support for streaming endpoint
    location /api/validate/stream {
        proxy_pass http://logic_guard;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }

    # Static files (optional caching)
    location /static/ {
        proxy_pass http://logic_guard;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/logic-guard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Cloud Deployment

#### AWS (EC2 + Application Load Balancer)

1. Launch EC2 instance (t3.small or larger)
2. Install dependencies and application
3. Configure security groups (allow 8000 from ALB only)
4. Create ALB with target group pointing to EC2
5. Configure Route 53 DNS

#### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/logic-guard-layer

# Deploy to Cloud Run
gcloud run deploy logic-guard-layer \
  --image gcr.io/PROJECT_ID/logic-guard-layer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=sk-or-v1-xxx
```

#### Heroku

`Procfile`:
```
web: uvicorn logic_guard_layer.main:app --host 0.0.0.0 --port $PORT
```

```bash
heroku create logic-guard-layer
heroku config:set OPENROUTER_API_KEY=sk-or-v1-xxx
git push heroku main
```

---

## Monitoring

### Health Checks

The `/api/health` endpoint provides health status:

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "model": "tngtech/deepseek-r1t2-chimera:free",
    "ontology_loaded": true
}
```

### Logging

Configure logging level via environment:

```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

Log format includes:
- Timestamp
- Log level
- Module name
- Message
- Request ID (for API requests)

### Metrics

Key metrics to monitor:
- Request latency (processing_time_ms)
- Validation success rate
- Correction iteration counts
- LLM API errors and latency
- Memory usage

Example Prometheus metrics endpoint (future enhancement):
```
logic_guard_validations_total{status="success"} 1523
logic_guard_validations_total{status="failed"} 127
logic_guard_correction_iterations_histogram_bucket{le="1"} 800
logic_guard_correction_iterations_histogram_bucket{le="3"} 1400
logic_guard_processing_time_seconds_histogram_bucket{le="1"} 600
logic_guard_processing_time_seconds_histogram_bucket{le="5"} 1500
```

---

## Troubleshooting

### Common Issues

#### API Key Not Found

```
Error: OPENROUTER_API_KEY environment variable not set
```

**Solution:** Set the API key in `.env` or environment:
```bash
export OPENROUTER_API_KEY=sk-or-v1-xxx
```

#### Rate Limiting

```
Error: 429 Too Many Requests
```

**Solution:**
- Use a paid OpenRouter tier
- Implement request queuing
- Add exponential backoff (already built-in)

#### Memory Issues

```
Error: MemoryError or OOM killed
```

**Solution:**
- Increase container/server memory
- Limit concurrent requests
- Use gunicorn with workers: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker`

#### Ontology Loading Failed

```
Error: Failed to load ontology from path
```

**Solution:**
- Ensure `data/` directory exists with OWL file
- Check file permissions
- Verify OWL file is valid

#### LLM Response Parsing Failed

```
Error: Failed to parse LLM response as JSON
```

**Solution:**
- Check LLM model compatibility
- Lower temperature for more deterministic output
- Review prompt templates in `llm/prompts.py`

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Via environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Via run script
python run.py --reload --debug
```

Debug mode enables:
- Detailed request/response logging
- Stack traces in error responses
- Auto-reload on code changes
- Verbose LLM interaction logs

### Performance Tuning

#### LLM Optimization

```python
# In config or environment
OPENROUTER_MODEL=anthropic/claude-3-haiku  # Faster model
```

#### Concurrency

```bash
# Use multiple workers
gunicorn logic_guard_layer.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### Caching (Future)

```python
# Example Redis caching setup
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_result(text_hash):
    return cache.get(f"validation:{text_hash}")

def cache_result(text_hash, result, ttl=3600):
    cache.setex(f"validation:{text_hash}", ttl, result)
```
