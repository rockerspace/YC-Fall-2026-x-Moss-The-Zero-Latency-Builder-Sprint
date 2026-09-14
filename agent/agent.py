import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero

load_dotenv()
logger = logging.getLogger("voice-agent")

# --- MOSS SDK STUB ---
# In a real environment, this would import the Moss SDK and connect to the Moss cluster
class MossContextEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("[Moss] Initialized sub-10ms semantic context engine")
        
    async def retrieve_context(self, user_id: str, query: str) -> str:
        """Simulates <10ms retrieval of semantic context and user state."""
        start = time.perf_counter()
        
        # Simulate network/retrieval latency (e.g., 5-8ms)
        await asyncio.sleep(0.005) 
        
        latency = (time.perf_counter() - start) * 1000
        logger.info(f"[Moss] Retrieved semantic context in {latency:.2f}ms for query: '{query}'")
        
        # Simulated context returned by Moss based on user state
        return (
            f"[ACTIVE SESSION: Assignment 42 - HVAC Repair]\n"
            f"User ID: {user_id}\n"
            f"Recent logs: Compressor valve pressure dropped below threshold.\n"
            f"Protocol: Inform user to wear safety goggles before inspecting the valve.\n"
        )

# Initialize Moss Client
moss_engine = MossContextEngine(api_key=os.getenv("MOSS_API_KEY", "hackathon-mock-key"))
# ---------------------

def prewarm(proc: JobProcess):
    """Preloads the Silero VAD (Voice Activity Detection) model to eliminate cold-start latency."""
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the Voice Agent."""
    
    # 1. Base CRISPE prompt incorporating constraints for low latency
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are an expert field operations and medical dispatch AI assistant operating in a real-time, voice-only environment. "
            "Answer the user's spoken inquiry immediately using the MOSS CONTEXT provided in the system messages. "
            "Be exceedingly concise, professional, and clear. Speak in short, digestible sentences suitable for text-to-speech. "
            "If the requested information is not in the context, clearly state that you do not have the information."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # 2. Define the Moss interception hook
    # This runs right after the STT finishes transcribing, but before the LLM generates a response.
    async def before_llm_cb(agent: VoicePipelineAgent, chat_ctx: llm.ChatContext):
        # Extract the user's latest transcribed speech
        last_user_msg = chat_ctx.messages[-1] if chat_ctx.messages else None
        
        if last_user_msg and last_user_msg.role == "user" and isinstance(last_user_msg.content, str):
            # Fetch real-time context from Moss in <10ms
            context = await moss_engine.retrieve_context(
                user_id=participant.identity, 
                query=last_user_msg.content
            )
            
            # Inject the context dynamically as a system message right before the LLM sees it
            chat_ctx.messages.append(llm.ChatMessage(
                role="system",
                content=f"MOSS CONTEXT (Inject Time: {time.time()}):\n{context}"
            ))

    # 3. Assemble the ultra-low latency pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],       
        stt=deepgram.STT(),                 
        llm=openai.LLM(model="gpt-4o"),     
        tts=elevenlabs.TTS(),               
        chat_ctx=initial_ctx,
        before_llm_cb=before_llm_cb,        # <--- Attach the Moss context injector here
    )

    agent.start(ctx.room, participant)

    # 4. Greet the user to establish the connection immediately
    await agent.say("Agent online. How can I assist you with your current task?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
