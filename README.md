# Solana Web3 MCP Server

A **Model Context Protocol (MCP)** server that exposes Solana blockchain tools to any MCP-compatible AI client (Claude Desktop, Cursor, etc.).

---
## Features

| Category | Tools |
|---|---|
| **Accounts & Balances** | `get_balance`, `get_account_info`, `get_multiple_accounts`, `get_token_accounts`, `get_token_balance` |
| **Transactions** | `get_transaction`, `get_signatures_for_address`, `simulate_transaction`, `get_latest_blockhash` |
| **Tokens & Mints** | `get_token_supply`, `get_token_largest_accounts`, `get_mint_info`, `decode_token_metadata` |
| **Programs** | `get_program_accounts`, `decode_instruction`, `fetch_anchor_idl` |
| **DEX / DeFi** | `get_jupiter_quote`, `get_token_price`, `get_orca_whirlpools` |
| **Network Info** | `get_slot`, `get_block_time`, `get_epoch_info`, `get_health`, `get_supply`, `get_version`, `get_inflation_rate`, `get_cluster_nodes`, `get_minimum_balance_for_rent_exemption` |
| **Priority Fees** | `get_recent_priority_fees` |
| **Voting** | `get_vote_accounts` |
| **Address Lookup Tables** | `get_address_lookup_table` |
| **Utilities** | `validate_address`, `decode_base58`, `parse_token_account` |
| **Composite** | `resolve_token_info`, `get_wallet_overview` |

---

## Requirements

- Python 3.11+
- `pip` or [`uv`](https://github.com/astral-sh/uv)

---

## Installation

### Option 1: With uv

```bash
git clone https://github.com/kvzsolt/Solana-Web3-MCP-Server.git
cd Solana-Web3-MCP-Server
uv venv
source .venv/bin/activate
uv sync
```

### Option 2: With pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Usage

### Run the server (stdio transport — default for MCP)

```bash
web3-mcp
# or
python solana_mcp_server.py
```

### Connect via Claude Desktop

Add to your `claude_desktop_config.json`:


You installed with `uv` and the `web3-mcp` script is in your PATH:

```json
{
  "mcpServers": {
    "solana-web3": {
      "command": "/absolute/path/to/Solana-Web3-MCP-Server/.venv/bin/web3-mcp"
    }
  }
}
```

---

## Configuration

The server uses Solana mainnet-beta by default:

```text
https://api.mainnet-beta.solana.com
```

Set `RPC_ENDPOINT` in your environment or `.env` file to use a different RPC provider:

```bash
RPC_ENDPOINT=https://your-rpc.example
```

Jupiter quote and price tools use Jupiter's public Lite API endpoints.

## Project Structure

```
Solana-Web3-MCP-Server/
├── solana_mcp_server.py  # Main MCP server and CLI entry point
├── pyproject.toml        # Project metadata & dependencies
├── requirements.txt      # pip-compatible dependency list
├── uv.lock               # uv lockfile
├── tests/
│   ├── test_all_tools.py # Live integration smoke test for MCP tools
│   └── test_mcp_client.py # Basic MCP client smoke test
├── .gitignore            # Git ignore rules
└── README.md
```

---

## License

MIT

## Roadmap

- Add transaction building and sending tools (`send_transaction`, `build_transfer`, `build_token_transfer`).
- Add NFT and compressed NFT tooling.
- Add WebSocket subscription tools for real-time updates.
- Add RPC retry, rate-limit handling, and endpoint failover.
- Add CI with linting and focused unit tests around parsers and response shaping.

Contributions are welcome.
