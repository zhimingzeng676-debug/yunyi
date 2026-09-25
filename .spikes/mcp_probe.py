"""Disposable SDK stdio fixture, never a production MCP server."""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

server = FastMCP('netpilot-dependency-spike')

class EchoResult(BaseModel):
    session_id: str
    value: int

@server.tool()
def echo_session(session_id: str, value: int) -> EchoResult:
    if not session_id:
        raise ValueError('session_id required')
    return EchoResult(session_id=session_id, value=value)

if __name__ == '__main__':
    server.run(transport='stdio')
