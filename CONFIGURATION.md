# Configuration Management

All configuration is managed through environment variables to avoid hardcoding.

## Setup

1. **Copy the example environment file**:
```bash
cp .env.example .env
```

2. **Edit `.env` with your values**:
```bash
nano .env
```

3. **Required: Add your Gemini API key**:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `DATABASE_PATH` | `projects.db` | SQLite database file path |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_SESSION_TTL_HOURS` | `1` | Session expiration time |
| `BACKEND_HOST` | `0.0.0.0` | Backend API host |
| `BACKEND_PORT` | `8000` | Backend API port |
| `FRONTEND_URL` | `http://localhost:4200` | Frontend URL for CORS |
| `ALLOWED_ORIGINS` | `http://localhost:4200` | Comma-separated CORS origins |
| `JAVA_BACKEND_URL` | *(optional)* | Java backend URL for future integration |

## Frontend Configuration

The frontend API URL is in `frontend/src/app/services/chat.service.ts`:

```typescript
private apiUrl = 'http://127.0.0.1:8000/chat';
```

**For production**, change this to your deployed backend URL.

## Multiple CORS Origins

To allow multiple frontend URLs:

```bash
ALLOWED_ORIGINS=http://localhost:4200,http://example.com,https://myapp.com
```

## Production Deployment

For production environments, you can:

1. Set environment variables directly on the server
2. Use a `.env` file (keep it secure, never commit it!)
3. Use cloud provider environment configuration (AWS, Heroku, etc.)

## Security Notes

- ⚠️ **Never commit `.env` to git!** (It's in `.gitignore`)
- ✅ Share `.env.example` as a template
- 🔒 Keep API keys secret
