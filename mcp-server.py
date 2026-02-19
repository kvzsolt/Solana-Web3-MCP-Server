from fastmcp import FastMCP
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from solders.signature import Signature as SoldersSig
from typing import Optional, List, Dict, Any
import base58
import struct
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONSTANTS
# ============================================================================

LAMPORTS_PER_SOL = 1_000_000_000

# RPC Client — override via RPC_ENDPOINT env var or .env file
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")
client = Client(RPC_ENDPOINT, commitment=Confirmed)

# Initialize MCP server
mcp = FastMCP("Solana Web3 Tools")


def _ok(data: Any, **extra) -> Dict[str, Any]:
    """Wrap a successful result."""
    resp = {"success": True, "data": data}
    resp.update(extra)
    return resp


def _err(msg: str, error_type: str = "Error") -> Dict[str, Any]:
    """Wrap an error result."""
    return {"success": False, "error": msg, "error_type": error_type}


def _pubkey(addr: str) -> Pubkey:
    return Pubkey.from_string(addr)


def _lamports_to_sol(lamports: int) -> float:
    return lamports / LAMPORTS_PER_SOL


# ============================================================================
# ACCOUNT & BALANCE OPERATIONS
# ============================================================================

@mcp.tool()
async def get_balance(address: str) -> Dict[str, Any]:
    """Get SOL balance for an address in lamports and SOL."""
    try:
        resp = client.get_balance(_pubkey(address))
        lamports = resp.value
        return _ok({
            "address": address,
            "lamports": lamports,
            "sol": _lamports_to_sol(lamports),
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_account_info(address: str) -> Dict[str, Any]:
    """Get detailed account information including owner, data size, executable status, and rent epoch."""
    try:
        resp = client.get_account_info(_pubkey(address))
        acct = resp.value
        if acct is None:
            return _err(f"Account {address} not found")
        return _ok({
            "address": address,
            "lamports": acct.lamports,
            "sol": _lamports_to_sol(acct.lamports),
            "owner": str(acct.owner),
            "executable": acct.executable,
            "rent_epoch": acct.rent_epoch,
            "data_length": len(acct.data),
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_token_accounts(owner: str, mint: Optional[str] = None) -> Dict[str, Any]:
    """Get all SPL token accounts owned by an address, optionally filtered by mint."""
    try:
        owner_pk = _pubkey(owner)
        if mint:
            from solana.rpc.types import TokenAccountOpts
            opts = TokenAccountOpts(mint=_pubkey(mint))
            resp = client.get_token_accounts_by_owner(owner_pk, opts)
        else:
            from solana.rpc.types import TokenAccountOpts
            opts = TokenAccountOpts(program_id=_pubkey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
            resp = client.get_token_accounts_by_owner(owner_pk, opts)

        accounts = []
        for item in resp.value:
            parsed = item.account.data.parsed
            info = parsed["info"]
            accounts.append({
                "pubkey": str(item.pubkey),
                "mint": info["mint"],
                "owner": info["owner"],
                "amount": info["tokenAmount"]["uiAmountString"],
                "decimals": info["tokenAmount"]["decimals"],
                "ui_amount": info["tokenAmount"]["uiAmount"],
            })
        return _ok(accounts, count=len(accounts))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_token_balance(token_account: str) -> Dict[str, Any]:
    """Get token balance for a specific SPL token account address."""
    try:
        resp = client.get_token_account_balance(_pubkey(token_account))
        val = resp.value
        return _ok({
            "address": token_account,
            "amount": val.amount,
            "decimals": val.decimals,
            "ui_amount": val.ui_amount,
            "ui_amount_string": val.ui_amount_string,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_multiple_accounts(addresses: List[str]) -> Dict[str, Any]:
    """Batch fetch multiple account infos in a single RPC call. Max 100 addresses."""
    try:
        if len(addresses) > 100:
            return _err("Maximum 100 addresses per request")
        pubkeys = [_pubkey(a) for a in addresses]
        resp = client.get_multiple_accounts(pubkeys)
        results = []
        for i, acct in enumerate(resp.value):
            if acct is None:
                results.append({"address": addresses[i], "exists": False})
            else:
                results.append({
                    "address": addresses[i],
                    "exists": True,
                    "lamports": acct.lamports,
                    "owner": str(acct.owner),
                    "executable": acct.executable,
                    "data_length": len(acct.data),
                })
        return _ok(results, count=len(results))
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# TRANSACTION OPERATIONS
# ============================================================================

@mcp.tool()
async def get_transaction(signature: str) -> Dict[str, Any]:
    """Get full transaction details by signature including instructions, logs, and balances."""
    try:
        sig = SoldersSig.from_string(signature)
        resp = client.get_transaction(sig, max_supported_transaction_version=0)
        if resp.value is None:
            return _err(f"Transaction {signature} not found")
        tx = resp.value
        meta = tx.transaction.meta
        msg = tx.transaction.transaction.message

        result = {
            "signature": signature,
            "slot": tx.slot,
            "block_time": tx.block_time,
        }
        if meta:
            result["fee"] = meta.fee
            result["fee_sol"] = _lamports_to_sol(meta.fee)
            result["err"] = str(meta.err) if meta.err else None
            result["log_messages"] = list(meta.log_messages) if meta.log_messages else []
            result["compute_units_consumed"] = meta.compute_units_consumed
            result["pre_balances"] = list(meta.pre_balances)
            result["post_balances"] = list(meta.post_balances)

        account_keys = [str(k) for k in msg.account_keys]
        result["account_keys"] = account_keys
        result["num_instructions"] = len(msg.instructions)

        return _ok(result)
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_signatures_for_address(
    address: str,
    limit: int = 10,
    before: Optional[str] = None,
    until: Optional[str] = None,
) -> Dict[str, Any]:
    """Get recent transaction signature history for an address."""
    try:
        pk = _pubkey(address)
        before_sig = SoldersSig.from_string(before) if before else None
        until_sig = SoldersSig.from_string(until) if until else None
        resp = client.get_signatures_for_address(
            pk, limit=limit, before=before_sig, until=until_sig
        )
        sigs = []
        for s in resp.value:
            sigs.append({
                "signature": str(s.signature),
                "slot": s.slot,
                "block_time": s.block_time,
                "err": str(s.err) if s.err else None,
                "memo": s.memo,
                "confirmation_status": str(s.confirmation_status) if s.confirmation_status else None,
            })
        return _ok(sigs, count=len(sigs))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def simulate_transaction(transaction_base64: str) -> Dict[str, Any]:
    """Simulate a base64-encoded transaction without sending it. Returns logs and error info."""
    try:
        from solders.transaction import VersionedTransaction
        tx_bytes = base58.b58decode(transaction_base64) if not transaction_base64.startswith("A") else __import__("base64").b64decode(transaction_base64)
        tx = VersionedTransaction.from_bytes(tx_bytes)
        resp = client.simulate_transaction(tx)
        val = resp.value
        return _ok({
            "err": str(val.err) if val.err else None,
            "logs": list(val.logs) if val.logs else [],
            "units_consumed": val.units_consumed,
            "return_data": str(val.return_data) if val.return_data else None,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_latest_blockhash() -> Dict[str, Any]:
    """Get the latest blockhash for transaction creation. Reference: Kit getLatestBlockhash()."""
    try:
        resp = client.get_latest_blockhash(Finalized)
        bh = resp.value
        return _ok({
            "blockhash": str(bh.blockhash),
            "last_valid_block_height": bh.last_valid_block_height,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def is_blockhash_valid(blockhash: str) -> Dict[str, Any]:
    """Check if a blockhash is still valid. Useful before submitting transactions."""
    try:
        from solders.hash import Hash as SoldersHash
        bh = SoldersHash.from_string(blockhash)
        resp = client.is_blockhash_valid(bh)
        return _ok({"blockhash": blockhash, "valid": resp.value})
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# TOKEN & MINT OPERATIONS
# ============================================================================

@mcp.tool()
async def get_token_supply(mint: str) -> Dict[str, Any]:
    """Get total supply for a token mint."""
    try:
        resp = client.get_token_supply(_pubkey(mint))
        val = resp.value
        return _ok({
            "mint": mint,
            "amount": val.amount,
            "decimals": val.decimals,
            "ui_amount": val.ui_amount,
            "ui_amount_string": val.ui_amount_string,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_token_largest_accounts(mint: str) -> Dict[str, Any]:
    """Get the largest token holders for a mint (top 20)."""
    try:
        resp = client.get_token_largest_accounts(_pubkey(mint))
        accounts = []
        for a in resp.value:
            accounts.append({
                "address": str(a.address),
                "amount": a.amount,
                "decimals": a.decimals,
                "ui_amount": a.ui_amount,
                "ui_amount_string": a.ui_amount_string,
            })
        return _ok(accounts, count=len(accounts))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_mint_info(mint: str) -> Dict[str, Any]:
    """Get mint account details: decimals, supply, authorities. Parses raw SPL Token mint layout."""
    try:
        resp = client.get_account_info(_pubkey(mint))
        acct = resp.value
        if acct is None:
            return _err(f"Mint account {mint} not found")

        data = bytes(acct.data)
        owner = str(acct.owner)

        is_token = owner == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        is_token_2022 = owner == "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        if not is_token and not is_token_2022:
            return _err(f"Account {mint} is not a token mint (owner: {owner})")

        # SPL Token Mint layout: 4+32+8+1+1+4+32 = 82 bytes minimum
        mint_authority_option = struct.unpack_from("<I", data, 0)[0]
        mint_authority = str(Pubkey.from_bytes(data[4:36])) if mint_authority_option == 1 else None
        supply = struct.unpack_from("<Q", data, 36)[0]
        decimals = data[44]
        is_initialized = bool(data[45])
        freeze_authority_option = struct.unpack_from("<I", data, 46)[0]
        freeze_authority = str(Pubkey.from_bytes(data[50:82])) if freeze_authority_option == 1 else None

        return _ok({
            "mint": mint,
            "decimals": decimals,
            "supply": supply,
            "supply_ui": supply / (10 ** decimals),
            "mint_authority": mint_authority,
            "freeze_authority": freeze_authority,
            "is_initialized": is_initialized,
            "program": "token-2022" if is_token_2022 else "token",
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def decode_token_metadata(mint: str) -> Dict[str, Any]:
    """Decode Metaplex token metadata (name, symbol, uri) for a token mint."""
    try:
        # Derive metadata PDA
        metaplex_program = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
        seeds = [
            b"metadata",
            bytes(_pubkey(metaplex_program)),
            bytes(_pubkey(mint)),
        ]
        metadata_addr, _ = Pubkey.find_program_address(seeds, _pubkey(metaplex_program))

        resp = client.get_account_info(metadata_addr)
        acct = resp.value
        if acct is None:
            return _err(f"No Metaplex metadata found for mint {mint}")

        data = bytes(acct.data)
        # Metaplex metadata v1 layout:
        # 1 byte key, 32 bytes update_authority, 32 bytes mint
        # then borsh-encoded strings: name, symbol, uri
        offset = 1 + 32 + 32
        name_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        name = data[offset:offset + name_len].decode("utf-8").rstrip("\x00")
        offset += name_len

        symbol_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        symbol = data[offset:offset + symbol_len].decode("utf-8").rstrip("\x00")
        offset += symbol_len

        uri_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        uri = data[offset:offset + uri_len].decode("utf-8").rstrip("\x00")

        update_authority = str(Pubkey.from_bytes(data[1:33]))

        return _ok({
            "mint": mint,
            "metadata_address": str(metadata_addr),
            "name": name,
            "symbol": symbol,
            "uri": uri,
            "update_authority": update_authority,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# PROGRAM OPERATIONS
# ============================================================================

@mcp.tool()
async def get_program_accounts(
    program_id: str,
    data_size: Optional[int] = None,
    memcmp_offset: Optional[int] = None,
    memcmp_bytes: Optional[str] = None,
) -> Dict[str, Any]:
    """Get all accounts owned by a program. Optional filters: data_size and memcmp (offset+bytes)."""
    try:
        filters: List[Any] = []
        if data_size is not None:
            filters.append(data_size)
        if memcmp_offset is not None and memcmp_bytes is not None:
            filters.append(MemcmpOpts(offset=memcmp_offset, bytes=memcmp_bytes))

        resp = client.get_program_accounts(
            _pubkey(program_id),
            encoding="base64",
            filters=filters if filters else None,
        )

        accounts = []
        for item in resp.value:
            accounts.append({
                "pubkey": str(item.pubkey),
                "lamports": item.account.lamports,
                "owner": str(item.account.owner),
                "data_length": len(item.account.data),
                "executable": item.account.executable,
            })
        return _ok(accounts, count=len(accounts))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def decode_instruction(instruction_data_base58: str, program_id: str) -> Dict[str, Any]:
    """Decode instruction data for well-known programs (System, Token, ComputeBudget, Memo)."""
    try:
        data = base58.b58decode(instruction_data_base58)
        result = {"program_id": program_id, "raw_data_hex": data.hex()}

        if program_id == "11111111111111111111111111111111" and len(data) >= 4:
            ix_type = struct.unpack_from("<I", data, 0)[0]
            system_ixs = {0: "CreateAccount", 1: "Assign", 2: "Transfer",
                          3: "CreateAccountWithSeed", 4: "AdvanceNonceAccount",
                          5: "WithdrawNonceAccount", 6: "InitializeNonceAccount",
                          7: "AuthorizeNonceAccount", 8: "Allocate", 9: "AllocateWithSeed",
                          10: "AssignWithSeed", 11: "TransferWithSeed", 12: "UpgradeNonceAccount"}
            result["instruction_name"] = system_ixs.get(ix_type, f"Unknown({ix_type})")
            if ix_type == 2 and len(data) >= 12:  # Transfer
                lamports = struct.unpack_from("<Q", data, 4)[0]
                result["lamports"] = lamports
                result["sol"] = _lamports_to_sol(lamports)

        elif program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" and len(data) >= 1:
            ix_type = data[0]
            token_ixs = {0: "InitializeMint", 1: "InitializeAccount", 2: "InitializeMultisig",
                         3: "Transfer", 4: "Approve", 5: "Revoke", 6: "SetAuthority",
                         7: "MintTo", 8: "Burn", 9: "CloseAccount", 10: "FreezeAccount",
                         11: "ThawAccount", 12: "TransferChecked", 13: "ApproveChecked",
                         14: "MintToChecked", 15: "BurnChecked"}
            result["instruction_name"] = token_ixs.get(ix_type, f"Unknown({ix_type})")
            if ix_type == 3 and len(data) >= 9:  # Transfer
                amount = struct.unpack_from("<Q", data, 1)[0]
                result["amount"] = amount

        elif program_id == "ComputeBudget111111111111111111111111111111" and len(data) >= 1:
            ix_type = data[0]
            if ix_type == 2 and len(data) >= 5:
                result["instruction_name"] = "SetComputeUnitLimit"
                result["units"] = struct.unpack_from("<I", data, 1)[0]
            elif ix_type == 3 and len(data) >= 9:
                result["instruction_name"] = "SetComputeUnitPrice"
                result["micro_lamports"] = struct.unpack_from("<Q", data, 1)[0]
            else:
                result["instruction_name"] = f"ComputeBudget({ix_type})"

        elif program_id == "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr":
            result["instruction_name"] = "Memo"
            result["memo_text"] = data.decode("utf-8", errors="replace")

        return _ok(result)
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def fetch_anchor_idl(program_id: str) -> Dict[str, Any]:
    """Fetch Anchor IDL stored on-chain for a program (IDL account at deterministic PDA)."""
    try:
        # Anchor IDL PDA: seeds = ["anchor:idl", program_id]
        base = Pubkey.find_program_address(
            [b"anchor:idl", bytes(_pubkey(program_id))],
            _pubkey(program_id),
        )[0]

        resp = client.get_account_info(base)
        acct = resp.value
        if acct is None:
            return _err(f"No Anchor IDL found on-chain for program {program_id}")

        data = bytes(acct.data)
        # Anchor IDL account: 8 byte discriminator + 4 byte authority + compressed IDL
        if len(data) < 44:
            return _err("IDL account data too short")

        authority = str(Pubkey.from_bytes(data[8:40]))
        data_len = struct.unpack_from("<I", data, 40)[0]
        compressed = data[44:44 + data_len]

        import zlib
        try:
            idl_json = zlib.decompress(compressed)
            idl = json.loads(idl_json)
        except Exception:
            return _ok({
                "program_id": program_id,
                "authority": authority,
                "idl_data_length": data_len,
                "note": "IDL found but could not decompress. May use a different compression format.",
            })

        return _ok({
            "program_id": program_id,
            "authority": authority,
            "idl": idl,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# DEX & DEFI OPERATIONS (via HTTP APIs)
# ============================================================================

@mcp.tool()
async def get_jupiter_quote(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 50,
) -> Dict[str, Any]:
    """Get a Jupiter swap quote. Amount is in smallest token units (e.g., lamports for SOL)."""
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get(
                "https://quote-api.jup.ag/v6/quote",
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": str(amount),
                    "slippageBps": slippage_bps,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return _ok({
            "input_mint": data.get("inputMint"),
            "output_mint": data.get("outputMint"),
            "in_amount": data.get("inAmount"),
            "out_amount": data.get("outAmount"),
            "other_amount_threshold": data.get("otherAmountThreshold"),
            "price_impact_pct": data.get("priceImpactPct"),
            "slippage_bps": data.get("slippageBps"),
            "route_plan_count": len(data.get("routePlan", [])),
        })
    except httpx.HTTPStatusError as e:
        return _err(f"Jupiter API error: {e.response.status_code} {e.response.text}", "HTTPError")
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_token_price(mints: str) -> Dict[str, Any]:
    """Get token prices from Jupiter Price API. Pass comma-separated mint addresses."""
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(
                "https://api.jup.ag/price/v2",
                params={"ids": mints},
            )
            resp.raise_for_status()
            data = resp.json()

        prices = {}
        for mint_addr, info in data.get("data", {}).items():
            prices[mint_addr] = {
                "id": info.get("id"),
                "type": info.get("type"),
                "price": info.get("price"),
            }
        return _ok(prices, count=len(prices))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_raydium_pools(token_mint: Optional[str] = None) -> Dict[str, Any]:
    """Get Raydium AMM pool information from their API. Optionally filter by token mint."""
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            params = {}
            if token_mint:
                params["mint"] = token_mint
            resp = await http.get(
                "https://api-v3.raydium.io/pools/info/list",
                params={**params, "pageSize": 10, "page": 1},
            )
            resp.raise_for_status()
            data = resp.json()

        pools = []
        for pool in data.get("data", {}).get("data", []):
            pools.append({
                "id": pool.get("id"),
                "type": pool.get("type"),
                "mint_a": pool.get("mintA", {}).get("address"),
                "mint_b": pool.get("mintB", {}).get("address"),
                "tvl": pool.get("tvl"),
                "volume_24h": pool.get("day", {}).get("volume"),
                "apr_24h": pool.get("day", {}).get("apr"),
            })
        return _ok(pools, count=len(pools))
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_orca_whirlpools(token_a: Optional[str] = None, token_b: Optional[str] = None) -> Dict[str, Any]:
    """Get Orca Whirlpool information from their API."""
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get("https://api.mainnet.orca.so/v1/whirlpool/list")
            resp.raise_for_status()
            data = resp.json()

        pools = []
        for pool in data.get("whirlpools", [])[:50]:  # limit to 50
            pool_a = pool.get("tokenA", {}).get("mint", "")
            pool_b = pool.get("tokenB", {}).get("mint", "")
            if token_a and token_a not in (pool_a, pool_b):
                continue
            if token_b and token_b not in (pool_a, pool_b):
                continue
            pools.append({
                "address": pool.get("address"),
                "token_a_mint": pool_a,
                "token_b_mint": pool_b,
                "token_a_symbol": pool.get("tokenA", {}).get("symbol"),
                "token_b_symbol": pool.get("tokenB", {}).get("symbol"),
                "tvl": pool.get("tvl"),
                "volume_24h": pool.get("volume", {}).get("day"),
                "price": pool.get("price"),
            })
        return _ok(pools, count=len(pools))
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# UTILITY OPERATIONS
# ============================================================================

@mcp.tool()
async def validate_address(address: str) -> Dict[str, Any]:
    """Validate if a string is a valid Solana base58 address and check if it's on-curve."""
    try:
        pk = _pubkey(address)
        on_curve = pk.is_on_curve()
        return _ok({
            "address": address,
            "valid": True,
            "on_curve": on_curve,
            "is_pda": not on_curve,
        })
    except Exception:
        return _ok({"address": address, "valid": False, "on_curve": False, "is_pda": False})


@mcp.tool()
async def decode_base58(data: str) -> Dict[str, Any]:
    """Decode a base58-encoded string to hex and byte length."""
    try:
        decoded = base58.b58decode(data)
        return _ok({
            "input": data,
            "hex": decoded.hex(),
            "byte_length": len(decoded),
            "bytes_list": list(decoded),
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def parse_token_account(account_address: str) -> Dict[str, Any]:
    """Parse a raw SPL Token account, returning mint, owner, amount, delegate, and state."""
    try:
        resp = client.get_account_info(_pubkey(account_address))
        acct = resp.value
        if acct is None:
            return _err(f"Account {account_address} not found")

        data = bytes(acct.data)
        if len(data) < 165:
            return _err("Data too short for SPL token account (need 165 bytes)")

        mint = str(Pubkey.from_bytes(data[0:32]))
        owner = str(Pubkey.from_bytes(data[32:64]))
        amount = struct.unpack_from("<Q", data, 64)[0]
        delegate_option = struct.unpack_from("<I", data, 72)[0]
        delegate = str(Pubkey.from_bytes(data[76:108])) if delegate_option == 1 else None
        state = data[108]
        state_names = {0: "uninitialized", 1: "initialized", 2: "frozen"}
        is_native_option = struct.unpack_from("<I", data, 109)[0]
        is_native = is_native_option == 1
        delegated_amount = struct.unpack_from("<Q", data, 121)[0]
        close_authority_option = struct.unpack_from("<I", data, 129)[0]
        close_authority = str(Pubkey.from_bytes(data[133:165])) if close_authority_option == 1 else None

        return _ok({
            "address": account_address,
            "mint": mint,
            "owner": owner,
            "amount": amount,
            "delegate": delegate,
            "state": state_names.get(state, f"unknown({state})"),
            "is_native": is_native,
            "delegated_amount": delegated_amount,
            "close_authority": close_authority,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_slot() -> Dict[str, Any]:
    """Get the current slot number."""
    try:
        resp = client.get_slot()
        return _ok({"slot": resp.value})
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_block_time(slot: int) -> Dict[str, Any]:
    """Get the Unix timestamp for a given slot."""
    try:
        resp = client.get_block_time(slot)
        if resp.value is None:
            return _err(f"Block time not available for slot {slot}")
        return _ok({"slot": slot, "block_time": resp.value})
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# NETWORK & CLUSTER INFO (NEW — from scraped Solanakit docs)
# ============================================================================

@mcp.tool()
async def get_epoch_info() -> Dict[str, Any]:
    """Get current epoch information: epoch number, slot index, slots in epoch, etc."""
    try:
        resp = client.get_epoch_info()
        ei = resp.value
        return _ok({
            "epoch": ei.epoch,
            "slot_index": ei.slot_index,
            "slots_in_epoch": ei.slots_in_epoch,
            "absolute_slot": ei.absolute_slot,
            "block_height": ei.block_height,
            "transaction_count": ei.transaction_count,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_health() -> Dict[str, Any]:
    """Check if the RPC node is healthy."""
    try:
        resp = client.get_health()
        return _ok({"healthy": True, "status": str(resp)})
    except Exception as e:
        return _ok({"healthy": False, "status": str(e)})


@mcp.tool()
async def get_supply() -> Dict[str, Any]:
    """Get total, circulating, and non-circulating SOL supply."""
    try:
        resp = client.get_supply()
        val = resp.value
        return _ok({
            "total_lamports": val.total,
            "total_sol": _lamports_to_sol(val.total),
            "circulating_lamports": val.circulating,
            "circulating_sol": _lamports_to_sol(val.circulating),
            "non_circulating_lamports": val.non_circulating,
            "non_circulating_sol": _lamports_to_sol(val.non_circulating),
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_version() -> Dict[str, Any]:
    """Get the Solana software version running on the RPC node."""
    try:
        resp = client.get_version()
        val = resp.value
        return _ok({
            "solana_core": val.solana_core,
            "feature_set": val.feature_set,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_inflation_rate() -> Dict[str, Any]:
    """Get current inflation rate: total, validator, foundation, and epoch."""
    try:
        resp = client.get_inflation_rate()
        val = resp.value
        return _ok({
            "total": val.total,
            "validator": val.validator,
            "foundation": val.foundation,
            "epoch": val.epoch,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_minimum_balance_for_rent_exemption(data_length: int) -> Dict[str, Any]:
    """Get the minimum lamports needed for rent exemption for a given account data size."""
    try:
        resp = client.get_minimum_balance_for_rent_exemption(data_length)
        lamports = resp.value
        return _ok({
            "data_length": data_length,
            "lamports": lamports,
            "sol": _lamports_to_sol(lamports),
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_cluster_nodes() -> Dict[str, Any]:
    """Get information about all nodes in the cluster."""
    try:
        resp = client.get_cluster_nodes()
        nodes = []
        for n in resp.value[:20]:  # limit to 20
            nodes.append({
                "pubkey": str(n.pubkey),
                "gossip": n.gossip,
                "tpu": n.tpu,
                "rpc": n.rpc,
                "version": n.version,
            })
        return _ok(nodes, count=len(resp.value), showing=len(nodes))
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# PRIORITY FEES & COMPUTE BUDGET (NEW — from Kit compute-budget docs)
# ============================================================================

@mcp.tool()
async def get_recent_priority_fees(addresses: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get recent priority fee levels. Optionally filter by writable account addresses."""
    try:
        pubkeys = [_pubkey(a) for a in addresses] if addresses else None
        resp = client.get_recent_prioritization_fees(pubkeys)
        fees = []
        for f in resp.value[-20:]:  # last 20 slots
            fees.append({
                "slot": f.slot,
                "prioritization_fee": f.prioritization_fee,
            })

        if fees:
            fee_values = [f["prioritization_fee"] for f in fees if f["prioritization_fee"] > 0]
            stats = {
                "min": min(fee_values) if fee_values else 0,
                "max": max(fee_values) if fee_values else 0,
                "median": sorted(fee_values)[len(fee_values) // 2] if fee_values else 0,
                "mean": sum(fee_values) // len(fee_values) if fee_values else 0,
            }
        else:
            stats = {"min": 0, "max": 0, "median": 0, "mean": 0}

        return _ok({"recent_fees": fees, "statistics": stats})
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# STAKE & VOTE (NEW — from scraped docs)
# ============================================================================

@mcp.tool()
async def get_stake_activation(stake_account: str) -> Dict[str, Any]:
    """Get stake activation status for a stake account."""
    try:
        resp = client.get_stake_activation(_pubkey(stake_account))
        val = resp.value
        return _ok({
            "stake_account": stake_account,
            "state": str(val.state),
            "active": val.active,
            "inactive": val.inactive,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_vote_accounts() -> Dict[str, Any]:
    """Get current and delinquent vote accounts (validators)."""
    try:
        resp = client.get_vote_accounts()
        val = resp.value

        current = []
        for v in val.current[:20]:
            current.append({
                "vote_pubkey": str(v.vote_pubkey),
                "node_pubkey": str(v.node_pubkey),
                "activated_stake": v.activated_stake,
                "activated_stake_sol": _lamports_to_sol(v.activated_stake),
                "commission": v.commission,
                "last_vote": v.last_vote,
            })

        return _ok({
            "current_count": len(val.current),
            "delinquent_count": len(val.delinquent),
            "top_current_validators": current,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# ADDRESS LOOKUP TABLE (NEW — from Kit compressTransactionMessageUsingAddressLookupTables)
# ============================================================================

@mcp.tool()
async def get_address_lookup_table(address: str) -> Dict[str, Any]:
    """Fetch and decode an Address Lookup Table (ALT), returning all stored addresses."""
    try:
        resp = client.get_account_info(_pubkey(address))
        acct = resp.value
        if acct is None:
            return _err(f"Address lookup table {address} not found")

        if str(acct.owner) != "AddressLookupTab1e1111111111111111111111111":
            return _err(f"Account {address} is not an address lookup table (owner: {acct.owner})")

        data = bytes(acct.data)
        # ALT layout: 4 bytes type, 8 bytes deactivation_slot, ... 56 bytes header, then 32-byte addresses
        if len(data) < 56:
            return _err("Data too short for ALT")

        deactivation_slot = struct.unpack_from("<Q", data, 4)[0]
        last_extended_slot = struct.unpack_from("<Q", data, 16)[0]
        authority_option = data[12]
        authority = str(Pubkey.from_bytes(data[24:56])) if authority_option == 1 else None

        addr_data = data[56:]
        num_addresses = len(addr_data) // 32
        addresses = []
        for i in range(num_addresses):
            addr_bytes = addr_data[i * 32:(i + 1) * 32]
            addresses.append(str(Pubkey.from_bytes(addr_bytes)))

        return _ok({
            "address": address,
            "authority": authority,
            "deactivation_slot": deactivation_slot if deactivation_slot != 0xFFFFFFFFFFFFFFFF else None,
            "last_extended_slot": last_extended_slot,
            "num_addresses": num_addresses,
            "addresses": addresses,
        })
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# COMPOSITE / CONVENIENCE TOOLS (NEW — discovered from analyzing docs)
# ============================================================================

@mcp.tool()
async def resolve_token_info(mint: str) -> Dict[str, Any]:
    """All-in-one: get mint details, metadata, supply, and current price for a token."""
    try:
        result: Dict[str, Any] = {"mint": mint}

        # Mint info
        mint_data = await get_mint_info.fn(mint)
        if mint_data["success"]:
            result["mint_info"] = mint_data["data"]

        # Metadata
        meta_data = await decode_token_metadata.fn(mint)
        if meta_data["success"]:
            result["metadata"] = meta_data["data"]

        # Supply
        supply_data = await get_token_supply.fn(mint)
        if supply_data["success"]:
            result["supply"] = supply_data["data"]

        # Price
        price_data = await get_token_price.fn(mint)
        if price_data["success"]:
            result["price"] = price_data["data"].get(mint)

        return _ok(result)
    except Exception as e:
        return _err(str(e), type(e).__name__)


@mcp.tool()
async def get_wallet_overview(address: str) -> Dict[str, Any]:
    """Get a complete wallet overview: SOL balance, token accounts, and recent transactions."""
    try:
        result: Dict[str, Any] = {"address": address}

        # SOL balance
        bal = await get_balance.fn(address)
        if bal["success"]:
            result["sol_balance"] = bal["data"]

        # Token accounts
        tokens = await get_token_accounts.fn(address)
        if tokens["success"]:
            result["token_accounts"] = tokens["data"][:20]  # limit to 20
            result["token_count"] = tokens.get("count", 0)

        # Recent transactions
        sigs = await get_signatures_for_address.fn(address, limit=5)
        if sigs["success"]:
            result["recent_transactions"] = sigs["data"]

        return _ok(result)
    except Exception as e:
        return _err(str(e), type(e).__name__)


# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    mcp.run()


if __name__ == "__main__":
    main()
