"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import Image from "next/image"

// This would be from shadcn/ui components in a real implementation
const Card = ({ children, className = "", ...props }) => (
  <div className={`rounded-lg border bg-card p-6 shadow-sm ${className}`} {...props}>
    {children}
  </div>
)

export default function BacktestResultPage({ params }) {
  const { id } = params
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    const fetchResult = async () => {
      try {
        const response = await fetch(`/api/backtest/${id}`)
        if (!response.ok) {
          throw new Error("Failed to fetch backtest result")
        }
        const data = await response.json()
        setResult(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    
    fetchResult()
    
    // Poll for updates if status is pending or running
    const interval = setInterval(async () => {
      if (result && (result.status === "pending" || result.status === "running")) {
        fetchResult()
      } else {
        clearInterval(interval)
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [id, result?.status])
  
  if (loading) {
    return (
      <div className="container mx-auto p-8 text-center">
        <div className="animate-pulse text-2xl">Loading backtest results...</div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="container mx-auto p-8">
        <div className="text-destructive text-xl">Error: {error}</div>
        <Link href="/backtest" className="mt-4 inline-block px-4 py-2 bg-secondary text-secondary-foreground rounded-md">
          Back to Backtest Form
        </Link>
      </div>
    )
  }
  
  if (!result) {
    return (
      <div className="container mx-auto p-8">
        <div className="text-xl">Backtest not found</div>
        <Link href="/backtest" className="mt-4 inline-block px-4 py-2 bg-secondary text-secondary-foreground rounded-md">
          Back to Backtest Form
        </Link>
      </div>
    )
  }
  
  // Format patterns list for display
  const formatPatterns = (patterns) => {
    if (!patterns) return "N/A"
    return patterns.map(pattern => 
      pattern.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    ).join(', ')
  }
  
  return (
    <div className="container mx-auto p-4 md:p-8 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">
          Backtest Results: {result.ticker}
        </h1>
        <div className="space-x-2">
          <Link href="/backtest" className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md">
            New Backtest
          </Link>
        </div>
      </div>
      
      {result.status === "pending" || result.status === "running" ? (
        <Card className="mb-8">
          <div className="flex flex-col items-center justify-center py-12">
            <div className="text-2xl font-semibold mb-4">
              {result.status === "pending" ? "Waiting to start..." : "Running backtest..."}
            </div>
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <div className="mt-4 text-muted-foreground">
              This may take a few minutes depending on the date range and selected patterns.
            </div>
          </div>
        </Card>
      ) : result.status === "failed" ? (
        <Card className="mb-8 border-destructive">
          <div className="text-center py-8">
            <div className="text-2xl font-semibold text-destructive mb-4">
              Backtest Failed
            </div>
            <div className="text-muted-foreground mb-4">
              {result.error || "An unknown error occurred while running the backtest."}
            </div>
          </div>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <Card>
              <h2 className="text-xl font-semibold mb-4">Performance Summary</h2>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Initial Capital</span>
                  <span className="font-medium">${result.strategy_params.principal || 10000}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Final Value</span>
                  <span className="font-medium">${result.final_portfolio_value?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Return</span>
                  <span className={`font-medium ${result.total_return > 0 ? 'text-[hsl(var(--up-color))]' : 'text-[hsl(var(--down-color))]'}`}>
                    {result.total_return?.toFixed(2) || "N/A"}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Trades</span>
                  <span className="font-medium">{result.num_trades || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Profitable Trades</span>
                  <span className="font-medium text-[hsl(var(--up-color))]">{result.num_profitable_trades || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Win Rate</span>
                  <span className="font-medium">
                    {result.num_trades ? ((result.num_profitable_trades / result.num_trades) * 100).toFixed(2) : "N/A"}%
                  </span>
                </div>
              </div>
            </Card>
            
            <Card>
              <h2 className="text-xl font-semibold mb-4">Backtest Configuration</h2>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Ticker</span>
                  <span className="font-medium">{result.ticker}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Date Range</span>
                  <span className="font-medium">{result.start_date} to {result.end_date}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Strategy</span>
                  <span className="font-medium">Candlestick Patterns</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Patterns</span>
                  <span className="font-medium">{formatPatterns(result.strategy_params.patterns)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Stop Loss</span>
                  <span className="font-medium">{(result.strategy_params.stop_loss * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Take Profit</span>
                  <span className="font-medium">{(result.strategy_params.take_profit * 100).toFixed(2)}%</span>
                </div>
              </div>
            </Card>
          </div>
          
          {result.chart_path && (
            <Card className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Performance Chart</h2>
              <div className="relative h-[500px] w-full">
                <Image 
                  src={`/${result.chart_path}`} 
                  alt="Backtest performance chart" 
                  fill
                  className="object-contain"
                />
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}