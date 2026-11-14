"""asset_universe_classifier.py: Institutional Asset Sector Classifier for Delta Exchange India.
Categorizes all perpetual futures into 5 distinct uncorrelated asset classes:
1. COMMODITIES_METALS
2. INDICES_ETFS
3. TRADFI_EQUITIES
4. CRYPTO_MAJORS
5. CRYPTO_ALTS_TOKENS
"""

import os
import re

SECTOR_COMMODITIES_METALS = "COMMODITIES_METALS"
SECTOR_INDICES_ETFS = "INDICES_ETFS"
SECTOR_TRADFI_EQUITIES = "TRADFI_EQUITIES"
SECTOR_CRYPTO_MAJORS = "CRYPTO_MAJORS"
SECTOR_CRYPTO_ALTS_TOKENS = "CRYPTO_ALTS_TOKENS"

ALL_SECTORS = [
    SECTOR_COMMODITIES_METALS,
    SECTOR_INDICES_ETFS,
    SECTOR_TRADFI_EQUITIES,
    SECTOR_CRYPTO_MAJORS,
    SECTOR_CRYPTO_ALTS_TOKENS
]

METALS_AND_COMMODITIES = {
    'PAXGUSD', 'XAUTUSD', 'SLVONUSD', 'OILUSD'
}

INDICES_AND_ETFS = {
    'SPXUSD', 'SPYXUSD', 'SPCXXUSD', 'QQQXUSD', 'TQQQBUSD', 'SOXLBUSD', 'EWYBUSD', 'KORUBUSD'
}

TRADFI_EQUITIES = {
    'AAOIBUSD', 'AAPLXUSD', 'AMDBUSD', 'AMZNXUSD', 'ARMBUSD', 'AVGOBUSD', 'BABABUSD',
    'BILLUSD', 'BMNRBUSD', 'CBRSBUSD', 'CHIPUSD', 'COINXUSD', 'CRCLBUSD', 'CRCLXUSD',
    'CRWDBUSD', 'DRAMBUSD', 'GOOGLXUSD', 'HIMSUSD', 'HOODBUSD', 'INTCBUSD', 'LABUSD',
    'LITEBUSD', 'METAXUSD', 'MRNABUSD', 'MRVLBUSD', 'MSFTBUSD', 'MSFTXUSD', 'MSTRBUSD',
    'MUBUSD', 'NBISBUSD', 'NFLXXUSD', 'NVDABUSD', 'NVDAXUSD', 'ORCLBUSD', 'PLTRBUSD',
    'RKLBBUSD', 'SKHYBUSD', 'SMCIUSD', 'SNDKBUSD', 'SNXXBUSD', 'TSLAXUSD', 'TSMBUSD', 'WDCBUSD'
}

CRYPTO_MAJORS = {
    'BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'BNBUSD', 'DOGEUSD', 'ADAUSD',
    'AVAXUSD', 'LINKUSD', 'SUIUSD', 'NEARUSD', 'TONUSD'
}

def classify_asset(symbol: str) -> str:
    """Classifies a Delta Exchange perpetual symbol into its institutional sector."""
    sym = symbol.upper().strip()
    
    if sym in METALS_AND_COMMODITIES:
        return SECTOR_COMMODITIES_METALS
    if sym in INDICES_AND_ETFS:
        return SECTOR_INDICES_ETFS
    if sym in TRADFI_EQUITIES:
        return SECTOR_TRADFI_EQUITIES
    if sym in CRYPTO_MAJORS:
        return SECTOR_CRYPTO_MAJORS
    
    return SECTOR_CRYPTO_ALTS_TOKENS

def get_sector_display_name(sector: str) -> str:
    mapping = {
        SECTOR_COMMODITIES_METALS: "Commodities & Metals",
        SECTOR_INDICES_ETFS: "Indices & ETFs",
        SECTOR_TRADFI_EQUITIES: "TradFi Equities & Synthetics",
        SECTOR_CRYPTO_MAJORS: "Crypto Blue-Chips",
        SECTOR_CRYPTO_ALTS_TOKENS: "Altcoins & DeFi Tokens"
    }
    return mapping.get(sector, sector)
