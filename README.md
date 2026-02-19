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

```bash
git clone https://github.com/kvzsolt/Web3js-MCP-Server.git
cd Web3js-MCP-Server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Or with `uv`:

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## Usage

### Run the server (stdio transport — default for MCP)

```bash
python server.py
```

### Connect via Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solana-web3": {
      "command": "python",
      "args": ["/absolute/path/to/Web3js-MCP-Server/server.py"]
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
python server.py
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
├── server.py           # Main MCP server — all tools defined here
├── pyproject.toml      # Project metadata & dependencies
├── requirements.txt    # Pinned dependencies for pip
└── README.md
```

---

## License

MIT

