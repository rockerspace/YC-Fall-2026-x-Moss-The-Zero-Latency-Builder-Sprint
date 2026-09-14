import { GET } from "../src/app/api/token/route";
import { NextResponse } from "next/server";

// Mock the livekit-server-sdk
jest.mock("livekit-server-sdk", () => {
  return {
    AccessToken: jest.fn().mockImplementation(() => {
      return {
        addGrant: jest.fn(),
        toJwt: jest.fn().mockResolvedValue("mocked_jwt_token"),
      };
    }),
  };
});

describe("GET /api/token", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it("returns 500 if credentials are missing", async () => {
    process.env.LIVEKIT_API_KEY = "";
    
    const req = new Request("http://localhost/api/token");
    const res = await GET(req) as NextResponse;
    
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.error).toBe("Server misconfigured. Missing LiveKit credentials.");
  });

  it("returns token and url when valid", async () => {
    process.env.LIVEKIT_API_KEY = "test_key";
    process.env.LIVEKIT_API_SECRET = "test_secret";
    process.env.NEXT_PUBLIC_LIVEKIT_URL = "wss://test.livekit.cloud";

    const req = new Request("http://localhost/api/token?participantName=Tester");
    const res = await GET(req) as NextResponse;
    
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.token).toBe("mocked_jwt_token");
    expect(data.url).toBe("wss://test.livekit.cloud");
  });
});
