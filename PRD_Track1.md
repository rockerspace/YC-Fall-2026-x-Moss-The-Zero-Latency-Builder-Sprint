# Product Requirements Document (PRD): Real-Time Voice & Conversational AI Platform (Track 1)

## 1. Executive Summary
This project aims to build a high-performance, low-latency Voice AI platform designed for mission-critical environments such as healthcare, emergency dispatch, and field operations. By leveraging **Moss** for sub-10ms context retrieval, **LiveKit** for ultra-low latency WebRTC streaming, and **Next.js** for robust administrative and frontend control, the system provides field workers with an intelligent voice agent that responds instantly, possesses real-time knowledge, and operates with human-like fluidity.

## 2. Problem Statement
Existing voice AI solutions suffer from high "glass-to-glass" latency (often >2 seconds), making them impractical for high-stakes environments. Field workers, doctors, and dispatchers cannot afford to wait for a cloud-based LLM to process information, nor can they navigate complex UI menus while their hands are busy. There is a critical need for a voice-first system that offers sub-second response times and instantaneous access to technical or medical documentation.

## 3. Goals & Objectives
*   **Ultra-Low Latency:** Achieve sub-10ms context retrieval using Moss and minimize total turn-around time (TAT) to under 500ms.
*   **Real-Time Audio Pipeline:** Utilize LiveKit WebRTC SFU to eliminate transport bottlenecks.
*   **Hands-Free Utility:** Enable 100% voice-operated workflows for field and clinical staff.
*   **Real-Time Knowledge & Explainability:** Provide agents with live manuals and log references for every generated response.
*   **Data Compliance:** Enforce strict consent management and data retention policies for voice recordings.

---

## 4. Requirements & Acceptance Criteria

### 4.1 Functional Requirements (FR)
| ID | Requirement | Acceptance Criteria |
| :--- | :--- | :--- |
| **FR-101** | **Real-Time Voice Streaming** | The system must use LiveKit WebRTC SFU for full-duplex communication with <50ms transport latency under normal network conditions. |
| **FR-102** | **Instant Context Retrieval** | The Moss Engine must fetch user context and session history in < 10ms (P95). |
| **FR-103** | **Administrative Dashboard** | A Next.js web application must allow admins to view live agents, monitor latency metrics, and provide a web-based voice client. |
| **FR-104** | **Interruptibility (Barge-in)** | The agent must halt TTS playback within 150ms of detecting user speech via LiveKit VAD. |
| **FR-105** | **Dynamic Knowledge Access** | The system must ingest and query external RAG sources, combining them with Moss hot-context. |

### 4.2 Non-Functional Requirements (NFR)
| ID | Requirement | Acceptance Criteria |
| :--- | :--- | :--- |
| **NFR-201** | **End-to-End Latency** | Total response latency (STT + LLM + TTS) must not exceed 800ms, with a target of 500ms. |
| **NFR-202** | **Scalability** | The LiveKit and Next.js infrastructure must auto-scale to support 1,000+ concurrent voice streams. |
| **NFR-203** | **High Availability** | The system must maintain 99.9% uptime, utilizing redundant LiveKit nodes. |

### 4.3 Security & Compliance (SEC)
| ID | Requirement | Acceptance Criteria |
| :--- | :--- | :--- |
| **SEC-301** | **Consent Management** | The Next.js frontend and voice client must capture explicit user consent before initiating WebRTC streams. State stored in Moss. |
| **SEC-302** | **Data Erasure & Retention** | Automated data lifecycle policies must purge or anonymize raw voice recordings within 24 hours of session end. |
| **SEC-303** | **AI Explainability** | The Orchestrator must append a metadata payload to every TTS response indicating the exact Moss/Vector DB source referenced. |

---

## 5. System Architecture Overview

The system transitions from a custom gateway to an industry-standard LiveKit ecosystem:
1.  **Client & Admin Layer (Next.js & React Native):** A Next.js web app serves as the main administrative dashboard and web-based voice client, alongside a React Native mobile client. Both connect via LiveKit SDKs.
2.  **Streaming Gateway (LiveKit WebRTC SFU):** Replaces custom Rust/Envoy gateways to manage high-throughput, real-time WebRTC audio streams natively.
3.  **Orchestration Engine (LiveKit Agents SDK):** The Python/Node orchestrator leverages the LiveKit Agents SDK to manage room events, VAD, and route audio dynamically between STT, LLM, and TTS pipelines.
4.  **Context Layer (Moss):** High-speed memory store for sub-10ms retrieval of session state, consent flags, and RAG metadata.
5.  **Inference Pipeline:** Deepgram (STT), GPT-4o / Claude 3.5 Sonnet (LLM), and ElevenLabs (TTS).

---

## 6. Architecture-to-Requirements Traceability Matrix

| Requirement ID | Architectural Component | Implementation Details |
| :--- | :--- | :--- |
| **FR-101** (Streaming) | LiveKit WebRTC SFU | Audio ingest and egress via WebRTC rooms. |
| **FR-102** (Context Retrieval) | Moss Context Engine | In-memory key-value and vector fetching for prompt injection. |
| **FR-103** (Web Dashboard) | Next.js Frontend App | Web portal for agent management and live WebRTC streaming. |
| **FR-104** (Barge-in) | LiveKit Agents SDK | VAD triggers interrupt signals to halt the TTS playback queue. |
| **SEC-301** (Consent) | Next.js App & Moss | UI captures consent; Orchestrator validates consent flag in Moss before recording. |
| **SEC-302** (Data Erasure) | Vector DB / Cloud Storage | CRON jobs or TTL indexes automatically expire audio blobs/logs after 24h. |
| **SEC-303** (Explainability) | Voice Orchestrator | Logs RAG chunk IDs and Moss keys alongside the generated LLM text payload. |

---

## 7. Prompt Engineering Specifications (CRISPE Framework)

The Voice Orchestrator relies on structured prompt templates to ensure the LLM generates concise, accurate, and explainable responses suitable for low-latency voice delivery.

**Framework: CRISPE (Capacity and Role, Insight, Statement, Personality, Experiment/Output)**

### Base System Prompt Template
```markdown
[CAPACITY AND ROLE]
You are an expert field operations and medical dispatch AI assistant operating in a real-time, voice-only environment. 

[INSIGHT]
The user is currently on an active assignment. 
- Recent Session Context (via Moss): {moss_session_context}
- Retrieved Knowledge (via Vector DB): {rag_documentation_chunks}
- User Consent Status: {consent_status}

[STATEMENT]
Answer the user's spoken inquiry immediately using the provided knowledge and session context. If the requested information is not in the context, clearly state that you do not have the information.

[PERSONALITY]
Be exceedingly concise, professional, and clear. Speak in short, digestible sentences suitable for text-to-speech. Do not use markdown, bullet points, or complex formatting.

[EXPERIMENT / OUTPUT]
Output your response as raw text. Ensure your response does not exceed 3 sentences to maintain ultra-low latency playback. 
```

---

## 8. Data Flow & Security Lifecycle

1.  **Ingestion:** User grants consent via the Next.js app (SEC-301). LiveKit establishes a secure WebRTC room.
2.  **Processing:** LiveKit Agents SDK routes audio to STT. Text is enriched with <10ms Moss context.
3.  **Generation:** LLM generates text. The Orchestrator logs the exact Moss/RAG IDs used (SEC-303).
4.  **Delivery:** Text is synthesized to speech (TTS) and streamed back via LiveKit.
5.  **Retention:** Audio recordings and transcriptions are tagged with a 24-hour TTL, ensuring automatic compliance with data erasure policies (SEC-302).
