# BGB Chat Frontend

Ein modernes Next.js Frontend für den BGB (Bürgerliches Gesetzbuch) Chat-Assistenten mit KI-gestützter Rechtsberatung.

## 🚀 Features

- **Modern UI/UX**: Aufgebaute Chat-Oberfläche mit React und Next.js 15
- **Multiple AI Agents**: Unterstützung für Qwen und Gemini Modelle
- **Real-time Streaming**: SSE (Server-Sent Events) für Echtzeit-Antworten
- **Tool Call Visualization**: "Chain of Thought" Anzeige mit aufklappbaren Tool-Aufrufen
- **Thread Management**: Persistente Konversationen mit Historie
- **TypeScript**: Vollständig typisiert für bessere Entwicklererfahrung
- **Responsive Design**: Optimiert für Desktop und Mobile

## 📋 Voraussetzungen

- **Node.js**: Version 18.x oder höher
- **pnpm**: Package Manager (empfohlen) oder npm/yarn
- **Backend**: Das Backend muss laufen (siehe `../backend/README.md`)

## 🛠️ Installation

### 1. Dependencies installieren

```bash
# Mit pnpm (empfohlen)
pnpm install

# Oder mit npm
npm install

# Oder mit yarn
yarn install
```

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env.local` Datei im Frontend-Verzeichnis:

```bash
# API Konfiguration
NEXT_PUBLIC_API_URL=http://localhost:8080

# Optional: Weitere Konfigurationen
NEXT_PUBLIC_APP_NAME="BGB Chat"
```

**Wichtig:** Stellen Sie sicher, dass die `NEXT_PUBLIC_API_URL` auf Ihre laufende Backend-Instanz zeigt.

## 🚀 Starten der Anwendung

### Development Server

```bash
# Mit pnpm
pnpm dev

# Mit npm
npm run dev

# Mit yarn
yarn dev
```

Die Anwendung ist dann unter [http://localhost:3000](http://localhost:3000) verfügbar.

### Production Build

```bash
# Build erstellen
pnpm build

# Production Server starten
pnpm start
```

### Linting und Formatierung

```bash
# ESLint ausführen
pnpm lint

# TypeScript Type-Checking
pnpm type-check
```

## 📁 Projektstruktur

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root Layout mit Providers
│   ├── page.tsx             # Startseite
│   ├── globals.css          # Globale Styles
│   └── chat/                # Chat-Seite
│       └── page.tsx
├── components/              # React Komponenten
│   ├── ai-elements/        # KI-spezifische UI Komponenten
│   │   ├── conversation.tsx
│   │   ├── message.tsx
│   │   ├── response.tsx
│   │   ├── tool.tsx
│   │   └── prompt-input.tsx
│   ├── ui/                 # Basis UI Komponenten (shadcn/ui)
│   ├── app-sidebar.tsx     # Hauptsidebar
│   ├── chat-interface.tsx  # Haupt-Chat-Interface
│   └── thread-sidebar.tsx  # Thread-Verwaltung
├── lib/                    # Utility Funktionen
│   ├── api-client.ts      # Backend API Client
│   ├── chat-store.ts      # Zustand Management (Zustand)
│   ├── utils.ts           # Hilfsfunktionen
│   └── actions.ts         # Server Actions
├── hooks/                 # Custom React Hooks
│   └── use-mobile.ts
├── public/               # Statische Assets
├── next.config.ts       # Next.js Konfiguration
├── tsconfig.json        # TypeScript Konfiguration
├── tailwind.config.ts   # Tailwind CSS Konfiguration
├── components.json      # shadcn/ui Konfiguration
└── package.json         # Package Dependencies
```

## 🔧 Technologie-Stack

### Core Framework
- **Next.js 15**: React Framework mit App Router
- **React 19**: UI Library
- **TypeScript**: Type Safety

### State Management
- **Zustand**: Lightweight State Management für Chat-Daten
- **React Context**: Für globale UI-Zustände

### Styling
- **Tailwind CSS**: Utility-First CSS Framework
- **shadcn/ui**: Wiederverwendbare UI-Komponenten
- **Radix UI**: Accessible Primitives

### Weitere Libraries
- **Lucide React**: Icon Library
- **date-fns**: Date Utilities
- **clsx / tailwind-merge**: CSS Class Management

## 🎨 UI Komponenten

Das Projekt verwendet **shadcn/ui** für konsistente und zugängliche UI-Komponenten:

### Neue Komponente hinzufügen

```bash
# Beispiel: Button Komponente hinzufügen
pnpm dlx shadcn-ui@latest add button

# Mehrere Komponenten auf einmal
pnpm dlx shadcn-ui@latest add card dialog dropdown-menu
```

### Custom AI Elements

Spezialisierte Komponenten für KI-Chat:
- **Conversation**: Container für Chat-Nachrichten
- **Message**: Einzelne Nachricht (User/Assistant)
- **Response**: Formatierte AI-Antwort mit Markdown
- **Tool**: Aufklappbare Tool Call Anzeige
- **PromptInput**: Erweiterte Eingabe mit Attachments

## 📡 API Integration

Das Frontend kommuniziert mit dem Backend über REST und SSE:

### REST Endpoints

```typescript
// Threads verwalten
apiClient.listThreads()
apiClient.createThread({ title: 'Neuer Chat' })
apiClient.deleteThread(threadId)

// Nachrichten
apiClient.listMessages(threadId)
apiClient.sendMessage(threadId, { input: 'Frage', agent: 'gemini' })

// Agents
apiClient.listAgents()
```

### Streaming (SSE)

```typescript
// Streaming Chat
const stream = apiClient.streamChat({
  input: 'Was ist § 433 BGB?',
  agent: 'gemini',
  thread_id: threadId
});

for await (const event of stream) {
  if (event.type === 'token') {
    // Token verarbeiten
  } else if (event.type === 'tool_call') {
    // Tool Call anzeigen
  }
}
```

## 🎯 Verwendung

### Einen neuen Chat starten

1. Öffnen Sie [http://localhost:3000](http://localhost:3000)
2. Klicken Sie auf "Neuer Chat" in der Sidebar
3. Wählen Sie ein AI-Modell (Qwen oder Gemini)
4. Geben Sie Ihre Frage zum BGB ein
5. Der Assistent antwortet mit Rechtsinformationen und zeigt verwendete Tools an

### Thread-Verwaltung

- **Alle Threads**: In der linken Sidebar sichtbar
- **Thread umbenennen**: Klicken Sie auf den Thread-Titel
- **Thread löschen**: Drei-Punkte-Menü → Löschen
- **Thread durchsuchen**: Suche in der Sidebar

### Tool Calls anzeigen

Wenn der AI-Agent Tools verwendet (z.B. Solr-Suche oder SPARQL-Queries):
1. Die Tool Calls erscheinen als "Chain of Thought" über der Antwort
2. Klicken Sie auf einen Tool Call, um Details zu sehen:
   - **Input**: Verwendete Parameter
   - **Output**: Ergebnis des Tool-Aufrufs

## 🔒 Sicherheit

- **Input Sanitization**: Alle Benutzereingaben werden validiert
- **API Key**: Optional für Backend-Authentifizierung (X-API-Key Header)
- **CORS**: Konfiguriert im Backend
- **XSS Protection**: React's eingebauter Schutz

## 🐛 Debugging

### Development Tools

```bash
# React DevTools im Browser installieren
# TypeScript Errors anzeigen
pnpm type-check

# Console Logs aktivieren
# In api-client.ts und chat-store.ts
```

### Häufige Probleme

**Problem**: "Failed to fetch" Fehler
- **Lösung**: Backend läuft nicht oder falsche `NEXT_PUBLIC_API_URL`

**Problem**: Nachrichten werden nicht angezeigt
- **Lösung**: Cache löschen mit `localStorage.clear()` in Browser Console

**Problem**: Tool Calls fehlen
- **Lösung**: Backend-Datenbank prüfen, ob `tool_calls` JSONB-Feld gefüllt ist

## 🧪 Testing

```bash
# Unit Tests (falls konfiguriert)
pnpm test

# E2E Tests mit Playwright (falls konfiguriert)
pnpm test:e2e
```

## 📦 Deployment

### Vercel (empfohlen)

```bash
# Vercel CLI installieren
npm i -g vercel

# Deployen
vercel
```

### Docker

```bash
# Dockerfile erstellen (nicht im Repository)
docker build -t bgb-frontend .
docker run -p 3000:3000 bgb-frontend
```

### Manuelle Deployment

```bash
# Production Build
pnpm build

# Output-Verzeichnis (.next) auf Server kopieren
# Node.js Server starten
node .next/standalone/server.js
```

## 🤝 Beitragen

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Changes committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📝 Entwicklungsrichtlinien

- **TypeScript**: Alle neuen Dateien müssen typisiert sein
- **ESLint**: Code muss ESLint-Regeln entsprechen
- **Komponenten**: Nutzen Sie shadcn/ui für konsistente UI
- **State**: Verwenden Sie Zustand für globalen State
- **API**: Alle Backend-Calls über `api-client.ts`

## 📄 Lizenz

Dieses Projekt ist Teil des BGB Chat Projekts.

## 🆘 Support

- **Issues**: GitHub Issues für Bugs und Feature Requests
- **Dokumentation**: Siehe `../backend/API_README.md` für API-Details
- **Backend Setup**: Siehe `../backend/README.md`

## 🔗 Verwandte Ressourcen

- [Next.js Dokumentation](https://nextjs.org/docs)
- [React Dokumentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Zustand](https://github.com/pmndrs/zustand)

---

**Entwickelt mit ❤️ für besseren Zugang zu BGB-Rechtsinformationen**

