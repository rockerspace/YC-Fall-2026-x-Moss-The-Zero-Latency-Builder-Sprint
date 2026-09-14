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

# --- HACKATHON SCENARIOS ---
# Showcasing the versatility of Moss for different industries!
SCENARIOS = {
    "field_worker": {
        "role": "expert field operations assistant",
        "context": "[ACTIVE SESSION: Assignment 42 - HVAC Repair]\nRecent logs: Compressor valve pressure dropped below threshold.\nProtocol: Inform user to wear safety goggles before inspecting the valve."
    },
    "healthcare": {
        "role": "medical triage assistant",
        "context": "[ACTIVE SESSION: Patient ER Intake]\nVitals: Heart rate 110bpm, Blood Pressure 140/90.\nProtocol: Ask patient about chest pain duration. Recommend immediate EKG."
    },
    "dispatch": {
        "role": "emergency dispatch coordinator",
        "context": "[ACTIVE SESSION: Incident 992 - Highway Collision]\nLocation: I-95 Northbound, Mile marker 42.\nProtocol: Dispatch 2 ambulances and 1 fire engine. Keep caller calm."
    },
    "customer_support": {
        "role": "customer support specialist",
        "context": "[ACTIVE SESSION: Billing Inquiry - Acct #7782]\nStatus: Overdue balance of $120.50.\nProtocol: Offer a 3-month payment plan. Do not charge late fees."
    }
}

# Change this variable to test different industries for your demo!
CURRENT_SCENARIO = "healthcare"

# --- MOSS SDK STUB ---
class MossContextEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("[Moss] Initialized sub-10ms semantic context engine")
        
    async def retrieve_context(self, user_id: str, query: str) -> str:
        """Simulates <10ms retrieval of semantic context and user state."""
        start = time.perf_counter()
        await asyncio.sleep(0.005) # Simulate 5ms retrieval
        latency = (time.perf_counter() - start) * 1000
        logger.info(f"[Moss] Retrieved semantic context in {latency:.2f}ms for query: '{query}'")
        
        return f"User ID: {user_id}\n{SCENARIOS[CURRENT_SCENARIO]['context']}"

moss_engine = MossContextEngine(api_key=os.getenv("MOSS_API_KEY", "hackathon-mock-key"))
# ---------------------

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # 1. Base CRISPE prompt incorporating constraints for low latency
    scenario = SCENARIOS[CURRENT_SCENARIO]
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            f"You are an {scenario['role']} operating in a real-time, voice-only environment. "
            "Answer the user's spoken inquiry immediately using the MOSS CONTEXT provided in the system messages. "
            "Be exceedingly concise, professional, and clear. Speak in short, digestible sentences suitable for text-to-speech. "
            "If the requested information is not in the context, clearly state that you do not have the information."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

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
                "data": f"[{CURRENT_SCENARIO.upper()}]\nQuery: '{last_user_msg.content}'\n{context}"
            }).encode('utf-8')
            await ctx.room.local_participant.publish_data(payload)

    # 3. Assemble the ultra-low latency pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],       
        stt=deepgram.STT(),                 
        llm=openai.LLM(model="gpt-4o"),     
        tts=elevenlabs.TTS(),               
        chat_ctx=initial_ctx,
        before_llm_cb=before_llm_cb,
    )

    agent.start(ctx.room, participant)
    await agent.say("Agent online. How can I assist you?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
