'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  HomeIcon,
  CpuChipIcon,
  ChartBarIcon,
  BeakerIcon,
  Cog6ToothIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  children?: NavigationItem[];
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: HomeIcon,
  },
  {
    name: 'Analyse',
    href: '/analysis',
    icon: DocumentTextIcon,
  },
  {
    name: 'Modèles ML',
    href: '/ml',
    icon: CpuChipIcon,
    children: [
      {
        name: 'Paramétrage',
        href: '/ml/parameters',
        icon: Cog6ToothIcon,
      },
      {
        name: 'Comparaisons',
        href: '/ml/comparisons',
        icon: ChartBarIcon,
      },
      {
        name: 'Prédictions',
        href: '/ml/predictions',
        icon: BeakerIcon,
      },
    ],
  },
  {
    name: 'Screeners',
    href: '/screeners',
    icon: ChartBarIcon,
  },
  {
    name: 'Backtesting',
    href: '/backtesting',
    icon: BeakerIcon,
  },
];

export default function Navigation() {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Modèles ML']);

  const toggleExpanded = (itemName: string) => {
    setExpandedItems(prev => 
      prev.includes(itemName) 
        ? prev.filter(item => item !== itemName)
        : [...prev, itemName]
    );
  };

  const isActive = (href: string) => {
    if (href === '/ml') {
      return pathname.startsWith('/ml');
    }
    return pathname === href;
  };

  const isChildActive = (children: NavigationItem[]) => {
    return children.some(child => pathname === child.href);
  };

  return (
    <nav className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/dashboard" className="text-xl font-bold">
                AIMarkets
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => (
                <div key={item.name} className="relative">
                  {item.children ? (
                    <div>
                      <button
                        onClick={() => toggleExpanded(item.name)}
                        className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          isActive(item.href) || isChildActive(item.children)
                            ? 'bg-gray-800 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        <item.icon className="mr-2 h-5 w-5" />
                        {item.name}
                        {expandedItems.includes(item.name) ? (
                          <ChevronDownIcon className="ml-1 h-4 w-4" />
                        ) : (
                          <ChevronRightIcon className="ml-1 h-4 w-4" />
                        )}
                      </button>
                      
                      {expandedItems.includes(item.name) && (
                        <div className="absolute top-full left-0 mt-1 w-48 bg-gray-800 rounded-md shadow-lg z-50">
                          <div className="py-1">
                            {item.children.map((child) => (
                              <Link
                                key={child.name}
                                href={child.href}
                                className={`flex items-center px-4 py-2 text-sm transition-colors ${
                                  pathname === child.href
                                    ? 'bg-gray-700 text-white'
                                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                }`}
                              >
                                <child.icon className="mr-2 h-4 w-4" />
                                {child.name}
                              </Link>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <Link
                      href={item.href}
                      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive(item.href)
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      <item.icon className="mr-2 h-5 w-5" />
                      {item.name}
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className="sm:hidden">
        <div className="px-2 pt-2 pb-3 space-y-1">
          {navigation.map((item) => (
            <div key={item.name}>
              {item.children ? (
                <div>
                  <button
                    onClick={() => toggleExpanded(item.name)}
                    className={`flex items-center w-full px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive(item.href) || isChildActive(item.children)
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    <item.icon className="mr-2 h-5 w-5" />
                    {item.name}
                    {expandedItems.includes(item.name) ? (
                      <ChevronDownIcon className="ml-auto h-4 w-4" />
                    ) : (
                      <ChevronRightIcon className="ml-auto h-4 w-4" />
                    )}
                  </button>
                  
                  {expandedItems.includes(item.name) && (
                    <div className="ml-4 mt-1 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.name}
                          href={child.href}
                          className={`flex items-center px-3 py-2 rounded-md text-sm transition-colors ${
                            pathname === child.href
                              ? 'bg-gray-700 text-white'
                              : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                          }`}
                        >
                          <child.icon className="mr-2 h-4 w-4" />
                          {child.name}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <item.icon className="mr-2 h-5 w-5" />
                  {item.name}
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </nav>
  );
}
