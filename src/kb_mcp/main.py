"""Main MCP server entry point."""
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from kb_mcp.db import get_db
from kb_mcp.mcp import tools as mcp_tools


def main():
    """Main entry point for MCP server."""
    print("🚀 Starting KB MCP Server...")
    
    # Initialize database
    db = get_db()
    db.connect()
    print("✅ Database initialized")
    
    # List available tools
    print(f"\n📋 Available MCP tools ({len(mcp_tools.MCP_TOOLS)}):")
    for name in sorted(mcp_tools.MCP_TOOLS.keys()):
        print(f"   • {name}")
    
    print("\n✅ MCP Server ready!")
    print("\nUsage with Claude Desktop or other MCP clients:")
    print("   Add to your MCP settings JSON:")
    print('   {')
    print('     "mcpServers": {')
    print('       "kb-mcp": {')
    print('         "command": "python",')
    print('         "args": ["-m", "kb_mcp.main"]')
    print('       }')
    print('     }')
    print('   }')


if __name__ == "__main__":
    main()
