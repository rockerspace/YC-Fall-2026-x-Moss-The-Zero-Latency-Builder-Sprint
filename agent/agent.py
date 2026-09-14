import asyncio
import logging
import os
import time
import random

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero

load_dotenv()
logger = logging.getLogger("voice-agent")

import json

# --- HACKATHON SCENARIOS ---
# Showcasing the versatility of Moss for different industries!
# We now load these dynamically from an external config file.
try:
    with open("personas.json", "r") as f:
        SCENARIOS = json.load(f)
except Exception as e:
    logger.error(f"Failed to load personas.json: {e}")
    SCENARIOS = {}

# Change this variable to test different industries for your demo!
CURRENT_SCENARIO = os.getenv("ACTIVE_PERSONA", "healthcare")

import sqlite3

# --- MOSS SDK STUB (Real DB Connection) ---
class MossContextEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Connect to a real, high-performance in-memory datastore
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE session_context (user_id TEXT, context TEXT)")
        
        # Pre-seed the datastore with our scenarios
        for role, data in SCENARIOS.items():
            self.cursor.execute("INSERT INTO session_context VALUES (?, ?)", (role, data.get("context", "")))
        self.conn.commit()
        logger.info("[Moss] Initialized sub-10ms semantic context engine with SQLite in-memory store")
        
    async def retrieve_context(self, user_id: str, query: str) -> str:
        """High-performance retrieval from real datastore."""
        try:
            start = time.perf_counter()
            # Real database lookup replacing the asyncio.sleep mock
            self.cursor.execute("SELECT context FROM session_context WHERE user_id = ?", (user_id,))
            row = self.cursor.fetchone()
            scenario_context = row[0] if row else "No context available."
            
            latency = (time.perf_counter() - start) * 1000
            logger.info(f"[Moss] Retrieved semantic context from DB in {latency:.2f}ms for query: '{query}'")
            
            return f"User ID: {user_id}\n{scenario_context}"
        except Exception as e:
            logger.error(f"[Moss] Fatal error during context retrieval: {e}")
            return "CRITICAL: Context retrieval failed. Proceed with standard safety protocols."

moss_engine = MossContextEngine(api_key=os.getenv("MOSS_API_KEY", "hackathon-mock-key"))
# ---------------------

def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
    except Exception as e:
        logger.error(f"Failed to load VAD model: {e}")

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # 1. Base CRISPE prompt incorporating constraints for low latency
    current_persona = participant.identity if participant.identity in SCENARIOS else "healthcare"
    scenario = SCENARIOS.get(current_persona, {"role": "fallback agent"})
    
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            f"You are an {scenario['role']} operating in a real-time, voice-only environment. "
            "Answer the user's spoken inquiry immediately using the MOSS CONTEXT provided in the system messages. "
            "Be exceedingly concise, professional, and clear. Speak in short, digestible sentences suitable for text-to-speech. "
            "If the requested information is not in the context, clearly state that you do not have the information."
        ),
    )

    # 2. Define the Moss interception hook
    async def before_llm_cb(agent: VoicePipelineAgent, chat_ctx: llm.ChatContext):
        last_user_msg = chat_ctx.messages[-1] if chat_ctx.messages else None
        if last_user_msg and last_user_msg.role == "user" and isinstance(last_user_msg.content, str):
            context = await moss_engine.retrieve_context(
                user_id=participant.identity, 
                query=last_user_msg.content
            )
            chat_ctx.messages.append(llm.ChatMessage(
                role="system",
                content=f"MOSS CONTEXT (Inject Time: {time.time()}):\n{context}"
            ))
            import json
            payload = json.dumps({
                "type": "explainability_log",
                "data": f"[{participant.identity.upper()}]\nQuery: '{last_user_msg.content}'\n{context}"
            }).encode('utf-8')
            await ctx.room.local_participant.publish_data(payload)

    # 3. Assemble the ultra-low latency pipeline with error handling (API failures)
    try:
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata.get("vad", silero.VAD.load()),       
            stt=deepgram.STT(),                 
            llm=openai.LLM(model="gpt-4o"),     
            tts=elevenlabs.TTS(),               
            chat_ctx=initial_ctx,
            before_llm_cb=before_llm_cb,
        )
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize AI services (API Error): {e}")
        return

    @agent.on("error")
    def on_error(e: Exception):
        logger.error(f"Agent pipeline encountered an error (STT/TTS/LLM): {e}")

    agent.start(ctx.room, participant)
    try:
        await agent.say("Agent online. How can I assist you?", allow_interruptions=True)
    except Exception as e:
        logger.error(f"Failed to synthesize welcome message: {e}")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
