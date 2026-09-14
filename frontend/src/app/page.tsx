"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  BarVisualizer,
  useVoiceAssistant,
  useRoomContext,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useState, useEffect } from "react";
import { RoomEvent } from "livekit-client";

export default function Home() {
  const [token, setToken] = useState("");
  const [url, setUrl] = useState("");
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [persona, setPersona] = useState("healthcare");

  const startSession = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/token?participantName=${persona}`);
      const data = await res.json();
      if (data.error) {
        alert(data.error);
        return;
      }
      setUrl(data.url);
      setToken(data.token);
      setConnected(true);
    } catch (e) {
      console.error(e);
      alert("Failed to fetch token.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 lg:p-24 bg-gray-950 text-white font-sans">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex mb-16">
        <h1 className="text-4xl font-bold tracking-tight">Voice Agent Dashboard</h1>
        <div className="text-gray-400 mt-2 lg:mt-0">Track 1: Sub-10ms Latency</div>
      </div>

      <div className="flex w-full max-w-4xl flex-col items-center">
        {!connected ? (
          <div className="flex w-full max-w-md flex-col space-y-4 rounded-xl bg-gray-900 p-8 shadow-2xl border border-gray-800">
            <h2 className="mb-4 text-2xl font-semibold text-gray-100">Start Operations</h2>
            <p className="text-sm text-gray-400 mb-4">
              Connect securely via LiveKit Cloud to start interacting with the Moss-powered agent.
            </p>
            
            <div className="mb-4 w-full">
              <label className="block text-sm font-medium text-gray-400 mb-2">Select Industry Persona</label>
              <select 
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                className="w-full bg-gray-950 border border-gray-700 rounded-md px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="healthcare">Healthcare (Medical Triage)</option>
                <option value="field_worker">Field Operations (HVAC Repair)</option>
                <option value="dispatch">Emergency Dispatch (911)</option>
                <option value="customer_support">Customer Support (Billing)</option>
              </select>
            </div>
            
            <button
              onClick={startSession}
              className="mt-6 w-full rounded-md bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500"
              disabled={loading}
            >
              {loading ? "Authenticating..." : "Start Secure Session"}
            </button>
          </div>
        ) : (
          <LiveKitRoom
            serverUrl={url}
            token={token}
            connect={connected}
            audio={true}
            video={false}
            onDisconnected={() => setConnected(false)}
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
              <AgentInterface onDisconnect={() => setConnected(false)} />
              <ExplainabilityLogs />
            </div>
            <RoomAudioRenderer />
          </LiveKitRoom>
        )}
      </div>
    </main>
  );
}

function AgentInterface({ onDisconnect }: { onDisconnect: () => void }) {
  const { state, audioTrack } = useVoiceAssistant();
  
  return (
    <div className="flex w-full flex-col items-center justify-center rounded-xl bg-gray-900 p-8 shadow-2xl border border-gray-800">
      <h3 className="text-xl font-semibold text-gray-200 mb-6 w-full text-left">Real-Time Interaction</h3>
      <div className="mb-8 flex w-full items-center space-x-3">
        <div className={`h-3 w-3 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)] ${
          state === 'speaking' ? 'bg-blue-500 shadow-blue-500/50 animate-pulse' :
          state === 'listening' ? 'bg-green-500 shadow-green-500/50' :
          state === 'thinking' ? 'bg-purple-500 shadow-purple-500/50 animate-pulse' :
          'bg-yellow-500 animate-pulse shadow-yellow-500/50'
        }`}></div>
        <span className="font-mono text-sm text-gray-300 uppercase tracking-widest">
          Agent: <span className="text-white font-bold">{state || 'connecting'}</span>
        </span>
      </div>
      
      <div className="mb-8 flex h-32 w-full items-center justify-center rounded-lg bg-gray-950 border border-gray-800 overflow-hidden">
        {audioTrack ? (
          <BarVisualizer state={state} barCount={7} trackRef={audioTrack} className="h-16 text-blue-500" />
        ) : (
          <span className="text-sm text-gray-600 font-mono animate-pulse">Awaiting audio stream...</span>
        )}
      </div>

      <button 
        onClick={onDisconnect}
        className="w-full mt-auto rounded-md bg-red-900/50 border border-red-800 px-6 py-3 font-semibold text-red-200 transition-all hover:bg-red-800/80 hover:text-white"
      >
        End Voice Session
      </button>
    </div>
  );
}

function ExplainabilityLogs() {
  const room = useRoomContext();
  const [logs, setLogs] = useState<{ time: string, message: string }[]>([]);

  useEffect(() => {
    if (!room) return;

    const handleData = (payload: Uint8Array, participant?: any) => {
      const decoder = new TextDecoder();
      const message = decoder.decode(payload);
      
      try {
        const parsed = JSON.parse(message);
        if (parsed.type === "explainability_log") {
          setLogs(prev => [...prev, {
            time: new Date().toLocaleTimeString(),
            message: parsed.data
          }].slice(-5)); // keep last 5
        }
      } catch (e) {
        console.error("Failed to parse data packet", e);
      }
    };

    room.on(RoomEvent.DataReceived, handleData);
    
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room]);

  return (
    <div className="flex w-full flex-col rounded-xl bg-gray-900 p-8 shadow-2xl border border-gray-800 h-[400px]">
      <h3 className="text-xl font-semibold text-gray-200 mb-6">AI Explainability & Traceability</h3>
      
      <div className="flex-1 overflow-y-auto space-y-4 font-mono text-sm pr-2">
        {logs.length === 0 ? (
          <p className="text-gray-500 italic">No context injected yet. Speak to the agent to see real-time Moss traces.</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="bg-gray-950 p-3 rounded border border-gray-800">
              <div className="text-blue-400 text-xs mb-1">[{log.time}] Moss Context Trace (SEC-303):</div>
              <div className="text-gray-300">{log.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
