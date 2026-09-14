import { AccessToken } from "livekit-server-sdk";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const participantName = searchParams.get("participantName") || "Field_Worker_01";

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const wsUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

  if (!apiKey || !apiSecret || !wsUrl) {
    return NextResponse.json(
      { error: "Server misconfigured. Missing LiveKit credentials." },
      { status: 500 }
    );
  }

  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantName,
    name: participantName,
  });

  at.addGrant({
    roomJoin: true,
    room: "moss-hackathon-room",
    canPublish: true,
    canSubscribe: true,
  });

  return NextResponse.json({ 
    token: await at.toJwt(), 
    url: wsUrl 
  });
}
