"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  BarVisualizer,
  useVoiceAssistant,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useState } from "react";

export default function Home() {
  const [token, setToken] = useState("");
  const [url, setUrl] = useState("");
  const [connected, setConnected] = useState(false);

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-950 text-white font-sans">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex mb-16">
        <h1 className="text-4xl font-bold tracking-tight">Voice Agent Dashboard</h1>
        <div className="text-gray-400 mt-2 lg:mt-0">Track 1: Sub-10ms Latency</div>
      </div>

      <div className="flex w-full max-w-md flex-col items-center">
        {!connected ? (
          <div className="flex w-full flex-col space-y-4 rounded-xl bg-gray-900 p-8 shadow-2xl border border-gray-800">
            <h2 className="mb-4 text-2xl font-semibold text-gray-100">Connect to LiveKit</h2>
            
            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Server URL</label>
              <input
                type="text"
                placeholder="wss://your-project.livekit.cloud"
                className="w-full rounded-md border border-gray-700 bg-gray-800 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Access Token</label>
              <input
                type="password"
                placeholder="eyJh..."
                className="w-full rounded-md border border-gray-700 bg-gray-800 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
            </div>
            
            <button
              onClick={() => setConnected(true)}
              className="mt-6 w-full rounded-md bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 disabled:shadow-none"
              disabled={!token || !url}
            >
              Start Session
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
            <AgentInterface onDisconnect={() => setConnected(false)} />
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
      <div className="mb-8 flex items-center space-x-3">
        <div className={`h-3 w-3 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)] ${
          state === 'connected' ? 'bg-green-500 shadow-green-500/50' : 
          state === 'speaking' ? 'bg-blue-500 shadow-blue-500/50 animate-pulse' :
          state === 'listening' ? 'bg-purple-500 shadow-purple-500/50' :
          'bg-yellow-500 animate-pulse shadow-yellow-500/50'
        }`}></div>
        <span className="font-mono text-sm text-gray-300 uppercase tracking-widest">
          Status: <span className="text-white font-bold">{state || 'connecting'}</span>
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
        className="w-full rounded-md bg-red-900/50 border border-red-800 px-6 py-3 font-semibold text-red-200 transition-all hover:bg-red-800/80 hover:text-white"
      >
        End Voice Session
      </button>
    </div>
  );
}
