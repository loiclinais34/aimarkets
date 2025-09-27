#!/usr/bin/env python3
"""
Test des nouveaux indicateurs de momentum dans les signaux avancés.
"""

import sys
sys.path.append('.')
import requests
import json

def test_advanced_signals():
    """Test des signaux avancés avec les nouveaux indicateurs."""
    
    print('🧪 Test des nouveaux indicateurs de momentum dans les signaux avancés')
    print('=' * 70)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        print(f'\n📊 Test pour {symbol}:')
        print('-' * 40)
        
        try:
            response = requests.get(f'http://localhost:8000/api/v1/advanced-signals/generate/{symbol}')
            
            if response.status_code == 200:
                data = response.json()
                
                print(f'   Type: {data["signal_type"]}')
                print(f'   Score: {data["score"]:.2f}')
                print(f'   Confiance: {data["confidence"]:.2f}')
                print(f'   Force: {data["strength"]:.2f}')
                
                print(f'   Indicateurs utilisés ({len(data["indicators_used"])}):')
                for indicator in data['indicators_used']:
                    print(f'     - {indicator}')
                
                print(f'   Signaux individuels:')
                for signal in data['individual_signals']:
                    weight = signal.get('weight', 'N/A')
                    print(f'     {signal["indicator"]:<15} | {signal["signal"]:<5} | Score: {signal["score"]:.1f} | Force: {signal["strength"]:.2f} | Poids: {weight}')
                
            else:
                print(f'   ❌ Erreur HTTP {response.status_code}: {response.text}')
                
        except Exception as e:
            print(f'   ❌ Erreur: {e}')

if __name__ == '__main__':
    test_advanced_signals()
