#!/usr/bin/env python3
"""Test ALL tools in the Solana Web3 MCP Server one by one."""

import asyncio
import base64
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Test addresses
WRAPPED_SOL = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SYSTEM_PROGRAM = "11111111111111111111111111111111"
# Real mainnet SPL token account owned by WRAPPED_SOL, discovered from get_token_accounts.
TOKEN_ACCOUNT = "7mLtyoHv5LBNS14oFGd1xUWJQeMSDhpLzaQYZnBpCRPt"
ADDRESS_LOOKUP_TABLE_PROGRAM = "AddressLookupTab1e1111111111111111111111111"
# A real transaction signature (recent one from mainnet)
REAL_TX_SIG = "EsGfwzWCnqfVT3A7GD3pzPAxf34Rp9pwv3xUNQLR6aNZstKvnuRGGovzqzyCizFD4fWasbeGJrwVUruAe5hveWt"
MEMO_PROGRAM = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
ANCHOR_IDL_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
_ADDRESS_LOOKUP_TABLE: str | None = None


def make_simulation_transaction_base64() -> str:
    """Build a valid signed transaction shape for simulateTransaction."""
    rpc = Client(RPC_ENDPOINT)
    payer = Keypair()
    instruction = transfer(
        TransferParams(
            from_pubkey=payer.pubkey(),
            to_pubkey=payer.pubkey(),
            lamports=0,
        )
    )
    blockhash = rpc.get_latest_blockhash().value.blockhash
    message = MessageV0.try_compile(payer.pubkey(), [instruction], [], blockhash)
    tx = VersionedTransaction(message, [payer])
    return base64.b64encode(bytes(tx)).decode("ascii")


def find_address_lookup_table() -> str:
    """Find a live ALT account from recent Address Lookup Table program activity."""
    global _ADDRESS_LOOKUP_TABLE
    if _ADDRESS_LOOKUP_TABLE is not None:
        return _ADDRESS_LOOKUP_TABLE

    rpc = Client(RPC_ENDPOINT)
    program = Pubkey.from_string(ADDRESS_LOOKUP_TABLE_PROGRAM)
    signatures = rpc.get_signatures_for_address(program, limit=10).value
    for signature_info in signatures:
        tx = rpc.get_transaction(
            signature_info.signature,
            max_supported_transaction_version=0,
        ).value
        if tx is None:
            continue

        for account_key in tx.transaction.transaction.message.account_keys:
            account = rpc.get_account_info(account_key).value
            if account and str(account.owner) == ADDRESS_LOOKUP_TABLE_PROGRAM:
                _ADDRESS_LOOKUP_TABLE = str(account_key)
                return _ADDRESS_LOOKUP_TABLE

    raise RuntimeError("Could not find a live Address Lookup Table account")


def is_expected_skip(name: str, text: str) -> bool:
    """Known environment/client limitations, not bad tool input data."""
    expected = {
        "get_token_largest_accounts": "HTTPStatusError",
    }
    marker = expected.get(name)
    return marker is not None and marker in text


def is_success_response(text: str) -> bool:
    try:
        return json.loads(text).get("success") is True
    except json.JSONDecodeError:
        return False

async def test_all_tools():
    server_params = StdioServerParameters(
        command=str(PROJECT_ROOT / ".venv" / "bin" / "web3-mcp"),
        args=[],
        env=None,
    )

    results = []

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCP Server connected!\n")

            tools = await session.list_tools()
            print(f"🛠️  Testing {len(tools.tools)} tools one by one...\n")

            for tool in tools.tools:
                name = tool.name
                try:
                    # Determine parameters based on tool name
                    params = {}

                    # Accounts & Balances
                    if name == "get_balance":
                        params = {"address": WRAPPED_SOL}
                    elif name == "get_account_info":
                        params = {"address": WRAPPED_SOL}
                    elif name == "get_token_accounts":
                        params = {"owner": WRAPPED_SOL}
                    elif name == "get_token_balance":
                        params = {"token_account": TOKEN_ACCOUNT}
                    elif name == "get_multiple_accounts":
                        params = {"addresses": [WRAPPED_SOL, USDC_MINT]}

                    # Transactions
                    elif name == "get_transaction":
                        params = {"signature": REAL_TX_SIG}
                    elif name == "get_signatures_for_address":
                        params = {"address": WRAPPED_SOL, "limit": 5}
                    elif name == "simulate_transaction":
                        params = {"transaction_base64": make_simulation_transaction_base64()}
                    elif name == "get_latest_blockhash":
                        params = {}

                    # Tokens & Mints
                    elif name in ["get_token_supply", "get_mint_info", "decode_token_metadata"]:
                        params = {"mint": USDC_MINT}
                    elif name == "get_token_largest_accounts":
                        params = {"mint": USDC_MINT}

                    # Programs
                    elif name == "get_program_accounts":
                        params = {"program_id": MEMO_PROGRAM}
                    elif name == "decode_instruction":
                        params = {"instruction_data_base58": "11111111111111111111111111111111", "program_id": SYSTEM_PROGRAM}
                    elif name == "fetch_anchor_idl":
                        params = {"program_id": ANCHOR_IDL_PROGRAM}

                    # DEX / DeFi
                    elif name == "get_jupiter_quote":
                        params = {"input_mint": WRAPPED_SOL, "output_mint": USDC_MINT, "amount": 1000000000}
                    elif name == "get_token_price":
                        params = {"mints": USDC_MINT}
                    elif name == "get_orca_whirlpools":
                        params = {}

                    # Network Info
                    elif name == "get_slot":
                        params = {}
                    elif name == "get_block_time":
                        params = {"slot": 427900000}
                    elif name == "get_epoch_info":
                        params = {}
                    elif name == "get_health":
                        params = {}
                    elif name == "get_supply":
                        params = {}
                    elif name == "get_version":
                        params = {}
                    elif name == "get_inflation_rate":
                        params = {}
                    elif name == "get_minimum_balance_for_rent_exemption":
                        params = {"data_length": 165}
                    elif name == "get_cluster_nodes":
                        params = {}
                    elif name == "get_recent_priority_fees":
                        params = {}

                    # Voting
                    elif name == "get_vote_accounts":
                        params = {}

                    # Address Lookup Tables
                    elif name == "get_address_lookup_table":
                        params = {"address": find_address_lookup_table()}

                    # Utilities
                    elif name == "validate_address":
                        params = {"address": WRAPPED_SOL}
                    elif name == "decode_base58":
                        params = {"data": "11111111111111111111111111111111"}
                    elif name == "parse_token_account":
                        params = {"account_address": TOKEN_ACCOUNT}

                    # Composite
                    elif name == "resolve_token_info":
                        params = {"mint": USDC_MINT}
                    elif name == "get_wallet_overview":
                        params = {"address": WRAPPED_SOL}

                    result = await session.call_tool(name, params)

                    # Check if result indicates error
                    text = result.content[0].text if result.content else ""
                    if is_success_response(text):
                        results.append((name, "✅ OK", text[:80]))
                    elif is_expected_skip(name, text):
                        results.append((name, "⏭️ SKIPPED", text[:150]))
                    else:
                        results.append((name, "❌ FAILED", text[:150]))

                except Exception as e:
                    results.append((name, "❌ ERROR", str(e)[:100]))

    # Print summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)

    ok_count = sum(1 for _, status, _ in results if status == "✅ OK")
    skip_count = sum(1 for _, status, _ in results if status == "⏭️ SKIPPED")
    fail_count = sum(1 for _, status, _ in results if status in ["❌ FAILED", "❌ ERROR"])

    for name, status, detail in results:
        print(f"{status} {name:<35} {detail}")

    print("\n" + "="*70)
    print(f"✅ Passed: {ok_count} | ⏭️ Skipped: {skip_count} | ❌ Failed: {fail_count} | Total: {len(results)}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_all_tools())
