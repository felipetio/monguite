#!/usr/bin/env python3
"""
Generate OAuth configuration for Monguite MCP Server
"""

import secrets


def generate_oauth_config():
    """Generate secure OAuth credentials."""
    print("\n" + "=" * 60)
    print("OAuth Configuration Generator")
    print("=" * 60)

    print("\nGenerating secure credentials...\n")

    # Generate secrets
    client_secret = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)

    # Default client ID
    default_client_id = "monguite-mcp-client"

    print("Add these to your .env file:")
    print("-" * 60)
    print("\n# OAuth 2.0 Configuration")
    print("OAUTH_ENABLED=true")
    print(f"OAUTH_CLIENT_ID={default_client_id}")
    print(f"OAUTH_CLIENT_SECRET={client_secret}")
    print(f"OAUTH_JWT_SECRET={jwt_secret}")
    print("OAUTH_TOKEN_EXPIRY=3600  # 1 hour")
    print("\n" + "-" * 60)

    print("\n✓ Generated secure credentials!")
    print("\nNOTE: Keep these credentials secret!")
    print("- OAUTH_CLIENT_SECRET: Share only with your MCP client")
    print("- OAUTH_JWT_SECRET: Keep on server only, never share")
    print("\nYou can customize OAUTH_CLIENT_ID to any value you prefer.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    generate_oauth_config()
