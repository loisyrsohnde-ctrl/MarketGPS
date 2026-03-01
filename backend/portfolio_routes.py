"""
MarketGPS Portfolio Sync Module
================================
Portfolio synchronization (read-only) via CSV import and manual entry.
NOT A BROKER - research/statistics tool only.

Endpoints:
- POST /api/portfolio/import/csv     - Import positions from CSV
- POST /api/portfolio/positions      - Manual position entry
- GET  /api/portfolio/accounts       - List user accounts
- GET  /api/portfolio/positions      - List user positions
- GET  /api/portfolio/transactions   - List transactions
- GET  /api/portfolio/summary        - Portfolio summary
- GET  /api/portfolio/sync-runs      - Import/sync history
- DELETE /api/portfolio/accounts/{id} - Delete account

Legal: Research tool only. No trading advice or execution.
"""

import os
import csv
import json
import uuid
import hashlib
import logging
from io import StringIO
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Header
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def _get_db():
    """Get database connection."""
    try:
        from storage.sqlite_store import SQLiteStore
        return SQLiteStore()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


def _ensure_portfolio_tables():
    """
    Create portfolio tables if they don't exist.
    Called on module load and before operations.
    """
    db = _get_db()
    
    with db._get_connection() as conn:
        # ═══════════════════════════════════════════════════════════════════════
        # portfolio_accounts: User's broker accounts / envelopes
        # ═══════════════════════════════════════════════════════════════════════
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                broker TEXT,
                account_type TEXT DEFAULT 'CTO',
                currency TEXT DEFAULT 'EUR',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                last_sync_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_accounts_user ON portfolio_accounts(user_id)")
        
        # ═══════════════════════════════════════════════════════════════════════
        # portfolio_positions: Current holdings
        # ═══════════════════════════════════════════════════════════════════════
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_positions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_id TEXT,
                symbol TEXT NOT NULL,
                isin TEXT,
                asset_id TEXT,
                name TEXT,
                quantity REAL NOT NULL DEFAULT 0,
                avg_cost REAL,
                currency TEXT DEFAULT 'EUR',
                asset_type TEXT DEFAULT 'EQUITY',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (account_id) REFERENCES portfolio_accounts(id) ON DELETE SET NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_positions_user ON portfolio_positions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_positions_account ON portfolio_positions(account_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_positions_symbol ON portfolio_positions(symbol)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_positions_unique ON portfolio_positions(user_id, account_id, symbol)")
        
        # ═══════════════════════════════════════════════════════════════════════
        # portfolio_transactions: Buy/sell history
        # ═══════════════════════════════════════════════════════════════════════
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_id TEXT,
                position_id TEXT,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'TRANSFER_IN', 'TRANSFER_OUT', 'SPLIT', 'OTHER')),
                quantity REAL NOT NULL,
                price REAL,
                total_amount REAL,
                currency TEXT DEFAULT 'EUR',
                fees REAL DEFAULT 0,
                executed_at TEXT NOT NULL,
                notes TEXT,
                import_source TEXT,
                import_run_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (account_id) REFERENCES portfolio_accounts(id) ON DELETE SET NULL,
                FOREIGN KEY (position_id) REFERENCES portfolio_positions(id) ON DELETE SET NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_user ON portfolio_transactions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_symbol ON portfolio_transactions(symbol)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_date ON portfolio_transactions(executed_at)")
        
        # ═══════════════════════════════════════════════════════════════════════
        # portfolio_sync_runs: Audit log for imports
        # ═══════════════════════════════════════════════════════════════════════
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_sync_runs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_id TEXT,
                source_type TEXT NOT NULL CHECK(source_type IN ('CSV', 'MANUAL', 'API')),
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
                file_hash TEXT,
                rows_total INTEGER DEFAULT 0,
                rows_imported INTEGER DEFAULT 0,
                rows_skipped INTEGER DEFAULT 0,
                rows_errors INTEGER DEFAULT 0,
                error_log TEXT,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                metadata_json TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_runs_user ON portfolio_sync_runs(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_runs_hash ON portfolio_sync_runs(file_hash)")
        
        logger.info("✅ Portfolio tables verified/created")


# Initialize tables on module load
try:
    _ensure_portfolio_tables()
except Exception as e:
    logger.warning(f"Portfolio tables initialization deferred: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AccountCreate(BaseModel):
    """Create a new portfolio account."""
    name: str = Field(..., min_length=1, max_length=100)
    broker: Optional[str] = None
    account_type: str = "CTO"  # CTO, PEA, PEA-PME, AV, COMPTE_TITRES, CRYPTO
    currency: str = "EUR"
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    """Portfolio account response."""
    id: str
    name: str
    broker: Optional[str]
    account_type: str
    currency: str
    notes: Optional[str]
    created_at: str
    last_sync_at: Optional[str]
    position_count: int = 0
    total_value: float = 0.0


class PositionCreate(BaseModel):
    """Create or update a position."""
    account_id: Optional[str] = None
    symbol: str = Field(..., min_length=1, max_length=20)
    isin: Optional[str] = None
    name: Optional[str] = None
    quantity: float = Field(..., gt=0)
    avg_cost: Optional[float] = None
    currency: str = "EUR"
    asset_type: str = "EQUITY"
    notes: Optional[str] = None


class PositionResponse(BaseModel):
    """Portfolio position response."""
    id: str
    account_id: Optional[str]
    account_name: Optional[str]
    symbol: str
    isin: Optional[str]
    asset_id: Optional[str]
    name: Optional[str]
    quantity: float
    avg_cost: Optional[float]
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    currency: str
    asset_type: str
    score: Optional[float] = None
    updated_at: str


class TransactionResponse(BaseModel):
    """Transaction history response."""
    id: str
    symbol: str
    transaction_type: str
    quantity: float
    price: Optional[float]
    total_amount: Optional[float]
    currency: str
    fees: float
    executed_at: str
    notes: Optional[str]


class CSVMappingRequest(BaseModel):
    """CSV column mapping configuration."""
    symbol_column: str
    quantity_column: str
    avg_cost_column: Optional[str] = None
    isin_column: Optional[str] = None
    name_column: Optional[str] = None
    currency_column: Optional[str] = None
    account_id: Optional[str] = None
    skip_header: bool = True


class PortfolioSummary(BaseModel):
    """Portfolio summary with aggregations."""
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_percent: float
    position_count: int
    account_count: int
    currency: str = "EUR"
    allocation_by_type: Dict[str, float]
    allocation_by_sector: Dict[str, float]
    top_holdings: List[Dict[str, Any]]
    last_sync_at: Optional[str]


class SyncRunResponse(BaseModel):
    """Sync run history entry."""
    id: str
    source_type: str
    status: str
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_errors: int
    started_at: str
    completed_at: Optional[str]


# ═══════════════════════════════════════════════════════════════════════════════
# BROKER CSV TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

BROKER_TEMPLATES = {
    "generic": {
        "name": "Format Générique",
        "description": "CSV standard avec colonnes Symbol, Quantity, AvgCost",
        "mapping": {
            "symbol_column": "Symbol",
            "quantity_column": "Quantity",
            "avg_cost_column": "AvgCost",
            "name_column": "Name",
            "isin_column": "ISIN",
        },
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "boursorama": {
        "name": "Boursorama",
        "description": "Export Boursorama Banque",
        "mapping": {
            "symbol_column": "Code",
            "quantity_column": "Quantité",
            "avg_cost_column": "PRU",
            "name_column": "Libellé",
            "isin_column": "ISIN",
        },
        "delimiter": ";",
        "encoding": "utf-8",
    },
    "degiro": {
        "name": "DEGIRO",
        "description": "Export DEGIRO",
        "mapping": {
            "symbol_column": "Symbole",
            "quantity_column": "Quantité",
            "avg_cost_column": "Prix de revient",
            "name_column": "Produit",
            "isin_column": "ISIN",
        },
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "interactive_brokers": {
        "name": "Interactive Brokers",
        "description": "Export IBKR Activity Statement",
        "mapping": {
            "symbol_column": "Symbol",
            "quantity_column": "Quantity",
            "avg_cost_column": "Cost Basis",
            "name_column": "Description",
            "isin_column": "ISIN",
        },
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "trade_republic": {
        "name": "Trade Republic",
        "description": "Export Trade Republic",
        "mapping": {
            "symbol_column": "ISIN",
            "quantity_column": "Anzahl",
            "avg_cost_column": "Einstiegspreis",
            "name_column": "Name",
            "isin_column": "ISIN",
        },
        "delimiter": ";",
        "encoding": "utf-8",
    },
    "fortuneo": {
        "name": "Fortuneo",
        "description": "Export Fortuneo",
        "mapping": {
            "symbol_column": "Code valeur",
            "quantity_column": "Quantité",
            "avg_cost_column": "PRU",
            "name_column": "Libellé valeur",
            "isin_column": "Code ISIN",
        },
        "delimiter": ";",
        "encoding": "iso-8859-1",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_user_id(authorization: Optional[str] = None) -> str:
    """
    Extract user ID from authorization header.
    Falls back to 'default' for development.
    """
    if not authorization:
        return "default"
    
    try:
        from security import verify_supabase_token
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            payload = verify_supabase_token(parts[1])
            if payload and payload.get("sub"):
                return payload["sub"]
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
    
    return "default"


def _resolve_symbol_to_asset(symbol: str, isin: Optional[str] = None) -> Optional[str]:
    """
    Resolve a symbol/ISIN to an asset_id in the MarketGPS universe.
    Returns None if not found (position will still be created).
    """
    try:
        db = _get_db()
        with db._get_connection() as conn:
            # Try by ISIN first (most reliable)
            if isin:
                row = conn.execute(
                    "SELECT asset_id FROM universe WHERE isin = ? AND active = 1",
                    (isin.upper(),)
                ).fetchone()
                if row:
                    return row["asset_id"]
            
            # Try by symbol (various formats)
            symbol_upper = symbol.upper().strip()
            for pattern in [symbol_upper, f"{symbol_upper}.US", f"{symbol_upper}.PA", f"{symbol_upper}.XETRA"]:
                row = conn.execute(
                    "SELECT asset_id FROM universe WHERE (symbol = ? OR asset_id = ?) AND active = 1",
                    (pattern, pattern)
                ).fetchone()
                if row:
                    return row["asset_id"]
    except Exception as e:
        logger.warning(f"Symbol resolution failed for {symbol}: {e}")
    
    return None


def _get_current_price(asset_id: str) -> Optional[float]:
    """Get current price for an asset from MarketGPS data."""
    if not asset_id:
        return None
    
    try:
        db = _get_db()
        with db._get_connection() as conn:
            row = conn.execute(
                "SELECT price FROM prices_latest WHERE asset_id = ?",
                (asset_id,)
            ).fetchone()
            if row:
                return float(row["price"])
    except Exception as e:
        logger.debug(f"Price lookup failed for {asset_id}: {e}")
    
    return None


def _get_asset_score(asset_id: str) -> Optional[float]:
    """Get MarketGPS score for an asset."""
    if not asset_id:
        return None
    
    try:
        db = _get_db()
        with db._get_connection() as conn:
            row = conn.execute(
                "SELECT score_total FROM scores_latest WHERE asset_id = ?",
                (asset_id,)
            ).fetchone()
            if row and row["score_total"]:
                return float(row["score_total"])
    except Exception as e:
        logger.debug(f"Score lookup failed for {asset_id}: {e}")
    
    return None


def _compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content for idempotency check."""
    return hashlib.sha256(content).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# API ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ═══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/disclaimer")
async def get_disclaimer():
    """
    Returns the legal disclaimer for the portfolio sync feature.
    Must be acknowledged before first import.
    """
    return {
        "title": "Outil de Recherche & Statistiques",
        "content": """
MarketGPS est un outil de recherche et d'analyse statistique. 
Il ne constitue PAS un conseil en investissement.

En utilisant la synchronisation de portefeuille, vous comprenez que :

1. **Lecture seule** : MarketGPS n'exécute aucun ordre. Aucune connexion 
   à vos comptes de courtage n'est utilisée pour le trading.

2. **Pas de conseil** : Les scores, analyses et données affichés sont 
   des indicateurs statistiques, pas des recommandations d'achat ou de vente.

3. **Vos données** : Vos positions sont stockées de manière sécurisée 
   et ne sont jamais partagées avec des tiers.

4. **Responsabilité** : Toute décision d'investissement reste de votre 
   entière responsabilité. Consultez un conseiller financier agréé.
        """,
        "version": "1.0",
        "requires_acknowledgment": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BROKER TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/templates")
async def list_broker_templates():
    """List available CSV import templates by broker."""
    return {
        "templates": [
            {
                "id": key,
                "name": val["name"],
                "description": val["description"],
            }
            for key, val in BROKER_TEMPLATES.items()
        ]
    }


@router.get("/templates/{template_id}")
async def get_broker_template(template_id: str):
    """Get specific broker template configuration."""
    template = BROKER_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    return {
        "id": template_id,
        **template
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNTS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """List all portfolio accounts for current user."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        rows = conn.execute("""
            SELECT 
                a.*,
                COUNT(p.id) as position_count,
                COALESCE(SUM(p.quantity * COALESCE(p.avg_cost, 0)), 0) as total_value
            FROM portfolio_accounts a
            LEFT JOIN portfolio_positions p ON p.account_id = a.id
            WHERE a.user_id = ? AND a.is_active = 1
            GROUP BY a.id
            ORDER BY a.created_at DESC
        """, (user_id,)).fetchall()
        
        return [
            AccountResponse(
                id=row["id"],
                name=row["name"],
                broker=row["broker"],
                account_type=row["account_type"],
                currency=row["currency"],
                notes=row["notes"],
                created_at=row["created_at"],
                last_sync_at=row["last_sync_at"],
                position_count=row["position_count"],
                total_value=float(row["total_value"]),
            )
            for row in rows
        ]


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account: AccountCreate,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Create a new portfolio account."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    account_id = str(uuid.uuid4())[:16]
    
    with db._get_connection() as conn:
        conn.execute("""
            INSERT INTO portfolio_accounts (id, user_id, name, broker, account_type, currency, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (account_id, user_id, account.name, account.broker, account.account_type, 
              account.currency, account.notes))
    
    logger.info(f"Created portfolio account: {account_id} for user {user_id}")
    
    return AccountResponse(
        id=account_id,
        name=account.name,
        broker=account.broker,
        account_type=account.account_type,
        currency=account.currency,
        notes=account.notes,
        created_at=datetime.utcnow().isoformat(),
        last_sync_at=None,
        position_count=0,
        total_value=0.0,
    )


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Soft delete a portfolio account."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        result = conn.execute("""
            UPDATE portfolio_accounts 
            SET is_active = 0, updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
        """, (account_id, user_id))
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
    
    logger.info(f"Deleted portfolio account: {account_id}")
    return {"status": "deleted", "id": account_id}


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIONS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    account_id: Optional[str] = None,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """List all positions for current user, optionally filtered by account."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        query = """
            SELECT 
                p.*,
                a.name as account_name
            FROM portfolio_positions p
            LEFT JOIN portfolio_accounts a ON a.id = p.account_id
            WHERE p.user_id = ?
        """
        params = [user_id]
        
        if account_id:
            query += " AND p.account_id = ?"
            params.append(account_id)
        
        query += " ORDER BY (p.quantity * COALESCE(p.avg_cost, 0)) DESC"
        
        rows = conn.execute(query, params).fetchall()
        
        positions = []
        for row in rows:
            # Get current price and score from MarketGPS data
            current_price = _get_current_price(row["asset_id"])
            score = _get_asset_score(row["asset_id"])
            
            # Calculate current value and P&L
            quantity = float(row["quantity"])
            avg_cost = float(row["avg_cost"]) if row["avg_cost"] else None
            
            if current_price and quantity:
                current_value = quantity * current_price
            elif avg_cost and quantity:
                current_value = quantity * avg_cost
            else:
                current_value = None
            
            if current_price and avg_cost and quantity:
                cost_basis = quantity * avg_cost
                pnl = current_value - cost_basis
                pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            else:
                pnl = None
                pnl_percent = None
            
            positions.append(PositionResponse(
                id=row["id"],
                account_id=row["account_id"],
                account_name=row["account_name"],
                symbol=row["symbol"],
                isin=row["isin"],
                asset_id=row["asset_id"],
                name=row["name"],
                quantity=quantity,
                avg_cost=avg_cost,
                current_price=current_price,
                current_value=current_value,
                pnl=pnl,
                pnl_percent=pnl_percent,
                currency=row["currency"],
                asset_type=row["asset_type"],
                score=score,
                updated_at=row["updated_at"],
            ))
        
        return positions


@router.post("/positions", response_model=PositionResponse)
async def create_or_update_position(
    position: PositionCreate,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Create or update a position (upsert by user+account+symbol)."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    # Resolve symbol to asset_id
    asset_id = _resolve_symbol_to_asset(position.symbol, position.isin)
    
    with db._get_connection() as conn:
        # Check if position exists
        existing = conn.execute("""
            SELECT id FROM portfolio_positions 
            WHERE user_id = ? AND account_id IS ? AND symbol = ?
        """, (user_id, position.account_id, position.symbol.upper())).fetchone()
        
        if existing:
            # Update existing position
            position_id = existing["id"]
            conn.execute("""
                UPDATE portfolio_positions SET
                    quantity = ?,
                    avg_cost = COALESCE(?, avg_cost),
                    isin = COALESCE(?, isin),
                    name = COALESCE(?, name),
                    asset_id = COALESCE(?, asset_id),
                    currency = ?,
                    asset_type = ?,
                    notes = COALESCE(?, notes),
                    updated_at = datetime('now')
                WHERE id = ?
            """, (position.quantity, position.avg_cost, position.isin, 
                  position.name, asset_id, position.currency, 
                  position.asset_type, position.notes, position_id))
            logger.info(f"Updated position: {position_id}")
        else:
            # Create new position
            position_id = str(uuid.uuid4())[:16]
            conn.execute("""
                INSERT INTO portfolio_positions 
                (id, user_id, account_id, symbol, isin, asset_id, name, quantity, avg_cost, currency, asset_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (position_id, user_id, position.account_id, position.symbol.upper(),
                  position.isin, asset_id, position.name, position.quantity,
                  position.avg_cost, position.currency, position.asset_type, position.notes))
            logger.info(f"Created position: {position_id}")
    
    # Return the position with enriched data
    current_price = _get_current_price(asset_id)
    score = _get_asset_score(asset_id)
    
    current_value = None
    pnl = None
    pnl_percent = None
    
    if current_price:
        current_value = position.quantity * current_price
        if position.avg_cost:
            cost_basis = position.quantity * position.avg_cost
            pnl = current_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
    
    return PositionResponse(
        id=position_id,
        account_id=position.account_id,
        account_name=None,
        symbol=position.symbol.upper(),
        isin=position.isin,
        asset_id=asset_id,
        name=position.name,
        quantity=position.quantity,
        avg_cost=position.avg_cost,
        current_price=current_price,
        current_value=current_value,
        pnl=pnl,
        pnl_percent=pnl_percent,
        currency=position.currency,
        asset_type=position.asset_type,
        score=score,
        updated_at=datetime.utcnow().isoformat(),
    )


@router.delete("/positions/{position_id}")
async def delete_position(
    position_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Delete a position."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        result = conn.execute("""
            DELETE FROM portfolio_positions WHERE id = ? AND user_id = ?
        """, (position_id, user_id))
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Position not found")
    
    return {"status": "deleted", "id": position_id}


# ═══════════════════════════════════════════════════════════════════════════════
# CSV IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/import/csv/preview")
async def preview_csv_import(
    file: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    delimiter: Optional[str] = Form(","),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Preview CSV import: parse file and return column detection + sample rows.
    Does NOT import any data.
    """
    content = await file.read()
    
    try:
        # Try different encodings
        for encoding in ["utf-8", "iso-8859-1", "cp1252"]:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise HTTPException(status_code=400, detail="Unable to decode file encoding")
        
        # Get template if specified
        template = BROKER_TEMPLATES.get(template_id) if template_id else None
        if template:
            delimiter = template.get("delimiter", delimiter)
        
        # Parse CSV
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        headers = reader.fieldnames or []
        
        # Get sample rows (max 5)
        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 5:
                break
            sample_rows.append(dict(row))
        
        # Auto-detect column mapping
        suggested_mapping = {}
        header_lower = {h.lower(): h for h in headers}
        
        # Symbol column detection
        for candidate in ["symbol", "ticker", "code", "symbole", "code valeur", "isin"]:
            if candidate in header_lower:
                suggested_mapping["symbol_column"] = header_lower[candidate]
                break
        
        # Quantity column detection
        for candidate in ["quantity", "quantité", "qty", "shares", "anzahl", "nb", "nombre"]:
            if candidate in header_lower:
                suggested_mapping["quantity_column"] = header_lower[candidate]
                break
        
        # Cost column detection
        for candidate in ["avg_cost", "avgcost", "pru", "prix de revient", "cost basis", "einstiegspreis", "prix moyen"]:
            if candidate in header_lower:
                suggested_mapping["avg_cost_column"] = header_lower[candidate]
                break
        
        # Name column detection
        for candidate in ["name", "nom", "libellé", "description", "produit", "libellé valeur"]:
            if candidate in header_lower:
                suggested_mapping["name_column"] = header_lower[candidate]
                break
        
        # ISIN column detection
        for candidate in ["isin", "code isin"]:
            if candidate in header_lower:
                suggested_mapping["isin_column"] = header_lower[candidate]
                break
        
        # Override with template mapping if available
        if template:
            for key, val in template["mapping"].items():
                if val in headers:
                    suggested_mapping[key] = val
        
        return {
            "filename": file.filename,
            "file_size": len(content),
            "file_hash": _compute_file_hash(content),
            "encoding_detected": encoding,
            "delimiter": delimiter,
            "headers": headers,
            "row_count": len(sample_rows),
            "sample_rows": sample_rows,
            "suggested_mapping": suggested_mapping,
            "template_applied": template_id,
        }
        
    except Exception as e:
        logger.error(f"CSV preview failed: {e}")
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    mapping: str = Form(...),  # JSON string of CSVMappingRequest
    account_id: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Import positions from CSV file.
    Idempotent: re-importing same file (by hash) updates positions without duplicating.
    """
    user_id = _get_user_id(authorization)
    db = _get_db()

    # CSV import is Pro-only
    try:
        from billing_routes import get_subscription, is_subscription_active
        sub = get_subscription(user_id, db)
        if not is_subscription_active(sub):
            raise HTTPException(
                status_code=403,
                detail="L'import CSV est réservé aux abonnés Pro. Passez à Pro pour importer votre portefeuille."
            )
    except ImportError:
        pass  # billing module not available, allow import

    content = await file.read()
    file_hash = _compute_file_hash(content)
    
    # Check for duplicate import (idempotency)
    with db._get_connection() as conn:
        existing = conn.execute("""
            SELECT id, status FROM portfolio_sync_runs 
            WHERE user_id = ? AND file_hash = ? AND status = 'completed'
            ORDER BY started_at DESC LIMIT 1
        """, (user_id, file_hash)).fetchone()
        
        if existing:
            logger.info(f"Duplicate import detected: {file_hash}")
            # Continue anyway - will update positions
    
    # Parse mapping
    try:
        mapping_data = json.loads(mapping)
        csv_mapping = CSVMappingRequest(**mapping_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid mapping: {e}")
    
    # Create sync run log
    run_id = str(uuid.uuid4())[:16]
    
    with db._get_connection() as conn:
        conn.execute("""
            INSERT INTO portfolio_sync_runs 
            (id, user_id, account_id, source_type, status, file_hash, metadata_json)
            VALUES (?, ?, ?, 'CSV', 'processing', ?, ?)
        """, (run_id, user_id, account_id, file_hash, json.dumps({
            "filename": file.filename,
            "template": template_id,
        })))
    
    # Parse and import
    try:
        # Get template settings
        template = BROKER_TEMPLATES.get(template_id) if template_id else None
        delimiter = template.get("delimiter", ",") if template else ","
        encoding = template.get("encoding", "utf-8") if template else "utf-8"
        
        # Decode content
        for enc in [encoding, "utf-8", "iso-8859-1", "cp1252"]:
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        
        rows_total = 0
        rows_imported = 0
        rows_skipped = 0
        rows_errors = 0
        errors = []
        
        with db._get_connection() as conn:
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                rows_total += 1
                
                try:
                    # Extract values using mapping
                    symbol = row.get(csv_mapping.symbol_column, "").strip()
                    quantity_str = row.get(csv_mapping.quantity_column, "").strip()
                    
                    if not symbol or not quantity_str:
                        rows_skipped += 1
                        continue
                    
                    # Parse quantity (handle different formats)
                    quantity_str = quantity_str.replace(",", ".").replace(" ", "")
                    try:
                        quantity = float(quantity_str)
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid quantity '{quantity_str}'")
                        rows_errors += 1
                        continue
                    
                    if quantity <= 0:
                        rows_skipped += 1
                        continue
                    
                    # Parse optional fields
                    avg_cost = None
                    if csv_mapping.avg_cost_column:
                        cost_str = row.get(csv_mapping.avg_cost_column, "").strip()
                        if cost_str:
                            cost_str = cost_str.replace(",", ".").replace(" ", "").replace("€", "").replace("$", "")
                            try:
                                avg_cost = float(cost_str)
                            except ValueError:
                                pass
                    
                    isin = None
                    if csv_mapping.isin_column:
                        isin = row.get(csv_mapping.isin_column, "").strip() or None
                    
                    name = None
                    if csv_mapping.name_column:
                        name = row.get(csv_mapping.name_column, "").strip() or None
                    
                    # Resolve to MarketGPS asset
                    asset_id = _resolve_symbol_to_asset(symbol, isin)
                    
                    # Upsert position
                    position_id = str(uuid.uuid4())[:16]
                    conn.execute("""
                        INSERT INTO portfolio_positions 
                        (id, user_id, account_id, symbol, isin, asset_id, name, quantity, avg_cost, currency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id, account_id, symbol) DO UPDATE SET
                            quantity = excluded.quantity,
                            avg_cost = COALESCE(excluded.avg_cost, portfolio_positions.avg_cost),
                            isin = COALESCE(excluded.isin, portfolio_positions.isin),
                            name = COALESCE(excluded.name, portfolio_positions.name),
                            asset_id = COALESCE(excluded.asset_id, portfolio_positions.asset_id),
                            updated_at = datetime('now')
                    """, (position_id, user_id, account_id, symbol.upper(), isin, 
                          asset_id, name, quantity, avg_cost, csv_mapping.currency_column or "EUR"))
                    
                    rows_imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    rows_errors += 1
        
        # Update sync run status
        status = "completed" if rows_errors == 0 else "partial"
        
        with db._get_connection() as conn:
            conn.execute("""
                UPDATE portfolio_sync_runs SET
                    status = ?,
                    rows_total = ?,
                    rows_imported = ?,
                    rows_skipped = ?,
                    rows_errors = ?,
                    error_log = ?,
                    completed_at = datetime('now')
                WHERE id = ?
            """, (status, rows_total, rows_imported, rows_skipped, rows_errors,
                  json.dumps(errors) if errors else None, run_id))
            
            # Update account last_sync_at
            if account_id:
                conn.execute("""
                    UPDATE portfolio_accounts SET last_sync_at = datetime('now')
                    WHERE id = ? AND user_id = ?
                """, (account_id, user_id))
        
        logger.info(f"CSV import completed: {rows_imported}/{rows_total} positions imported")
        
        return {
            "status": status,
            "run_id": run_id,
            "rows_total": rows_total,
            "rows_imported": rows_imported,
            "rows_skipped": rows_skipped,
            "rows_errors": rows_errors,
            "errors": errors[:10] if errors else [],  # Limit error display
        }
        
    except Exception as e:
        logger.error(f"CSV import failed: {e}")
        
        with db._get_connection() as conn:
            conn.execute("""
                UPDATE portfolio_sync_runs SET
                    status = 'failed',
                    error_log = ?,
                    completed_at = datetime('now')
                WHERE id = ?
            """, (str(e), run_id))
        
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get portfolio summary with aggregations."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        # Get all positions
        positions = conn.execute("""
            SELECT * FROM portfolio_positions WHERE user_id = ?
        """, (user_id,)).fetchall()
        
        if not positions:
            return PortfolioSummary(
                total_value=0,
                total_cost=0,
                total_pnl=0,
                total_pnl_percent=0,
                position_count=0,
                account_count=0,
                allocation_by_type={},
                allocation_by_sector={},
                top_holdings=[],
                last_sync_at=None,
            )
        
        # Calculate totals
        total_value = 0
        total_cost = 0
        allocation_by_type = {}
        top_holdings = []
        
        for pos in positions:
            quantity = float(pos["quantity"])
            avg_cost = float(pos["avg_cost"]) if pos["avg_cost"] else 0
            
            current_price = _get_current_price(pos["asset_id"])
            if current_price:
                value = quantity * current_price
            else:
                value = quantity * avg_cost
            
            cost = quantity * avg_cost
            
            total_value += value
            total_cost += cost
            
            # Allocation by type
            asset_type = pos["asset_type"] or "OTHER"
            allocation_by_type[asset_type] = allocation_by_type.get(asset_type, 0) + value
            
            # Top holdings
            top_holdings.append({
                "symbol": pos["symbol"],
                "name": pos["name"],
                "value": value,
                "quantity": quantity,
                "pnl": value - cost if cost > 0 else 0,
                "score": _get_asset_score(pos["asset_id"]),
            })
        
        # Sort top holdings by value
        top_holdings.sort(key=lambda x: x["value"], reverse=True)
        top_holdings = top_holdings[:10]
        
        # Convert allocation to percentages
        if total_value > 0:
            allocation_by_type = {k: round(v / total_value * 100, 1) for k, v in allocation_by_type.items()}
        
        # Get account count
        account_count = conn.execute("""
            SELECT COUNT(DISTINCT id) FROM portfolio_accounts WHERE user_id = ? AND is_active = 1
        """, (user_id,)).fetchone()[0]
        
        # Get last sync
        last_sync = conn.execute("""
            SELECT MAX(completed_at) FROM portfolio_sync_runs 
            WHERE user_id = ? AND status = 'completed'
        """, (user_id,)).fetchone()[0]
        
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return PortfolioSummary(
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_percent=round(total_pnl_percent, 2),
            position_count=len(positions),
            account_count=account_count,
            allocation_by_type=allocation_by_type,
            allocation_by_sector={},  # TODO: sector data from universe
            top_holdings=top_holdings,
            last_sync_at=last_sync,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    limit: int = Query(50, le=200),
    offset: int = 0,
    symbol: Optional[str] = None,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """List transaction history."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        query = """
            SELECT * FROM portfolio_transactions 
            WHERE user_id = ?
        """
        params = [user_id]
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol.upper())
        
        query += " ORDER BY executed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        
        return [
            TransactionResponse(
                id=row["id"],
                symbol=row["symbol"],
                transaction_type=row["transaction_type"],
                quantity=float(row["quantity"]),
                price=float(row["price"]) if row["price"] else None,
                total_amount=float(row["total_amount"]) if row["total_amount"] else None,
                currency=row["currency"],
                fees=float(row["fees"]) if row["fees"] else 0,
                executed_at=row["executed_at"],
                notes=row["notes"],
            )
            for row in rows
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC RUNS HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/sync-runs", response_model=List[SyncRunResponse])
async def list_sync_runs(
    limit: int = Query(20, le=100),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """List import/sync history."""
    user_id = _get_user_id(authorization)
    db = _get_db()
    
    with db._get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM portfolio_sync_runs 
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        
        return [
            SyncRunResponse(
                id=row["id"],
                source_type=row["source_type"],
                status=row["status"],
                rows_total=row["rows_total"],
                rows_imported=row["rows_imported"],
                rows_skipped=row["rows_skipped"],
                rows_errors=row["rows_errors"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]
