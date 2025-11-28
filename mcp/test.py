#!/usr/bin/env python3
"""
Test script for Monguite MCP Server
Run this to verify the server is working correctly before connecting to Claude Desktop.
"""

import asyncio
import json
import os
import sys

# Add the current directory to path if needed
sys.path.insert(0, os.path.dirname(__file__))

import server


async def test_mcp_server():
    """Test the MCP server functionality."""

    print("=" * 60)
    print("Monguite MCP Server Test")
    print("=" * 60)

    # Test 1: Get API stats
    print("\n[Test 1] Testing get_api_stats tool...")
    try:
        result = await server.get_api_stats()
        stats = json.loads(result)
        print("✓ API Stats retrieved successfully:")
        print(f"  • Total lands: {stats.get('total_lands', 'N/A')}")
        print(f"  • Total communities: {stats.get('total_communities', 'N/A')}")
        print(f"  • API URL: {stats.get('api_base_url', 'N/A')}")
        print(f"  • Status: {stats.get('api_status', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Error getting stats: {e}")
        print("  Make sure Monguite API is running at the configured URL")
        print(f"  Current URL: {os.getenv('MONGUITE_API_URL', 'http://localhost:8000')}\n")
        return False

    # Test 2: Search lands (simple query)
    print("[Test 2] Testing search_lands tool...")
    try:
        result = await server.search_lands(page=1)
        data = json.loads(result)
        print("✓ Search successful:")
        print(f"  • Total count: {data.get('total_count', 0)}")
        print(f"  • Page results: {data.get('page_results', 0)}")

        if data.get("lands"):
            first_land = data["lands"][0]
            print(f"  • First land: {first_land.get('name', 'N/A')}")
            print(f"    Category: {first_land.get('category', 'N/A')}")
            print(f"    Biome: {first_land.get('biome', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Error searching lands: {e}\n")
        return False

    # Test 3: Search communities
    print("[Test 3] Testing search_communities tool...")
    try:
        result = await server.search_communities(page=1)
        data = json.loads(result)
        print("✓ Search successful:")
        print(f"  • Total count: {data.get('total_count', 0)}")
        print(f"  • Page results: {data.get('page_results', 0)}")

        if data.get("communities"):
            first_community = data["communities"][0]
            print(f"  • First community: {first_community.get('name', 'N/A')}")
            print(f"    Lands count: {first_community.get('lands_count', 0)}")
        print()
    except Exception as e:
        print(f"✗ Error searching communities: {e}\n")
        return False

    # Test 4: Filtered search
    print("[Test 4] Testing filtered search (category=TI)...")
    try:
        result = await server.search_lands(category="TI", page=1)
        data = json.loads(result)
        print("✓ Filtered search successful:")
        print(f"  • Terra Indígena (TI) count: {data.get('total_count', 0)}")
        print(f"  • Results on this page: {data.get('page_results', 0)}")
        print()
    except Exception as e:
        print(f"✗ Error in filtered search: {e}\n")
        return False

    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Configure Claude Desktop with the MCP server")
    print("2. Restart Claude Desktop")
    print("3. Try queries like: 'Show me indigenous lands in the Amazon'")
    print("\nSee mcp/README.md for detailed setup instructions.")
    print()

    return True


def main():
    """Main entry point."""
    # Check if API URL is set
    api_url = os.getenv("MONGUITE_API_URL", "http://localhost:8000")
    print(f"\nUsing API URL: {api_url}")

    # Check if API token is set
    api_token = os.getenv("MONGUITE_API_TOKEN", "")
    if api_token:
        print(f"Using API Token: {api_token[:10]}...")
    else:
        print("No API token configured (OK for local development)")

    print("\nStarting tests...\n")

    # Run async tests
    try:
        success = asyncio.run(test_mcp_server())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
