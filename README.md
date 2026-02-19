# Solana Web3 MCP Server

A **Model Context Protocol (MCP)** server that exposes a comprehensive set of Solana blockchain tools to any MCP-compatible AI client (Claude Desktop, Cursor, etc.).

Built with [FastMCP](https://github.com/jlowin/fastmcp) and the [solana-py](https://github.com/michaelhly/solana-py) RPC client.

---

## Features

| Category | Tools |
|---|---|
| **Accounts & Balances** | `get_balance`, `get_account_info`, `get_multiple_accounts`, `get_token_accounts`, `get_token_balance` |
| **Transactions** | `get_transaction`, `get_signatures_for_address`, `simulate_transaction`, `get_latest_blockhash`, `is_blockhash_valid` |
| **Tokens & Mints** | `get_token_supply`, `get_token_largest_accounts`, `get_mint_info`, `decode_token_metadata` |
| **Programs** | `get_program_accounts`, `decode_instruction`, `fetch_anchor_idl` |
| **DEX / DeFi** | `get_jupiter_quote`, `get_token_price`, `get_raydium_pools`, `get_orca_whirlpools` |
| **Network Info** | `get_slot`, `get_block_time`, `get_epoch_info`, `get_health`, `get_supply`, `get_version`, `get_inflation_rate`, `get_cluster_nodes`, `get_minimum_balance_for_rent_exemption` |
| **Priority Fees** | `get_recent_priority_fees` |
| **Staking & Voting** | `get_stake_activation`, `get_vote_accounts` |
| **Address Lookup Tables** | `get_address_lookup_table` |
| **Utilities** | `validate_address`, `decode_base58`, `parse_token_account` |
| **Composite** | `resolve_token_info`, `get_wallet_overview` |

---

## Requirements

- Python 3.11+
- `pip` or [`uv`](https://github.com/astral-sh/uv)

---

## Installation

### Option 1: With pip

```bash
git clone https://github.com/kvzsolt/Web3js-MCP-Server.git
cd Web3js-MCP-Server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: With uv (recommended — faster!)

```bash
git clone https://github.com/kvzsolt/Web3js-MCP-Server.git
cd Web3js-MCP-Server

# Create venv and install from pyproject.toml
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e .
```

---

## Usage

### Run the server (stdio transport — default for MCP)

**If installed with pip:**
```bash
python mcp-server.py
```

**If installed with uv:**
```bash
web3-mcp
# or
python mcp-server.py
```

### Connect via Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solana-web3": {
      "command": "python",
      "args": ["/absolute/path/to/Web3js-MCP-Server/mcp-server.py"]
    }
  }
}
```

Or if you installed with `uv` and the `web3-mcp` script is in your PATH:

```json
{
  "mcpServers": {
    "solana-web3": {
      "command": "/absolute/path/to/Web3js-MCP-Server/.venv/bin/web3-mcp"
    }
  }
}
```

---

## Configuration

By default the server connects to the **Solana Mainnet** public RPC endpoint:

```
https://api.mainnet-beta.solana.com
```

To use a custom RPC endpoint (e.g. Helius, QuickNode, Triton), set the environment variable before starting the server:

```bash
export RPC_ENDPOINT="https://your-rpc-endpoint.com"
python mcp-server.py
```

Or create a `.env` file in the project root:

```env
RPC_ENDPOINT=https://your-rpc-endpoint.com
```

> **Note:** `.env` files are ignored by git. Never commit your private RPC URLs or API keys.

---

## Project Structure

```
Web3js-MCP-Server/
├── mcp-server.py         # Main MCP server — all tools defined here
├── web3_mcp_server.py    # Entry point wrapper for CLI script
├── pyproject.toml        # Project metadata & dependencies
├── requirements.txt      # Pinned dependencies for pip
├── .gitignore            # Git ignore rules
├── .env.example          # Template for environment variables
└── README.md
```

---

## License

MIT

