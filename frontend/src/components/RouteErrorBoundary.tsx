'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  routeName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class RouteErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      `RouteErrorBoundary (${this.props.routeName || 'unknown'}) caught an error:`,
      error,
      errorInfo
    );

    // In production, send to error tracking service (Sentry)
    if (process.env.NEXT_PUBLIC_ENV === 'production') {
      // TODO: Sentry.captureException(error, {
      //   extra: { ...errorInfo, routeName: this.props.routeName },
      // });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-[50vh] p-6">
          <div className="max-w-md w-full bg-white rounded-lg border border-red-200 p-6">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-900">
                  Erreur de chargement
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  Impossible de charger cette section.
                </p>
              </div>
            </div>

            {process.env.NEXT_PUBLIC_ENV !== 'production' && this.state.error && (
              <div className="mt-4 p-3 bg-gray-50 rounded text-xs">
                <p className="font-mono text-red-600 font-semibold">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-4 w-full px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Réessayer
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
