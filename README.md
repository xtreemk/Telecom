# LiveBox AI — Voice-First Telecom Customer Care (Development Build v0.4)

LiveBox AI is being developed as a voice-first conversational customer-care platform for telecommunications providers. The goal is for a customer to call customer care, speak naturally, and get help without navigating keypad menus or listening to long IVR instructions. The first product scenario is an MTN Nigeria customer-care call (333); the platform is intended to expand to additional operators and international markets over time.

The current v0.4 package is an early development build of that product. It uses sample customer records and simulated operator services so the conversation, orchestration, authorization, audit, escalation, and reporting flows can be developed and tested safely. It is **not connected to MTN, a live carrier network, real subscriber records, or production telecom APIs**. Those integrations and production controls are future delivery work, not the product's end goal.

## Product direction

- **Voice-first customer care:** callers explain what they need in ordinary speech instead of selecting keypad options.
- **Natural, continuous conversations:** LiveBox keeps context across turns, handles follow-up questions, and is designed for interruption and natural turn-taking.
- **Personalized, authorized service:** where the operator has permission to use the information, LiveBox can greet a known customer by name and use their profile to help.
- **Multilingual from the start:** the initial Nigeria language set is English, Nigerian Pidgin, Yorùbá, Hausa, and Igbo. LiveBox should detect language changes during a conversation and respond in the customer's current language, including ordinary code-switching.
- **Useful proactive assistance:** LiveBox can offer relevant help and, where customer consent and operator rules permit, relevant bundles or services. It should identify itself as an AI assistant and never depend on customers mistaking it for a human.
- **International expansion:** country and operator integrations, languages, policies, and service catalogues will be added market by market through replaceable integration adapters.

## Architecture

Customer calls customer care or uses a digital channel
  ↓
Voice-first channel (web chat is the current development interface)
  ↓
LiveBox AI Orchestrator (Conversational Engine)
  ↓
Intent Router → Language Detector → Context Manager
  ↓
Specialist Agent
  ↓
Authorized operator integration
  ↓
Operator customer-care, billing, network, and service systems
  ↓
Result
  ↓
Audit Log
  ↓
Responder (Short Spoken Responses)
  ↓
Spoken or digital customer response

In v0.4, the operator integration layer is simulated and uses sample data. The architecture is being developed so real operator adapters can be added without changing the customer conversation flow.

## Core v0.4 Features

### Conversational Engine
- Multi-turn conversation with context retention across messages
- Conversation context carries intent history, tool results, language, customer profile
- Natural follow-ups (e.g., "what about my data?" after balance inquiry)
- Short, spoken-style responses designed for voice

### Interruption / Barge-in Foundation
- Barge-in state and conversation history are retained across turns
- The current endpoint exercises interruption in the development environment; live playback interruption requires a connected streaming voice provider

### Voice Channel and Integration Readiness
- Voice session management (call start, call end, call lifecycle)
- Speech input/output abstraction layer for future SIP, carrier, and voice-provider connections
- Browser-based speech demonstration for development; this is not yet a live telephone service
- All existing web/chat flows reuse the same conversational brain

### Five-Language Capability
- **English** (default)
- **Nigerian Pidgin** (markers: wetin, abeg, na, de, pikin, how far, wahala)
- **Yoruba** (markers: ṣé, bà, rẹ̀, ẹni, ní, kí, lò, wá, báwo)
- **Hausa** (markers: ina, yaya, ka, ki, kafin, kuma, don, sune, musa, iya, mata)
- **Igbo** (markers: nna, m, gị, ka, ị, chere, nke, ụfọdụ, biko, kedu)
- Automatic language detection (continuously, not a menu)
- Language switching when customer switches
- Code-switching handling (mixed-language messages)
- Unknown-language fallback (respond in English, ask to repeat)

### Personalized Greeting
- "Hello Aisha Bello, how may I help you today?"
- Production greetings must use customer information only after the operator has authorized identity matching and data access
- The current interface displays greetings as text and can speak responses using the browser's speech engine

### Controlled Proactive Engagement
- Relevant offers/services introduced when appropriate
- Marketing/consent controls (only offer with consent, track consent)
- Assistant identifies as AI ("I'm LiveBox AI, your telecom assistant.")
- No uncontrolled advertising

## Current development capabilities
- Support Agent
- Billing/Transaction Agent
- Network Agent
- Complaint Agent
- Escalation Agent
- Reporting Agent

## Current simulated service tools
- customer lookup
- data balance lookup
- transaction lookup
- network diagnostic
- complaint creation
- bundle remediation

These tools currently operate against the included development data. They are not live MTN services.

## Security foundations and production requirements
- Tool access controlled by agent permissions
- Validation through Pydantic models
- No hard-coded secrets
- Environment-based configuration settings
- Audit logging for meaningful automated actions
- Production deployment will additionally require operator-approved identity and access controls, privacy and retention rules, availability and incident processes, and country-specific compliance review

## Project structure

```text
LiveBox_AI_Telecom_MVP_v0_4/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── main.py
│   ├── livebox.db (created locally on first launch; not included in the package)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── seed_data.py
│   │   ├── agent_config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── chat.py
│   │   │       ├── conversations.py
│   │   │       ├── customers.py
│   │   │       ├── escalations.py
│   │   │       ├── health.py
│   │   │       ├── knowledge.py
│   │   │       ├── reports.py
│   │   │       ├── tickets.py
│   │   │       └── voice.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   ├── billing_agent.py
│   │   │   ├── complaint_agent.py
│   │   │   ├── escalation_agent.py
│   │   │   ├── network_agent.py
│   │   │   ├── reporting_agent.py
│   │   │   └── support_agent.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── permissions.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── audit_service.py
│   │   │   ├── conversation_context.py
│   │   │   ├── customer_service.py
│   │   │   ├── intent_router.py
│   │   │   ├── knowledge_service.py
│   │   │   ├── language_detector.py
│   │   │   ├── orchestrator.py
│   │   │   ├── proactive_engagement.py
│   │   │   ├── responder.py
│   │   │   ├── speech_io.py
│   │   │   ├── ticket_service.py
│   │   │   └── voice_session.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── complaint_tools.py
│   │   │   ├── customer_tools.py
│   │   │   ├── network_tools.py
│   │   │   └── remediation_tools.py
│   │   └── main.py
│   └── tests/
│       ├── test_reporting_and_escalations.py
│       ├── test_v03_regression.py
│       ├── test_v04_conversation.py
│       ├── test_v04_language.py
│       ├── test_v04_proactive.py
│       └── test_v04_voice.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
```

## Backend startup

Open a terminal in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Frontend startup

Open a second terminal in the project root:

```powershell
cd frontend
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

## API endpoints

### Health
- GET /api/health

### Customers
- GET /api/customer/{phone}
- PATCH /api/customer/{phone}/consent — `{marketing_consent: boolean}`

### Chat (multi-turn)
- POST /api/chat — `{phone, message, conversation_id?, session_id?}`

### Voice Session
- POST /api/voice/start — `{phone}` → `{session_id, greeting, ssml, language, customer_name}`
- POST /api/voice/speech — `{session_id, text}` → `{reply, ssml, phonetic_markers, language, intent, action}`
- POST /api/voice/barge — `{session_id}` → barge-in response
- POST /api/voice/no-input — `{session_id}` → one silence prompt and, only when permitted, a relevant offer
- POST /api/voice/end — `{session_id}` → ends session
- GET /api/voice/sessions — list active voice sessions

### Conversations
- GET /api/conversations/{phone} — full conversation history
- GET /api/conversations/{phone}/context — context summary for follow-ups

### Knowledge
- GET /api/knowledge/search?q=<query> — search knowledge entries
- GET /api/knowledge?category=<cat> — list all entries

### Tickets
- GET /api/tickets

### Reports
- GET /api/reports/overview
- GET /api/reports/intents
- GET /api/reports/agents
- GET /api/reports/escalations
- GET /api/reports/transactions

### Escalations
- GET /api/escalations

## Initial Nigeria Language Set

These five languages define the initial Nigerian customer-care experience. The v0.4 language detector is an early implementation and must be validated with real speakers and production speech-recognition services before operator launch. Additional languages and locale behavior are part of the international market rollout.

| Code | Language | Greeting | Example Markers |
|------|----------|----------|-----------------|
| en | English | Hello | — |
| pid | Nigerian Pidgin | How far | wetin, abeg, na, de, wahala |
| yo | Yoruba | Bawo ni | ṣé, bà, rẹ̀, ẹni, báwo |
| ha | Hausa | Sannu | ina, yaya, kafin, kuma, sune |
| ig | Igbo | Nnoọ | nna, gị, ka, ị, biko, kedu |

## Proactive Engagement

- Offers only made when `marketing_consent = true` on customer profile
- Frequency limited in persistent storage: max 1 per conversation session, max 3 per UTC day, 4-hour cooldown
- Bundle-specific offers are limited to customers on the matching bundle
- Context-aware: offers matched to recent intent (e.g., data boost after balance check)
- Assistant always identifies as AI: "I'm LiveBox AI, your telecom assistant."

## Barge-in / Interruption

- `POST /api/voice/barge` exercises the interruption state in the development adapter and returns a brief acknowledgment
- Actual playback interruption and natural telephone turn-taking require a connected streaming voice provider

## Voice Session Lifecycle

1. **Start** — `POST /api/voice/start` with phone → returns session_id + personalized greeting
2. **Speech** — `POST /api/voice/speech` with session_id + transcribed text → returns spoken response with SSML
3. **Barge-in** — `POST /api/voice/barge` with session_id → exercises the development interruption response
4. **No input** — `POST /api/voice/no-input` after the provider's silence timeout → sends one useful prompt
5. **End** — `POST /api/voice/end` with session_id → saves conversation, returns farewell

## Current Voice Demonstration and Telephone Integration Path

- The development backend accepts recognized text and returns responses and SSML; it is not connected to a phone network
- The browser demonstration can read responses aloud with its built-in speech engine
- Where the browser supports speech recognition, **Speak** captures one utterance; typing remains available as a fallback
- The development UI has controls to exercise silence handling and barge-in flows
- Available voices and their quality depend on the browser and voices installed on the computer
- A live customer-care number, carrier/SIP routing, production speech recognition and speech generation, and streaming interruption are future integration milestones

## Chat history in the browser

- The demo saves each customer's visible chat and conversation ID in the browser's local storage, so refreshing the page or reopening it in the same browser profile restores the messages.
- Browser storage is separate for each browser and computer. Switching to another browser does not transfer the chat history.
- If the page refreshes while a request is still being processed, send that request again after the page returns; requests already completed remain visible.

## Running Tests

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Test Categories

- `test_v03_regression.py` — All v0.3 tests must pass
- `test_v04_conversation.py` — Multi-turn, context retention, greeting
- `test_v04_language.py` — Detection, switching, code-switching, fallback
- `test_v04_voice.py` — Voice lifecycle, no-input prompt, mock interruption, SSML escaping
- `test_v04_proactive.py` — Proactive offers, consent controls

## Delivery Path: Development to Operator and International Deployment

1. **Conversation foundation:** continue improving multi-turn service flows, language switching, consent handling, authorization, audit, escalation, and frontend reliability against safe development data.
2. **Nigeria operator pilot:** agree on an operator sandbox and approved APIs, then connect identity, customer care, billing, bundles, network diagnostics, and complaint workflows through operator-specific adapters. Add telephony routing, production speech services, monitoring, security review, and human handoff.
3. **Production readiness:** complete load, resilience, privacy, security, accessibility, language-quality, and operational acceptance testing with the operator before serving real callers.
4. **International rollout:** add markets through configuration and adapters for each operator, including local languages, voice providers, customer-care policies, service catalogues, regulatory requirements, data residency, and support operations.

The order, scope, and timing of market launches depend on operator partnerships, approved system access, local requirements, and validation with customers in each market.

## Local notes

The development backend creates `backend/livebox.db` on first launch. Sample customer profiles, simulated balance changes, tickets, and audit events persist across restarts. This local database is for development and is not a production subscriber database. Set `LIVEBOX_DB_PATH` to store it elsewhere.

The v0.3 fallback was not included in the uploaded ZIP. Keep your existing v0.3 folder unchanged alongside this project if you need a rollback copy.
