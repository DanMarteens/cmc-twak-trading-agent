"""
Verify the CMC MCP key and discover the 12 real tool names + schemas.

    python scripts/verify_cmc.py            # list tools
    python scripts/verify_cmc.py BTC        # also fetch a sample quote

Handles the MCP streamable-HTTP handshake (initialize -> initialized -> tools/list)
and parses both plain-JSON and SSE responses. Output drives the _TOOL_NAMES
mapping in agent/cmc_client.py.
"""

import json
import os
import sys

import httpx

URL = "https://mcp.coinmarketcap.com/mcp"


def _load_key() -> str:
    # read .env without extra deps
    key = os.environ.get("CMC_MCP_API_KEY", "")
    if not key and os.path.exists(".env"):
        for line in open(".env"):
            if line.strip().startswith("CMC_MCP_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("CMC_MCP_API_KEY not found (env or .env)")
    return key


def _parse(resp: httpx.Response) -> dict:
    ctype = resp.headers.get("content-type", "")
    if "text/event-stream" in ctype:
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return {}
    return resp.json()


def main():
    key = _load_key()
    headers = {
        "X-CMC-MCP-API-KEY": key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    with httpx.Client(timeout=30, headers=headers) as c:
        init = c.post(URL, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "bnb-hack-agent", "version": "0.1"},
            },
        })
        init.raise_for_status()
        sid = init.headers.get("mcp-session-id")
        if sid:
            headers["Mcp-Session-Id"] = sid
            c.headers.update(headers)
        res = _parse(init)
        srv = res.get("result", {}).get("serverInfo", {})
        print(f"✓ connected: {srv.get('name','?')} {srv.get('version','')}  session={sid}")

        # notify initialized
        c.post(URL, json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        tools = c.post(URL, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tlist = _parse(tools).get("result", {}).get("tools", [])
        print(f"\n=== {len(tlist)} tools ===")
        for t in tlist:
            print(f"  {t['name']}  —  {t.get('description','')[:70]}")

        if len(sys.argv) > 1:
            sym = sys.argv[1]
            print(f"\n=== sample call for {sym} (first quote-ish tool) ===")
            for t in tlist:
                if "quote" in t["name"].lower() or "price" in t["name"].lower():
                    call = c.post(URL, json={
                        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": t["name"], "arguments": {"symbol": sym}},
                    })
                    print(f"  tool={t['name']}")
                    print("  result:", json.dumps(_parse(call).get("result", {}), indent=2)[:800])
                    break


if __name__ == "__main__":
    main()
