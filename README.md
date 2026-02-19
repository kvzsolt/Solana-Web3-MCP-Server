# Solana Web3 MCP Server

A **Model Context Protocol (MCP)** server that exposes a basic set of Solana blockchain tools to any MCP-compatible AI client (Claude Desktop, Cursor, etc.)

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
# Create venv and install from pyproject.toml
uv venv
source .venv/bin/activate
uv pip install -e .
```

---

## Usage

### Run the server (stdio transport — default for MCP)

**If installed with uv:**
```bash
web3-mcp
# or
python mcp-server.py
```

### Connect via Claude Desktop

Add to your `claude_desktop_config.json`:


You installed with `uv` and the `web3-mcp` script is in your PATH:

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

## Project Structure

```
Web3js-MCP-Server/
├── mcp-server.py         # Main MCP server — all tools defined here
├── web3_mcp_server.py    # Entry point wrapper for CLI script
├── pyproject.toml        # Project metadata & dependencies
├── .gitignore            # Git ignore rules
└── README.md
```

---

## License

MIT

## Todos

### Features
- [ ] Add transaction building and sending tools (`send_transaction`, `build_transfer`, `build_token_transfer`)
- [ ] Add support for Metaplex NFT operations (fetch metadata, get collection info)
- [ ] Add Jupiter swap execution (currently only has quote fetching)
- [ ] Add WebSocket subscription tools for real-time updates
- [ ] Add support for compressed NFTs (cNFTs)
- [ ] Add Pyth price feed integration

### Improvements
- [ ] Add caching layer for frequently requested data (token metadata, account info)
- [ ] Add retry logic with exponential backoff for RPC calls
- [ ] Add request rate limiting to avoid RPC endpoint throttling
- [ ] Add logging with configurable verbosity levels
- [ ] Add health check endpoint for server monitoring
- [ ] Add tool execution metrics and performance tracking

### Testing & Quality
- [ ] Add unit tests for all tools
- [ ] Add integration tests with devnet
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Add code coverage reporting
- [ ] Add linting and formatting checks (ruff, black)

### Documentation
- [ ] Add examples for each tool in README
- [ ] Add troubleshooting section
- [ ] Add video tutorial or GIF demo
- [ ] Add API documentation with tool parameters and return types
- [ ] Document common use cases (wallet analysis, token research, etc.)

### DevOps
- [ ] Add Docker support
- [ ] Add support for multiple RPC endpoints with failover
- [ ] Add environment-specific configs (mainnet, devnet, testnet)
- [ ] Add graceful shutdown handling


