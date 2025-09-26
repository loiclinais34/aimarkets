'use client';

import React, { useState, useEffect } from 'react';

export default function CartDebug() {
  const [cartContent, setCartContent] = useState<string>('');

  useEffect(() => {
    const updateCartContent = () => {
      const cart = localStorage.getItem('opportunity-cart');
      setCartContent(cart || 'Panier vide');
    };

    updateCartContent();

    // Écouter les changements
    const handleCartUpdate = () => {
      updateCartContent();
    };

    window.addEventListener('cartUpdated', handleCartUpdate);
    window.addEventListener('storage', handleCartUpdate);

    return () => {
      window.removeEventListener('cartUpdated', handleCartUpdate);
      window.removeEventListener('storage', handleCartUpdate);
    };
  }, []);

  const clearCart = () => {
    localStorage.removeItem('opportunity-cart');
    setCartContent('Panier vidé');
    window.dispatchEvent(new CustomEvent('cartUpdated'));
  };

  const addTestItem = () => {
    const testItem = {
      symbol: 'TEST',
      company_name: 'Test Company',
      prediction: 1.0,
      confidence: 0.95,
      model_id: 9999,
      model_name: 'test_model',
      target_return: 5.0,
      time_horizon: 30,
      rank: 1,
      prediction_date: '2025-01-01',
      screener_run_id: 1
    };

    const existingCart = localStorage.getItem('opportunity-cart');
    let cart = existingCart ? JSON.parse(existingCart) : [];
    cart.push(testItem);
    localStorage.setItem('opportunity-cart', JSON.stringify(cart));
    setCartContent(JSON.stringify(cart, null, 2));
    window.dispatchEvent(new CustomEvent('cartUpdated'));
  };

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-black bg-opacity-80 text-white p-4 rounded-lg text-xs max-w-md max-h-64 overflow-auto z-50">
      <div className="font-bold mb-2">🐛 Cart Debug</div>
      <div className="mb-2">
        <strong>Contenu localStorage:</strong>
        <pre className="text-xs mt-1 whitespace-pre-wrap">{cartContent}</pre>
      </div>
      <div className="flex space-x-2">
        <button
          onClick={addTestItem}
          className="px-2 py-1 bg-blue-600 rounded text-xs"
        >
          + Test
        </button>
        <button
          onClick={clearCart}
          className="px-2 py-1 bg-red-600 rounded text-xs"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
