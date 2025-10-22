# 🔄 BGB Chat Service - Architektur Update

## ✅ Umstrukturierung abgeschlossen!

Das System wurde neu strukturiert für eine **klare Trennung der Verantwortlichkeiten**:

### 🎯 Neue Architektur

```
┌─────────────────────────────────────────────────────────┐
│           Frontend (Next.js + Drizzle ORM)              │
│  • Chat History Speicherung (PostgreSQL)                │
│  • Session Management                                    │
│  • UI/UX                                                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/SSE
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Backend (FastAPI - STATELESS)                  │
│  • Streaming Chat Service                               │
│  • Tool Calls (Solr + SPARQL)                           │
│  • Qwen Agent Integration                               │
│  • NUTZT History vom Frontend für Kontext!              │
│  • KEINE eigene Persistence                             │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌─────────────┐      ┌─────────────┐
   │    Solr     │      │ Blazegraph  │
   │   Search    │      │   SPARQL    │
   └─────────────┘      └─────────────┘
```

## 🔧 Backend Änderungen (FastAPI)

### Entfernt:
- ❌ PostgreSQL Persistence (`postgres_saver.py`)
- ❌ Session Management Router (`session_router.py`)
- ❌ Chat History Endpoints
- ❌ Dependencies: `psycopg2-binary`, `sqlalchemy`, `langgraph-checkpoint-postgres`

### Vereinfacht:
- ✅ `chat_service.py` - Nur noch Streaming, keine DB
- ✅ `chat_router.py` - Ein Endpoint: `POST /chat/stream`
- ✅ `main.py` - Keine PostgreSQL Connection mehr

### Neues API Schema:

**POST /chat/stream**
```json
{
  "message": "Was ist ein Kaufvertrag?",
  "history": [
    {"role": "user", "content": "Hallo"},
    {"role": "assistant", "content": "Wie kann ich helfen?"}
  ]
}
```

Frontend sendet die History MIT, Backend streamt nur Response!

## 📦 Frontend Änderungen (Next.js)

### Neu hinzugefügt:

1. **Drizzle Schema** (`lib/db/schema-bgb.ts`)
   - `bgb_chats` - Chat Sessions
   - `bgb_messages` - Chat Messages
   - `bgb_tool_results` - Tool Call Results

2. **Server Actions** (`lib/actions/chat-actions.ts`)
   - `createChat()` - Neue Chat Session
   - `saveMessage()` - Message speichern
   - `getMessagesForBackend()` - History für Backend
   - `deleteChat()` - Chat löschen

3. **React Hook** (`hooks/use-bgb-chat.ts`)
   - `useBGBChat()` - Streaming + Auto-Save

4. **API Client** (`lib/api/bgb-chat-api.ts`)
   - `streamChat()` - Server-Sent Events
   - `healthCheck()` - Backend Status

## 🗄️ Datenbank Setup

### PostgreSQL Tabellen (Frontend)

```sql
-- Chat Sessions
CREATE TABLE bgb_chats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL DEFAULT 'default_user',
  title TEXT NOT NULL DEFAULT 'Neue Unterhaltung',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE bgb_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id UUID NOT NULL REFERENCES bgb_chats(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'function')),
  content TEXT NOT NULL,
  thinking_content TEXT,
  tool_calls JSONB,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tool Results
CREATE TABLE bgb_tool_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES bgb_messages(id) ON DELETE CASCADE,
  tool_call_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  output TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## 🚀 Workflow

### 1. User sendet Nachricht

```typescript
const { sendMessage } = useBGBChat({ chatId: '...' });
await sendMessage("Was ist ein Kaufvertrag?");
```

### 2. Hook speichert User Message in DB

```typescript
await saveMessage(chatId, 'user', userMessage);
```

### 3. Hook holt History für Backend

```typescript
const history = await getMessagesForBackend(chatId);
// [{ role: 'user', content: '...' }, ...]
```

### 4. Backend streamt Response

```typescript
for await (const chunk of streamChat(chatId, message, history)) {
  // type: 'thinking' | 'text' | 'tool_call' | 'tool_result' | 'done'
}
```

### 5. Hook speichert Assistant Response in DB

```typescript
await saveMessage(chatId, 'assistant', assistantMessage, thinkingContent, toolCalls);
```

## 🔑 Environment Variables

### Backend (.env)
```bash
# API
API_PORT=8000

# Qwen Agent
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14B
ENABLE_THINKING=true

# Services
SOLR_URL=http://localhost:8984/solr/bgb_core
BLAZEGRAPH_URL=http://localhost:9999/bigdata/sparql

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# PostgreSQL (für Chat History)
POSTGRES_URL=postgresql://bgb_user:bgb_secure_password_2024@localhost:5432/bgb_chat

# Auth
AUTH_SECRET=your-super-secret-key
```

## 📝 Migration Anleitung

### 1. Backend neu installieren

```bash
cd packages/chat_service
pip install -r requirements.txt  # Keine PostgreSQL Dependencies mehr!
./start.sh
```

### 2. Frontend Setup

```bash
cd packages/frontend
pnpm install

# Drizzle Schema generieren
pnpm db:generate

# Migration ausführen
pnpm db:migrate

# Frontend starten
pnpm dev
```

### 3. PostgreSQL starten (für Frontend)

```bash
# Im Root-Verzeichnis
docker-compose up -d bgb-postgres
```

## ✅ Vorteile der neuen Architektur

1. **Backend Simplicity**: Stateless → einfacher zu skalieren
2. **Frontend Control**: Volle Kontrolle über Chat History
3. **Bessere Performance**: Keine redundante Speicherung
4. **Klare Trennung**: Backend = AI Logic, Frontend = Data Management
5. **Flexibilität**: Frontend kann History beliebig formatieren

## 🧪 Testing

```bash
# Backend Health Check
curl http://localhost:8000/health/detailed

# Chat Stream Test
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Was ist ein Kaufvertrag?",
    "history": []
  }'
```

## 🎯 Nächste Schritte

1. ✅ Backend vereinfacht
2. ✅ Frontend Drizzle Schema erstellt
3. ✅ Server Actions implementiert
4. ✅ React Hook erstellt
5. ⏳ UI Components anpassen (Chat Interface)
6. ⏳ Database Migrations ausführen
7. ⏳ End-to-End Tests

---

**Status**: ✅ Backend & Frontend Core implementiert  
**Bereit für**: UI Integration & Testing

