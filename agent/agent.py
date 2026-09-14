import asyncio
import logging

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero

load_dotenv()
logger = logging.getLogger("voice-agent")

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
            "Answer the user's spoken inquiry immediately. Be exceedingly concise, professional, and clear. "
            "Speak in short, digestible sentences suitable for text-to-speech. Do not use markdown."
            # TODO: We will dynamically inject Moss context here in the next step!
        ),
    )

    # 2. Connect to the LiveKit Room (Audio Only for lowest bandwidth/latency)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for the user to join the room via the Next.js frontend
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # 3. Assemble the ultra-low latency pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],       # Voice Activity Detection (Barge-in support)
        stt=deepgram.STT(),                 # Low-latency Speech-to-Text
        llm=openai.LLM(model="gpt-4o"),     # Reasoning Engine (or Claude 3.5 Sonnet)
        tts=elevenlabs.TTS(),               # High-quality Text-to-Speech
        chat_ctx=initial_ctx,
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
