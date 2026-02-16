# AI Project Manager

An intelligent chatbot for project management powered by Google Gemini AI, featuring natural language understanding, risk analysis, and conversation memory.

## Features

- **Natural Language Commands**: Create projects and query status using plain English
- **AI Risk Analysis**: Automatic detection of delays and bottlenecks with recommendations
- **Multi-Person Assignment**: Assign tasks to specific people across different teams
- **Conversation Memory**: Redis-powered context retention (remembers "it", "that project", etc.)
- **SQLite Database**: Production-grade data persistence with ACID transactions
- **Hybrid Fallback**: Local regex parser when AI quota is exhausted
- **Real-time Updates**: Angular frontend with live chatbot interface

## Tech Stack

**Backend:**
- FastAPI (Python)
- Google Gemini AI (gemini-2.5-flash)
- spaCy (NLP entity extraction)
- Redis (conversation memory)
- SQLite (data persistence)

**Frontend:**
- Angular 19
- TypeScript
- Vite

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redis server
- Google Gemini API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-project-manager.git
cd ai-project-manager
```

2. **Backend Setup**
```bash
# Create virtual environment
python3 -m venv ai_env
source ai_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python3 -m spacy download en_core_web_sm

# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

3. **Start Redis**
```bash
sudo systemctl start redis-server
```

4. **Start Backend**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. **Frontend Setup** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

6. **Access the app**
- Frontend: http://localhost:4200
- Backend API: http://localhost:8000

## Usage Examples

**Create a project:**
```
Create Project Alpha with 16 tasks, assign 7 to frontend (John, Sarah), 
5 to backend (Mike, Tom), and 4 to testing (Lisa)
```

**Query status with AI analysis:**
```
What's the status of Project Alpha?
```
*Response includes completion %, delayed tasks, risk level, and recommendations*

**Use conversation memory:**
```
User: Create Project Beta with 10 tasks
Bot: ✅ Created

User: What's the status of it?
Bot: Project Beta is at 0% completion...  ← "it" resolves to Beta
```

## Project Structure

```
ai-project-manager/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── nlp_processor.py     # Gemini AI + spaCy
│   ├── session_manager.py   # Redis conversation memory
│   ├── db_manager.py        # SQLite CRUD operations
│   ├── database.py          # Database schema
│   ├── java_gateway.py      # Backend interface
│   └── parser.py            # Local regex fallback
├── frontend/
│   └── src/
│       └── app/
│           └── chat/        # Chat UI component
├── scripts/
│   ├── migrate_to_sqlite.py    # JSON → SQLite migration
│   ├── test_redis_memory.py    # Conversation memory tests
│   └── view_database.py        # Database viewer
└── requirements.txt
```

## Database Schema

**projects** table:
- id, name, status, completion, delayed_tasks, total_tasks

**allocations** table:
- id, project_id, team_name, task_count

**team_members** table:
- id, allocation_id, person_name

## API Endpoints

- `POST /chat` - Send message to chatbot
- `GET /health` - Backend health check

## Features in Detail

### Smart Risk Analysis
- Calculates 0-100 risk score based on delays and completion rate
- Classifies as LOW/MEDIUM/HIGH
- Provides actionable recommendations

### Conversation Memory
- Stores last 5 messages per session
- Resolves pronouns using context
- 1-hour session expiration

### Hybrid Parser
- Primary: Gemini AI (accurate, intelligent)
- Fallback: Regex parser (when quota exhausted)

## Development

**Run tests:**
```bash
python3 scripts/test_redis_memory.py
python3 scripts/test_sqlite_storage.py
```

**View database:**
```bash
python3 scripts/view_database.py
```

## Contributing

Pull requests welcome! Please ensure:
- Code follows PEP 8
- All tests pass
- Update README if needed

## License

MIT

## Author

Built with ❤️ using Google Gemini AI
