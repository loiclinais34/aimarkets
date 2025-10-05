#!/usr/bin/env python3
"""
Script pour générer plus d'indicateurs techniques et de sentiment
pour permettre l'entraînement ML
"""
import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def generate_indicators_for_symbol(symbol: str):
    """Générer les indicateurs pour un symbole"""
    print(f"🔄 Génération des indicateurs pour {symbol}...")
    
    try:
        # Récupérer les données historiques
        response = requests.get(f"{BASE_URL}/data/historical/{symbol}")
        response.raise_for_status()
        historical_data = response.json()
        
        if len(historical_data) < 30:
            print(f"⚠️ {symbol}: Pas assez de données historiques ({len(historical_data)} < 30)")
            return False
        
        print(f"📊 {symbol}: {len(historical_data)} enregistrements historiques")
        
        # Générer les indicateurs techniques
        print(f"🔧 Génération des indicateurs techniques pour {symbol}...")
        tech_response = requests.post(f"{BASE_URL}/data/generate-technical/{symbol}")
        if tech_response.status_code == 200:
            print(f"✅ {symbol}: Indicateurs techniques générés")
        else:
            print(f"❌ {symbol}: Erreur génération indicateurs techniques - {tech_response.status_code}")
        
        # Générer les indicateurs de sentiment
        print(f"📈 Génération des indicateurs de sentiment pour {symbol}...")
        sentiment_response = requests.post(f"{BASE_URL}/data/generate-sentiment/{symbol}")
        if sentiment_response.status_code == 200:
            print(f"✅ {symbol}: Indicateurs de sentiment générés")
        else:
            print(f"❌ {symbol}: Erreur génération indicateurs de sentiment - {sentiment_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ {symbol}: Erreur - {e}")
        return False

def generate_indicators_for_multiple_symbols(symbols: list):
    """Générer les indicateurs pour plusieurs symboles"""
    print(f"🚀 Génération des indicateurs pour {len(symbols)} symboles...")
    
    successful = 0
    for i, symbol in enumerate(symbols):
        print(f"\n📊 Progression: {i+1}/{len(symbols)}")
        if generate_indicators_for_symbol(symbol):
            successful += 1
        time.sleep(1)  # Pause entre les symboles
    
    print(f"\n🎉 Génération terminée: {successful}/{len(symbols)} symboles traités avec succès")
    return successful

def main():
    """Fonction principale"""
    print("🚀 Script de génération d'indicateurs pour ML")
    
    # Récupérer la liste des symboles
    try:
        response = requests.get(f"{BASE_URL}/data/symbols")
        response.raise_for_status()
        symbols_data = response.json()
        symbols = [s["symbol"] for s in symbols_data[:10]]  # Limiter à 10 symboles pour le test
        print(f"📊 {len(symbols)} symboles à traiter: {', '.join(symbols)}")
        
        # Générer les indicateurs
        successful = generate_indicators_for_multiple_symbols(symbols)
        
        print(f"\n✅ Script terminé: {successful} symboles traités avec succès")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
