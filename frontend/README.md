# BGB Chat Frontend

Next.js Frontend für die BGB AI Chat API mit shadcn/ui.

## Features

- 💬 Chat-Interface mit Streaming-Unterstützung
- 🧵 Thread-Verwaltung (erstellen, löschen, auswählen)
- 🤖 Multi-Agent Support (Qwen, Gemini)
- 🎨 Moderne UI mit shadcn/ui
- ⚡ Echtzeit-Streaming von AI-Antworten

## Setup

1. **Dependencies installieren:**
```bash
pnpm install
```

2. **Environment konfigurieren:**
Die `.env.local` ist bereits erstellt. Bei Bedarf anpassen:
```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

3. **Backend starten:**
Im `backend` Ordner:
```bash
cd ../backend
pipenv run api-start
```

4. **Frontend starten:**
```bash
pnpm dev
```

5. **Öffnen:**
Browser: http://localhost:3000

## Verwendung

### Chat starten
- Klicke auf "Neuer Chat" in der Sidebar
- Gib deine Frage zum BGB ein
- Die Antwort wird in Echtzeit gestreamt

### Agent wechseln
- Klicke auf die Badge-Buttons oben (qwen/gemini)
- Nur verfügbare Agents sind anklickbar

### Threads verwalten
- Threads werden automatisch gespeichert
- Klicke auf einen Thread, um ihn zu öffnen
- Lösche Threads mit dem Papierkorb-Icon

## Komponenten

### `lib/api-client.ts`
TypeScript API-Client für alle Backend-Routen:
- Threads (erstellen, laden, löschen)
- Messages (senden, laden)
- Streaming (SSE-Support)
- Agents (verfügbare Agents laden)

### `components/chat-interface.tsx`
Haupt-Chat-Komponente mit:
- Message-Display (User & Assistant)
- Input-Feld mit Send-Button
- Agent-Auswahl
- Streaming-Anzeige
- Error-Handling

### `components/thread-sidebar.tsx`
Sidebar mit:
- Thread-Liste
- "Neuer Chat" Button
- Thread-Auswahl
- Thread-Löschen

## API-Routen

Das Frontend nutzt folgende Backend-Routes:
- `GET /api/v1/threads` - Threads auflisten
- `POST /api/v1/threads` - Thread erstellen
- `DELETE /api/v1/threads/:id` - Thread löschen
- `GET /api/v1/threads/:id/messages` - Messages laden
- `POST /api/v1/stream/chat` - Chat streamen (SSE)
- `GET /api/v1/agents` - Verfügbare Agents

## Technologien

- **Next.js 16** (App Router)
- **React 19**
- **TypeScript**
- **shadcn/ui** (Radix UI + Tailwind)
- **Lucide Icons**
- **Server-Sent Events** für Streaming

## Troubleshooting

### "Keine Agents verfügbar"
- Backend läuft nicht → `pipenv run api-start` im backend Ordner
- Ollama läuft nicht (für Qwen) → `ollama serve`
- Gemini API Key fehlt → `.env` im backend setzen

### CORS-Fehler
- Backend CORS ist auf `*` gesetzt (nur Dev!)
- Falls Probleme: Backend-Port in `.env.local` prüfen

### Streaming funktioniert nicht
- Browser-Kompatibilität: SSE wird von allen modernen Browsern unterstützt
- Network-Tab öffnen und `/stream/chat` Request prüfen
- Backend-Logs prüfen

