# 🎙️ Zero-Latency Voice Builder Sprint (Track 1)

This repository contains our submission for the **YC Fall 2026 x Moss Hackathon (Track 1)**. 

We have built a mission-critical, real-time Voice AI Platform designed for field workers, dispatchers, and healthcare professionals. By replacing traditional high-latency vector databases with **Moss** and substituting standard websockets with **LiveKit WebRTC**, we have successfully created an intelligent, interruptible voice agent capable of operating with sub-500ms Turn-Around Time (TAT).

---

## 🌟 Key Features

* **Ultra-Low Latency Transport:** Full-duplex audio streaming powered by LiveKit WebRTC SFU, avoiding standard HTTP/WebSocket bottlenecks.
* **Sub-10ms Semantic Context:** Integrates the Moss Context Engine to instantly inject real-time session state and knowledge (like technical manuals or live logs) into the LLM before generation.
* **Barge-In / Interruptibility:** Utilizes Silero Voice Activity Detection (VAD) via the LiveKit Agents SDK to instantly halt the Text-to-Speech queue when the user interrupts the agent.
* **Next.js Admin Dashboard:** A slick, real-time web portal that securely mints session tokens and allows admins to view connection metrics and AI explainability logs.
* **AI Explainability (SEC-303):** The backend streams LiveKit Data Packets containing the exact Moss context traces used to generate the agent's response, rendering them on the frontend for traceability.

---

## 🏗️ Architecture Overview

The system is split into two main components:

1. **`/frontend` (Next.js 15, TailwindCSS, LiveKit Components)**
   * Securely generates JWT tokens via `/api/token`.
   * Manages the WebRTC connection via `<LiveKitRoom>`.
   * Displays agent status, audio visualizers, and real-time Moss explainability logs.
2. **`/agent` (Python 3.12, LiveKit Agents SDK)**
   * The "Voice Orchestrator". Connects to the room and listens to the user.
   * **STT:** Deepgram (Nova-2) for lightning-fast transcription.
   * **Context:** Moss SDK intercepts the pipeline via `before_llm_cb` to fetch semantic context in <10ms.
   * **LLM:** OpenAI GPT-4o powers the conversational logic based on the CRISPE prompt framework.
   * **TTS:** ElevenLabs generates ultra-realistic voice output.

---

## 🚀 Quick Start Guide

### 1. Start the Voice Orchestrator (Backend)

Navigate to the `agent/` directory:
```bash
cd agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the `.env.example` file to `.env` and add your API keys:
```bash
cp .env.example .env
# Edit .env to add LiveKit, Deepgram, OpenAI, and ElevenLabs keys
```

Run the agent worker:
```bash
python agent.py dev
```

### 2. Start the Dashboard (Frontend)

Open a new terminal and navigate to the `frontend/` directory:
```bash
cd frontend
npm install
```

Copy the `.env.local.example` to `.env.local`:
```bash
cp .env.local.example .env.local
# Edit .env.local to add your LiveKit Cloud Project URL, API Key, and API Secret
```

Run the Next.js development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser and click **Start Secure Session**!

---

## 🛡️ Continuous Integration (CI)

This repository is equipped with GitHub Actions located in `.github/workflows`:
- **Frontend Build Check:** Ensures Next.js builds successfully on every pull request.
- **Backend Python Check:** Verifies Python syntax and validates dependencies.

See the [PRD_Track1.md](./PRD_Track1.md) file for a detailed look at the functional, non-functional, and security requirements guiding this architecture.
