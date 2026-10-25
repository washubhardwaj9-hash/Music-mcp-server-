from fastmcp import FastMCP
from JioSaavnP import JioSaavn

mcp = FastMCP("JioSaavn Music Server")
jio = JioSaavn()

@mcp.tool
def search_songs(query: str, limit: int = 5):
    """Search for songs on JioSaavn"""
    return jio.search_songs(query, limit=limit)

if __name__ == "__main__":
    mcp.run()
