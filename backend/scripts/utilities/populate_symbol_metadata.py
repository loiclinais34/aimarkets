#!/usr/bin/env python3
"""
Script pour peupler la table symbol_metadata avec les noms des entreprises
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import SymbolMetadata

# Dictionnaire des noms d'entreprises pour les symboles NASDAQ
SYMBOL_COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc. Class A",
    "GOOG": "Alphabet Inc. Class C",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.",
    "CRM": "Salesforce Inc.",
    "ORCL": "Oracle Corporation",
    "INTC": "Intel Corporation",
    "AMD": "Advanced Micro Devices Inc.",
    "QCOM": "QUALCOMM Incorporated",
    "TXN": "Texas Instruments Incorporated",
    "AVGO": "Broadcom Inc.",
    "CSCO": "Cisco Systems Inc.",
    "IBM": "International Business Machines Corporation",
    "NOW": "ServiceNow Inc.",
    "UBER": "Uber Technologies Inc.",
    "PYPL": "PayPal Holdings Inc.",
    "SHOP": "Shopify Inc.",
    "ZM": "Zoom Video Communications Inc.",
    "DOCU": "DocuSign Inc.",
    "SNOW": "Snowflake Inc.",
    "CRWD": "CrowdStrike Holdings Inc.",
    "OKTA": "Okta Inc.",
    "DDOG": "Datadog Inc.",
    "NET": "Cloudflare Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "ROKU": "Roku Inc.",
    "SPOT": "Spotify Technology S.A.",
    "SQ": "Block Inc.",
    "TWLO": "Twilio Inc.",
    "WDAY": "Workday Inc.",
    "VEEV": "Veeva Systems Inc.",
    "MDB": "MongoDB Inc.",
    "ESTC": "Elastic N.V.",
    "TEAM": "Atlassian Corporation",
    "ZS": "Zscaler Inc.",
    "PANW": "Palo Alto Networks Inc.",
    "FTNT": "Fortinet Inc.",
    "CHKP": "Check Point Software Technologies Ltd.",
    "CYBR": "CyberArk Software Ltd.",
    "OKTA": "Okta Inc.",
    "AKAM": "Akamai Technologies Inc.",
    "FFIV": "F5 Inc.",
    "JNPR": "Juniper Networks Inc.",
    "ANET": "Arista Networks Inc.",
    "NTAP": "NetApp Inc.",
    "WDC": "Western Digital Corporation",
    "STX": "Seagate Technology Holdings plc",
    "MU": "Micron Technology Inc.",
    "LRCX": "Lam Research Corporation",
    "AMAT": "Applied Materials Inc.",
    "KLAC": "KLA Corporation",
    "MCHP": "Microchip Technology Incorporated",
    "ADI": "Analog Devices Inc.",
    "MRVL": "Marvell Technology Inc.",
    "NXPI": "NXP Semiconductors N.V.",
    "ON": "ON Semiconductor Corporation",
    "SWKS": "Skyworks Solutions Inc.",
    "QRVO": "Qorvo Inc.",
    "TER": "Teradyne Inc.",
    "CDNS": "Cadence Design Systems Inc.",
    "SNPS": "Synopsys Inc.",
    "ANSS": "ANSYS Inc.",
    "KEYS": "Keysight Technologies Inc.",
    "FLT": "FleetCor Technologies Inc.",
    "GPN": "Global Payments Inc.",
    "FISV": "Fiserv Inc.",
    "FIS": "Fidelity National Information Services Inc.",
    "JKHY": "Jack Henry & Associates Inc.",
    "PAYX": "Paychex Inc.",
    "ADP": "Automatic Data Processing Inc.",
    "WU": "The Western Union Company",
    "V": "Visa Inc.",
    "MA": "Mastercard Incorporated",
    "AXP": "American Express Company",
    "COF": "Capital One Financial Corporation",
    "DFS": "Discover Financial Services",
    "SYF": "Synchrony Financial",
    "ALLY": "Ally Financial Inc.",
    "SOFI": "SoFi Technologies Inc.",
    "LC": "LendingClub Corporation",
    "UPST": "Upstart Holdings Inc.",
    "AFRM": "Affirm Holdings Inc.",
    "OPEN": "Opendoor Technologies Inc.",
    "Z": "Zillow Group Inc.",
    "RDFN": "Redfin Corporation",
    "COMP": "Compass Inc.",
    "EXPI": "eXp World Holdings Inc.",
    "REAL": "The RealReal Inc.",
    "PINS": "Pinterest Inc.",
    "SNAP": "Snap Inc.",
    "TWTR": "Twitter Inc.",
    "FB": "Meta Platforms Inc.",
    "DIS": "The Walt Disney Company",
    "NFLX": "Netflix Inc.",
    "CMCSA": "Comcast Corporation",
    "CHTR": "Charter Communications Inc.",
    "DISH": "DISH Network Corporation",
    "VZ": "Verizon Communications Inc.",
    "T": "AT&T Inc.",
    "TMUS": "T-Mobile US Inc.",
    "S": "Sprint Corporation",
    "LUMN": "Lumen Technologies Inc.",
    "CTL": "CenturyLink Inc.",
    "FANG": "Diamondback Energy Inc.",
    "ISRG": "Intuitive Surgical Inc.",
    "CCEP": "Coca-Cola Europacific Partners plc",
    "WBD": "Warner Bros. Discovery Inc.",
    "CSGP": "CoStar Group Inc.",
    "PYPL": "PayPal Holdings Inc.",
    "SHOP": "Shopify Inc.",
    "AXON": "Axon Enterprise Inc.",
    "LRCX": "Lam Research Corporation",
    "NFLX": "Netflix Inc.",
    "SBUX": "Starbucks Corporation",
    "ORLY": "O'Reilly Automotive Inc.",
    "CTAS": "Cintas Corporation",
    "BKNG": "Booking Holdings Inc.",
    "FAST": "Fastenal Company",
    "ARM": "Arm Holdings plc",
    "TMUS": "T-Mobile US Inc.",
    "EXC": "Exelon Corporation",
    "APP": "AppLovin Corporation",
    "GEHC": "GE HealthCare Technologies Inc.",
    "TEAM": "Atlassian Corporation",
    "CTSH": "Cognizant Technology Solutions Corporation",
    "GFS": "GLOBALFOUNDRIES Inc.",
    "COST": "Costco Wholesale Corporation",
    "VRSK": "Verisk Analytics Inc.",
    "BKR": "Baker Hughes Company",
    "TTD": "The Trade Desk Inc.",
    "IDXX": "IDEXX Laboratories Inc.",
    "AVGO": "Broadcom Inc.",
    "ADI": "Analog Devices Inc.",
    "MSTR": "MicroStrategy Incorporated",
    "KDP": "Keurig Dr Pepper Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "CDW": "CDW Corporation",
    "KHC": "The Kraft Heinz Company",
    "CSCO": "Cisco Systems Inc.",
    "ROP": "Roper Technologies Inc.",
    "VRTX": "Vertex Pharmaceuticals Incorporated",
    "PANW": "Palo Alto Networks Inc.",
    "MELI": "MercadoLibre Inc.",
    "ADSK": "Autodesk Inc.",
    "AMZN": "Amazon.com Inc.",
    "FTNT": "Fortinet Inc.",
    "TRI": "Thomson Reuters Corporation",
    "WDAY": "Workday Inc.",
    "PAYX": "Paychex Inc.",
    "ASML": "ASML Holding N.V.",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "CPRT": "Copart Inc.",
    "AEP": "American Electric Power Company Inc.",
    "AZN": "AstraZeneca PLC",
    "CDNS": "Cadence Design Systems Inc.",
    "AMAT": "Applied Materials Inc.",
    "LIN": "Linde plc",
    "MCHP": "Microchip Technology Incorporated",
    "CSX": "CSX Corporation",
    "HON": "Honeywell International Inc.",
    "GOOG": "Alphabet Inc. Class C",
    "REGN": "Regeneron Pharmaceuticals Inc.",
    "ADP": "Automatic Data Processing Inc.",
    "MAR": "Marriott International Inc.",
    "EA": "Electronic Arts Inc.",
    "MU": "Micron Technology Inc.",
    "DASH": "DoorDash Inc.",
    "ODFL": "Old Dominion Freight Line Inc.",
    "TTWO": "Take-Two Interactive Software Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "ADBE": "Adobe Inc.",
    "ABNB": "Airbnb Inc.",
    "CMCSA": "Comcast Corporation",
    "QCOM": "QUALCOMM Incorporated",
    "CHTR": "Charter Communications Inc.",
    "PCAR": "PACCAR Inc.",
    "ZS": "Zscaler Inc.",
    "SNPS": "Synopsys Inc.",
    "GILD": "Gilead Sciences Inc.",
    "AMGN": "Amgen Inc.",
    "MDLZ": "Mondelez International Inc.",
    "XEL": "Xcel Energy Inc.",
    "TXN": "Texas Instruments Incorporated",
    "MRVL": "Marvell Technology Inc.",
    "PEP": "PepsiCo Inc.",
    "DXCM": "DexCom Inc.",
    "INTU": "Intuit Inc.",
    "PDD": "PDD Holdings Inc.",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla Inc.",
    "LULU": "Lululemon Athletica Inc.",
    "BIIB": "Biogen Inc.",
    "INTC": "Intel Corporation",
    "GOOGL": "Alphabet Inc. Class A",
    "ROST": "Ross Stores Inc.",
    "KLAC": "KLA Corporation",
    "CRWD": "CrowdStrike Holdings Inc.",
    "DDOG": "Datadog Inc.",
    "MNST": "Monster Beverage Corporation",
    "ON": "ON Semiconductor Corporation",
    "CEG": "Constellation Energy Corporation"
}

# Dictionnaire des secteurs pour les symboles
SYMBOL_SECTORS = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "GOOG": "Technology",
    "AMZN": "Technology", "NVDA": "Technology", "META": "Technology", "NFLX": "Technology",
    "ADBE": "Technology", "CRM": "Technology", "ORCL": "Technology", "INTC": "Technology",
    "AMD": "Technology", "QCOM": "Technology", "TXN": "Technology", "AVGO": "Technology",
    "CSCO": "Technology", "IBM": "Technology", "NOW": "Technology", "UBER": "Technology",
    "PYPL": "Technology", "SHOP": "Technology", "ZM": "Technology", "DOCU": "Technology",
    "SNOW": "Technology", "CRWD": "Technology", "OKTA": "Technology", "DDOG": "Technology",
    "NET": "Technology", "PLTR": "Technology", "ROKU": "Technology", "SPOT": "Technology",
    "SQ": "Technology", "TWLO": "Technology", "WDAY": "Technology", "VEEV": "Technology",
    "MDB": "Technology", "ESTC": "Technology", "TEAM": "Technology", "ZS": "Technology",
    "PANW": "Technology", "FTNT": "Technology", "CHKP": "Technology", "CYBR": "Technology",
    "AKAM": "Technology", "FFIV": "Technology", "JNPR": "Technology", "ANET": "Technology",
    "NTAP": "Technology", "WDC": "Technology", "STX": "Technology", "MU": "Technology",
    "LRCX": "Technology", "AMAT": "Technology", "KLAC": "Technology", "MCHP": "Technology",
    "ADI": "Technology", "MRVL": "Technology", "NXPI": "Technology", "ON": "Technology",
    "SWKS": "Technology", "QRVO": "Technology", "TER": "Technology", "CDNS": "Technology",
    "SNPS": "Technology", "ANSS": "Technology", "KEYS": "Technology", "ARM": "Technology",
    "GFS": "Technology", "ASML": "Technology", "CDW": "Technology", "ADSK": "Technology",
    "TRI": "Technology", "INTU": "Technology", "PDD": "Technology",
    
    # Healthcare
    "ISRG": "Healthcare", "VRTX": "Healthcare", "GILD": "Healthcare", "AMGN": "Healthcare",
    "BIIB": "Healthcare", "REGN": "Healthcare", "DXCM": "Healthcare", "IDXX": "Healthcare",
    
    # Consumer Discretionary
    "TSLA": "Consumer Discretionary", "AMZN": "Consumer Discretionary", "NFLX": "Consumer Discretionary",
    "SBUX": "Consumer Discretionary", "BKNG": "Consumer Discretionary", "COST": "Consumer Discretionary",
    "LULU": "Consumer Discretionary", "ROST": "Consumer Discretionary", "ABNB": "Consumer Discretionary",
    "DASH": "Consumer Discretionary", "EA": "Consumer Discretionary", "TTWO": "Consumer Discretionary",
    "MAR": "Consumer Discretionary", "WBD": "Consumer Discretionary", "DIS": "Consumer Discretionary",
    "PINS": "Consumer Discretionary", "SNAP": "Consumer Discretionary", "TWTR": "Consumer Discretionary",
    "FB": "Consumer Discretionary", "ROKU": "Consumer Discretionary", "SPOT": "Consumer Discretionary",
    "SHOP": "Consumer Discretionary", "SQ": "Consumer Discretionary", "UBER": "Consumer Discretionary",
    "OPEN": "Consumer Discretionary", "Z": "Consumer Discretionary", "RDFN": "Consumer Discretionary",
    "COMP": "Consumer Discretionary", "EXPI": "Consumer Discretionary", "REAL": "Consumer Discretionary",
    
    # Consumer Staples
    "KDP": "Consumer Staples", "KHC": "Consumer Staples", "PEP": "Consumer Staples", "MNST": "Consumer Staples",
    "MDLZ": "Consumer Staples", "COST": "Consumer Staples",
    
    # Financials
    "V": "Financials", "MA": "Financials", "AXP": "Financials", "COF": "Financials", "DFS": "Financials",
    "SYF": "Financials", "ALLY": "Financials", "SOFI": "Financials", "LC": "Financials", "UPST": "Financials",
    "AFRM": "Financials", "FLT": "Financials", "GPN": "Financials", "FISV": "Financials", "FIS": "Financials",
    "JKHY": "Financials", "PAYX": "Financials", "ADP": "Financials", "WU": "Financials",
    
    # Communication Services
    "GOOGL": "Communication Services", "GOOG": "Communication Services", "META": "Communication Services",
    "NFLX": "Communication Services", "DIS": "Communication Services", "CMCSA": "Communication Services",
    "CHTR": "Communication Services", "DISH": "Communication Services", "VZ": "Communication Services",
    "T": "Communication Services", "TMUS": "Communication Services", "S": "Communication Services",
    "LUMN": "Communication Services", "CTL": "Communication Services", "WBD": "Communication Services",
    
    # Industrials
    "HON": "Industrials", "CSX": "Industrials", "ODFL": "Industrials", "PCAR": "Industrials",
    "CTAS": "Industrials", "FAST": "Industrials", "CPRT": "Industrials", "LIN": "Industrials",
    "BKR": "Industrials", "ROP": "Industrials", "TRI": "Industrials", "WDAY": "Industrials",
    
    # Energy
    "FANG": "Energy", "EXC": "Energy", "CEG": "Energy",
    
    # Utilities
    "AEP": "Utilities", "XEL": "Utilities", "EXC": "Utilities",
    
    # Materials
    "LIN": "Materials",
    
    # Real Estate
    "CSGP": "Real Estate", "OPEN": "Real Estate", "Z": "Real Estate", "RDFN": "Real Estate",
    "COMP": "Real Estate", "EXPI": "Real Estate", "REAL": "Real Estate",
    
    # Others
    "ORLY": "Consumer Discretionary", "CTSH": "Technology", "VRSK": "Technology", "TTD": "Technology",
    "MELI": "Consumer Discretionary", "AZN": "Healthcare", "MSTR": "Technology", "PLTR": "Technology",
    "APP": "Technology", "GEHC": "Healthcare", "GFS": "Technology", "COST": "Consumer Staples",
    "BKR": "Energy", "IDXX": "Healthcare", "AVGO": "Technology", "ADI": "Technology",
    "MSTR": "Technology", "KDP": "Consumer Staples", "PLTR": "Technology", "CDW": "Technology",
    "KHC": "Consumer Staples", "CSCO": "Technology", "ROP": "Industrials", "VRTX": "Healthcare",
    "PANW": "Technology", "MELI": "Consumer Discretionary", "ADSK": "Technology", "AMZN": "Consumer Discretionary",
    "FTNT": "Technology", "TRI": "Industrials", "WDAY": "Technology", "PAYX": "Financials",
    "ASML": "Technology", "AAPL": "Technology", "MSFT": "Technology", "CPRT": "Industrials",
    "AEP": "Utilities", "AZN": "Healthcare", "CDNS": "Technology", "AMAT": "Technology",
    "LIN": "Materials", "MCHP": "Technology", "CSX": "Industrials", "HON": "Industrials",
    "GOOG": "Communication Services", "REGN": "Healthcare", "ADP": "Financials", "MAR": "Consumer Discretionary",
    "EA": "Communication Services", "MU": "Technology", "DASH": "Consumer Discretionary",
    "ODFL": "Industrials", "TTWO": "Communication Services", "AMD": "Technology", "ADBE": "Technology",
    "ABNB": "Consumer Discretionary", "CMCSA": "Communication Services", "QCOM": "Technology",
    "CHTR": "Communication Services", "PCAR": "Industrials", "ZS": "Technology", "SNPS": "Technology",
    "GILD": "Healthcare", "AMGN": "Healthcare", "MDLZ": "Consumer Staples", "XEL": "Utilities",
    "TXN": "Technology", "MRVL": "Technology", "PEP": "Consumer Staples", "DXCM": "Healthcare",
    "INTU": "Technology", "PDD": "Consumer Discretionary", "NVDA": "Technology", "TSLA": "Consumer Discretionary",
    "LULU": "Consumer Discretionary", "BIIB": "Healthcare", "INTC": "Technology", "GOOGL": "Communication Services",
    "ROST": "Consumer Discretionary", "KLAC": "Technology", "CRWD": "Technology", "DDOG": "Technology",
    "MNST": "Consumer Staples", "ON": "Technology", "CEG": "Utilities"
}

def populate_symbol_metadata():
    """Peuple la table symbol_metadata avec les données des symboles"""
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        print("🚀 Début du peuplement de la table symbol_metadata...")
        
        # Récupérer tous les symboles uniques de historical_data
        from app.models.database import HistoricalData
        symbols_in_db = db.query(HistoricalData.symbol).distinct().all()
        symbols_list = [symbol[0] for symbol in symbols_in_db]
        
        print(f"📊 {len(symbols_list)} symboles trouvés dans historical_data")
        
        # Insérer les métadonnées pour chaque symbole
        inserted_count = 0
        updated_count = 0
        
        for symbol in symbols_list:
            # Vérifier si le symbole existe déjà
            existing_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == symbol).first()
            
            if existing_metadata:
                # Mettre à jour les informations existantes
                existing_metadata.company_name = SYMBOL_COMPANY_NAMES.get(symbol, f"{symbol} Corporation")
                existing_metadata.sector = SYMBOL_SECTORS.get(symbol, "Unknown")
                existing_metadata.industry = "Technology" if SYMBOL_SECTORS.get(symbol) == "Technology" else "Other"
                existing_metadata.market_cap_category = "Large Cap"  # Par défaut
                existing_metadata.is_active = True
                updated_count += 1
                print(f"✅ Mis à jour: {symbol} - {existing_metadata.company_name}")
            else:
                # Créer une nouvelle entrée
                new_metadata = SymbolMetadata(
                    symbol=symbol,
                    company_name=SYMBOL_COMPANY_NAMES.get(symbol, f"{symbol} Corporation"),
                    sector=SYMBOL_SECTORS.get(symbol, "Unknown"),
                    industry="Technology" if SYMBOL_SECTORS.get(symbol) == "Technology" else "Other",
                    market_cap_category="Large Cap",  # Par défaut
                    is_active=True
                )
                db.add(new_metadata)
                inserted_count += 1
                print(f"➕ Ajouté: {symbol} - {new_metadata.company_name}")
        
        # Valider les changements
        db.commit()
        
        print(f"\n🎉 Peuplement terminé avec succès!")
        print(f"📈 {inserted_count} nouveaux symboles ajoutés")
        print(f"🔄 {updated_count} symboles mis à jour")
        print(f"📊 Total: {inserted_count + updated_count} symboles traités")
        
        # Afficher quelques exemples
        print(f"\n📋 Exemples de métadonnées créées:")
        sample_metadata = db.query(SymbolMetadata).limit(5).all()
        for metadata in sample_metadata:
            print(f"   {metadata.symbol}: {metadata.company_name} ({metadata.sector})")
            
    except Exception as e:
        print(f"❌ Erreur lors du peuplement: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_symbol_metadata()
