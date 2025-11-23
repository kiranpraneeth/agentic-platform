# Agentic Platform - Developer Cheat Sheet

> **Quick reference card for daily development**
>
> **Print this!** Perfect for 2-sided reference card

---

## 🚀 Quick Start

```bash
# Start everything
make docker-up

# Run migrations
make migrate

# Seed data
make seed

# View logs
make docker-logs

# Access API
open http://localhost:8000/docs
```

---

## 📁 Project Structure

```
src/
├── api/v1/          → Endpoints
├── core/            → Config, security
├── db/              → Models, session
├── schemas/         → Pydantic models
└── services/        → Business logic
```

---

## 🔧 Common Commands

### Docker
```bash
docker-compose up -d        # Start
docker-compose down         # Stop
docker-compose logs -f api  # Logs
docker-compose restart api  # Restart
```

### Database
```bash
alembic upgrade head               # Apply migrations
alembic revision --autogenerate -m # Create migration
docker-compose exec postgres psql  # Connect to DB
```

### Development
```bash
make dev       # Run dev server
make test      # Run tests
make lint      # Run linters
make format    # Format code
```

---

## 💻 Code Patterns

### Create API Endpoint
```python
# src/api/v1/your_module.py
from fastapi import APIRouter, Depends
from src.api.dependencies import CurrentTenant, CurrentUser

router = APIRouter()

@router.post("/endpoint")
async def your_endpoint(
    tenant: CurrentTenant,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Your logic
    return {"status": "ok"}
```

### Create Database Model
```python
# src/db/models.py
class YourModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "your_table"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
```

### Create Pydantic Schema
```python
# src/schemas/your_schema.py
class YourCreate(BaseModel):
    name: str = Field(..., min_length=1)

class YourResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Create Service
```python
# src/services/your_service.py
class YourService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create(self, name: str):
        obj = YourModel(tenant_id=self.tenant_id, name=name)
        self.db.add(obj)
        await self.db.flush()
        return obj
```

---

## 🗄️ Database Queries

```python
# Get single
result = await db.execute(
    select(Model).where(Model.id == id)
)
obj = result.scalar_one_or_none()

# Get multiple
result = await db.execute(
    select(Model)
    .where(Model.tenant_id == tenant_id)
    .order_by(Model.created_at.desc())
)
objs = result.scalars().all()

# Count
count = await db.scalar(
    select(func.count()).select_from(Model)
)

# Insert
obj = Model(name="test")
db.add(obj)
await db.flush()

# Update
obj.name = "updated"
await db.commit()

# Delete (soft)
obj.deleted_at = datetime.utcnow()
await db.commit()
```

---

## 🔐 Authentication

```python
# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Use token
curl http://localhost:8000/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# In code
@router.get("/protected")
async def protected(
    tenant: CurrentTenant,
    user: CurrentUser,
):
    # Auto-authenticated
    pass
```

---

## 🤖 Agent Execution

```python
# Execute agent
from src.services.agent_executor import AgentExecutor

agent = await db.get(Agent, agent_id)
executor = AgentExecutor(agent, db)

response = await executor.execute(
    input_text="Hello!",
    conversation=conversation
)

print(response.response)
print(response.token_usage)
print(response.latency_ms)
```

---

## 📚 RAG Operations

```python
# Create collection
from src.services.rag_service import RAGService

rag = RAGService(db, tenant_id)
collection = await rag.create_collection(
    name="Docs",
    embedding_model="text-embedding-3-small"
)

# Upload document
document = await rag.upload_document(
    collection_id=collection.id,
    title="My Doc",
    file_content=file_bytes,
    filename="doc.pdf"
)

# Search
results = await rag.search(
    collection_id=collection.id,
    query_text="search term",
    top_k=5
)
```

---

## 🐛 Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with ipdb
import ipdb; ipdb.set_trace()

# Commands:
#   c - continue
#   n - next line
#   s - step into
#   p var - print variable
#   l - list code
#   q - quit
```

---

## 🧪 Testing

```python
# Run all tests
pytest

# Run specific test
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src --cov-report=html

# Test pattern
@pytest.mark.asyncio
async def test_create_agent():
    agent = await create_test_agent()
    assert agent.name == "Test"
```

---

## 🔍 Troubleshooting

### Database Connection
```bash
# Check if running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### API Not Responding
```bash
# Check logs
docker-compose logs -f api

# Restart
docker-compose restart api

# Rebuild
docker-compose up -d --build api
```

### Migration Issues
```bash
# Check status
alembic current

# Rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

---

## 📞 Environment Variables

```bash
# Required
SECRET_KEY=your-secret-32-chars+
JWT_SECRET=your-jwt-secret-32-chars+
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=sk-ant-...

# Optional
OPENAI_API_KEY=sk-...
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*
```

---

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app |
| `src/core/config.py` | Settings |
| `src/db/models.py` | Database models |
| `src/api/dependencies.py` | Auth dependencies |
| `.env` | Environment variables |
| `docker-compose.yml` | Services config |
| `alembic.ini` | Migration config |

---

## 📖 Documentation

| Doc | Use For |
|-----|---------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Daily patterns |
| [CODEBASE_DEEP_DIVE.md](CODEBASE_DEEP_DIVE.md) | Deep learning |
| [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) | Why decisions |
| [docs/README.md](README.md) | Navigation |

---

## 🆘 Getting Help

1. Search docs: `grep "term" docs/*.md`
2. Check troubleshooting in QUICK_REFERENCE.md
3. Ask team
4. Check GitHub issues

---

## ⚡ Pro Tips

✅ Use `make help` to see all commands
✅ Use `Ctrl+F` to search this sheet
✅ Keep `.env` file secure (never commit)
✅ Run `make format` before committing
✅ Test locally with `make test`
✅ Check logs with `make docker-logs`
✅ Use type hints everywhere
✅ Filter by `tenant_id` in all queries
✅ Use async/await for DB operations
✅ Read QUICK_REFERENCE.md for more patterns

---

## 🎨 VS Code Shortcuts

| Key | Action |
|-----|--------|
| `Cmd+P` | Quick file open |
| `Cmd+Shift+F` | Search in files |
| `Cmd+T` | Go to symbol |
| `F12` | Go to definition |
| `Shift+F12` | Find references |
| `Cmd+.` | Quick fix |

---

**Print this for your desk!** 🖨️

---

*Last Updated: 2025-01-09*
*Quick Reference v1.0*
