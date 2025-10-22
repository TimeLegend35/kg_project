# 🔄 Frontend Migration: Vercel AI SDK → FastAPI Backend

## ✅ Was wurde geändert

### 1. Custom Provider erstellt (`lib/ai/bgb-provider.ts`)
- **Ersetzt**: Vercel AI Gateway (xAI/Grok Models)
- **Nutzt jetzt**: Direkten Stream von FastAPI Backend
- Implementiert `LanguageModelV1` Interface für AI SDK Kompatibilität
- Konvertiert Backend-Chunks (text, thinking, tool_call) zu AI SDK Format

### 2. Provider umgestellt (`lib/ai/providers.ts`)
- **Entfernt**: `@ai-sdk/gateway` und `@ai-sdk/xai`
- **Nutzt**: Custom `bgbProvider` für alle Model-Typen
- Test-Mocks bleiben für Playwright Tests

### 3. Chat Actions vereinfacht (`app/(chat)/actions.ts`)
- `generateTitleFromUserMessage()` nutzt jetzt `generateTitleWithBackend()`
- **Kein AI SDK `generateText()` mehr**
- Gleiches FastAPI Backend Endpoint für Titel wie für Chat

### 4. Chat Route komplett neu (`app/(chat)/api/chat/route.ts`)
- **Entfernt**: Komplexe Vercel AI SDK Logik (500+ Zeilen)
- **Vereinfacht**: ~150 Zeilen direkter Backend-Integration
- Nutzt `streamChat()` von unserem API Client
- Konvertiert Chunks on-the-fly zu AI SDK Format für Frontend-Kompatibilität

### 5. Dependencies aufgeräumt (`package.json`)
- **Entfernt**: 
  - `@ai-sdk/gateway` (Vercel Gateway)
  - `@ai-sdk/xai` (xAI/Grok Provider)
- **Behalten**: 
  - `@ai-sdk/provider` (Types für Custom Provider)
  - `@ai-sdk/react` (React Hooks wie `useChat`)
  - `ai` (Core SDK für Stream-Handling)

## 🎯 Architektur jetzt

```
┌─────────────────────────────────────────────────┐
│  Next.js Frontend (Vercel AI Chatbot Template) │
│  • useChat Hook (AI SDK React)                  │
│  • Custom BGBLanguageModel                      │
│  • Chat UI Components (unverändert)             │
└────────────────┬────────────────────────────────┘
                 │
                 │ POST /api/chat
                 │ { id, message }
                 ▼
┌─────────────────────────────────────────────────┐
│  Chat Route (app/api/chat/route.ts)             │
│  • Speichert Message in DB (Drizzle)            │
│  • Ruft FastAPI Backend                         │
│  • Konvertiert Stream zu AI SDK Format          │
└────────────────┬────────────────────────────────┘
                 │
                 │ POST /chat/stream
                 │ { chat_id, message }
                 ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Backend + LangGraph                    │
│  • Lädt History aus PostgreSQL                  │
│  • Qwen Agent mit Tools (Solr + SPARQL)         │
│  • Streamt: text, thinking, tool_call, tool_result│
└─────────────────────────────────────────────────┘
```

## 🔌 Stream-Flow

### Backend → Frontend Konvertierung

```typescript
// Backend sendet:
{ type: 'text', content: 'Ein Kaufvertrag...' }
{ type: 'thinking', thinking_content: 'Ich suche nach...' }
{ type: 'tool_call', tool_call: { name: 'bgb_solr_search', ... } }
{ type: 'tool_result', tool_result: { output: '...' } }
{ type: 'done' }

// Route konvertiert zu AI SDK Format:
{ type: 'text-delta', textDelta: 'Ein Kaufvertrag...' }
{ type: 'text-delta', textDelta: '💭 Ich suche nach...' }
{ type: 'tool-call', toolName: 'bgb_solr_search', ... }
{ type: 'tool-result', result: '...' }
{ type: 'finish', finishReason: 'stop' }

// Frontend useChat empfängt AI SDK Format
// → Funktioniert mit allen existierenden UI Components!
```

## 📝 Titel-Generierung

**Vorher:**
```typescript
generateText({
  model: provider.languageModel("xai/grok-2-1212"),
  system: "...",
  prompt: message
})
```

**Jetzt:**
```typescript
generateTitleWithBackend(chatId, userMessage)
// → Nutzt gleichen /chat/stream Endpoint
// → Einfacher Prompt für Titel
// → Kein separates Model nötig
```

## ✅ Vorteile

1. **Keine Vendor Lock-in**: Unabhängig von Vercel AI Gateway
2. **Ein Backend**: FastAPI + LangGraph für alles
3. **Volle Kontrolle**: Eigene Tools, eigenes Model (Qwen)
4. **Einfacher Code**: ~70% weniger Code in Chat Route
5. **Kompatibilität**: Alle Frontend-UI Components funktionieren weiter
6. **Shared DB**: PostgreSQL für Backend & Frontend

## 🧪 Testing

Alle existierenden Frontend-Tests sollten weiterhin funktionieren, da:
- AI SDK React Hooks (`useChat`) unverändert
- UI Components unverändert
- Nur Provider-Implementierung ausgetauscht

## 📦 Installation

```bash
cd packages/frontend

# Alte Dependencies entfernen
pnpm remove @ai-sdk/gateway @ai-sdk/xai

# Dependencies neu installieren
pnpm install

# Frontend starten
pnpm dev
```

## 🎉 Fertig!

Das Frontend nutzt jetzt **100% unser FastAPI + LangGraph Backend** mit:
- ✅ Qwen Agent statt xAI/Grok
- ✅ BGB Tools (Solr + SPARQL)
- ✅ Thinking Mode sichtbar im Frontend
- ✅ Shared PostgreSQL
- ✅ Alle UI Features erhalten

