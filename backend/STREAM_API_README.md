# 🚀 BGB AI Chat API - Stream-Endpunkt für Frontend

## ✅ Was wurde geändert?

### 1. **Authentifizierung vereinfacht** (POC-Mode)
- JWT-Authentifizierung ist nun **optional**
- API erlaubt anonyme Zugriffe für schnelle Tests
- Perfekt für POC und Entwicklung

### 2. **Neuer Stream-Endpunkt** für Frontend-Integration
- **Endpoint**: `POST /api/v1/stream/chat`
- **SSE (Server-Sent Events)** für Echtzeit-Streaming
- **CORS aktiviert** für Frontend-Zugriff

### 3. **Frontend-Demo** (HTML/JavaScript)
- Vollständiges Chat-Interface
- Live-Streaming der Token
- Agent-Auswahl (Qwen/Gemini)
- Thread-Management

---

## 🎯 Stream-Endpunkt Nutzung

### Endpoint: `POST /api/v1/stream/chat`

#### Request Body:
```json
{
  "thread_id": "optional-uuid-for-existing-thread",
  "agent": "qwen",  // oder "gemini"
  "message": "Was ist § 833 BGB?",
  "params": {}
}
```

#### SSE Events:
Der Stream sendet folgende Events:

1. **`metadata`** - Thread-Informationen
   ```json
   {"thread_id": "550e8400-e29b-41d4-a716-446655440000"}
   ```

2. **`start`** - Stream beginnt
   ```json
   {"role": "assistant", "agent": "qwen"}
   ```

3. **`token`** - Einzelne Token-Chunks (viele!)
   ```json
   {"token": "Nach"}
   {"token": " § 833"}
   {"token": " BGB..."}
   ```

4. **`tool_call`** - Tool wurde aufgerufen (optional)
   ```json
   {"name": "bgb_solr_search", "arguments": "..."}
   ```

5. **`usage`** - Nutzungsstatistik (optional)
   ```json
   {"tokens": 1234, "cost": 0.05}
   ```

6. **`done`** - Stream abgeschlossen
   ```json
   {
     "message_id": 123,
     "thread_id": "550e8400-...",
     "content": "Nach § 833 BGB haftet..."
   }
   ```

7. **`error`** - Fehler aufgetreten
   ```json
   {"message": "Agent execution failed"}
   ```

---

## 🧪 Schnellstart

### Option 1: Mit der HTML-Demo

1. **API starten:**
   ```bash
   cd /Users/I570118/PycharmProjects/kg_project333/backend
   pipenv run uvicorn api.main:app --host 0.0.0.0 --port 8080
   ```

2. **HTML-Demo öffnen:**
   ```bash
   open stream_demo.html
   ```
   Oder direkt im Browser: `file:///Users/I570118/PycharmProjects/kg_project333/backend/stream_demo.html`

3. **Fertig!** 🎉
   - Wähle einen Agent (Qwen oder Gemini)
   - Stelle eine Frage zum BGB
   - Sieh die Antwort in Echtzeit streamen

### Option 2: Mit cURL (Test)

```bash
curl -N -X POST http://localhost:8080/api/v1/stream/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "qwen",
    "message": "Was ist § 1 BGB?"
  }'
```

Die `-N` Flag ist wichtig für Streaming!

### Option 3: Mit JavaScript/Fetch

```javascript
const response = await fetch('http://localhost:8080/api/v1/stream/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent: 'qwen',
    message: 'Was ist § 833 BGB?'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data:')) {
      const data = JSON.parse(line.substring(5));
      
      if (data.token) {
        console.log('Token:', data.token);
        // Append token to UI
      }
      
      if (data.message_id) {
        console.log('Done!', data.content);
        // Stream complete
      }
    }
  }
}
```

---

## 📋 API-Endpunkte (Übersicht)

### Stream (NEU! 🆕)
- `POST /api/v1/stream/chat` - Chat mit Streaming
- `GET /api/v1/stream/health` - Stream Health Check

### Threads
- `POST /api/v1/threads` - Thread erstellen
- `GET /api/v1/threads/{id}` - Thread abrufen
- `GET /api/v1/threads` - Threads auflisten
- `DELETE /api/v1/threads/{id}` - Thread löschen

### Messages
- `GET /api/v1/threads/{id}/messages` - Nachrichten auflisten
- `POST /api/v1/threads/{id}/messages` - Nachricht senden (non-stream)

### Agents
- `GET /api/v1/agents` - Verfügbare Agents

### Health
- `GET /healthz` - Health Check
- `GET /readyz` - Readiness Check
- `GET /version` - Version Info

---

## 🎨 Frontend-Demo Features

Die `stream_demo.html` bietet:

✅ **Echtzeit-Streaming** - Token erscheinen live  
✅ **Agent-Auswahl** - Wechsel zwischen Qwen und Gemini  
✅ **Thread-Management** - Automatische Thread-Erstellung und -Wiederverwendung  
✅ **Tool-Call-Anzeige** - Sehe, welche Tools der Agent nutzt  
✅ **Responsive Design** - Schöne UI mit Gradients  
✅ **Typing-Indicator** - Zeigt an, wenn Agent denkt  
✅ **Error-Handling** - Zeigt Fehler sauber an  

---

## 🔧 Konfiguration (Environment)

Keine Authentifizierung erforderlich für POC! Aber du kannst optional setzen:

```bash
# Optional: API-Key (wenn gewünscht)
export API_KEY=""  # Leer = keine Auth

# Database
export DB_URL="postgresql+psycopg://bgb_user:bgb_password@localhost:5432/bgb_chat"

# Agent
export AGENT_SERVICE_MODE="inproc"

# Logging
export LOG_LEVEL="INFO"
```

---

## 🐛 Troubleshooting

### Problem: "CORS error"
**Lösung**: CORS ist bereits aktiviert (`allow_origins=["*"]`). Prüfe, ob API läuft.

### Problem: "Connection refused"
**Lösung**: 
```bash
# API starten
cd backend
pipenv run uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### Problem: "Agent not available"
**Lösung für Qwen**: 
```bash
ollama serve
ollama pull qwen2.5:14b
```

**Lösung für Gemini**:
```bash
export GOOGLE_API_KEY="your-key-here"
```

### Problem: "Database connection failed"
**Lösung**:
```bash
docker-compose up -d postgres
pipenv run alembic upgrade head
```

---

## 📚 Beispiel-Fragen zum Testen

1. "Was besagt § 833 BGB?" (Tierhalterhaftung)
2. "Erkläre mir § 1 BGB" (Beginn der Rechtsfähigkeit)
3. "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?"
4. "Was ist ein Kaufvertrag nach BGB?"
5. "Welche Voraussetzungen hat eine Willenserklärung?"

---

## 🎯 Nächste Schritte

1. ✅ **API läuft** mit Stream-Endpunkt
2. ✅ **Frontend-Demo** ist bereit
3. 🔜 **Integration in dein Frontend** (React/Vue/Next.js)
4. 🔜 **Produktions-Deployment** mit Docker

---

## 💡 Tipps für Frontend-Integration

### React Example:
```jsx
import { useState, useEffect } from 'react';

function Chat() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  
  const streamChat = async () => {
    const res = await fetch('http://localhost:8080/api/v1/stream/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent: 'qwen', message })
    });
    
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      // Parse SSE events and update state
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const data = JSON.parse(line.substring(5));
          if (data.token) {
            setResponse(prev => prev + data.token);
          }
        }
      }
    }
  };
  
  return (
    <div>
      <input value={message} onChange={e => setMessage(e.target.value)} />
      <button onClick={streamChat}>Send</button>
      <div>{response}</div>
    </div>
  );
}
```

Viel Erfolg! 🚀

