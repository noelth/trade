"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

// This would be from shadcn/ui components in a real implementation
const Card = ({ children, className = "", ...props }) => (
  <div className={`rounded-lg border bg-card p-6 shadow-sm ${className}`} {...props}>
    {children}
  </div>
)

export default function BacktestPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  
  const [formData, setFormData] = useState({
    ticker: "AAPL",
    startDate: "2022-01-01",
    endDate: "2023-01-01",
    timeframe: "1d",
    principal: 10000,
    commission: 0.0003,
    patterns: ["engulfing", "doji", "hammer"],
    stopLoss: 0.05,
    takeProfit: 0.10,
  })
  
  const handleChange = (e) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === "number" ? parseFloat(value) : value
    }))
  }
  
  const handleMultiSelectChange = (e) => {
    const options = e.target.options
    const selected = []
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selected.push(options[i].value)
      }
    }
    setFormData(prev => ({
      ...prev,
      patterns: selected
    }))
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      // Format data for API
      const backtestData = {
        ticker: formData.ticker,
        start_date: formData.startDate,
        end_date: formData.endDate,
        timeframe: formData.timeframe,
        principal: formData.principal,
        commission: formData.commission,
        strategy_type: "candlestick",
        strategy_params: {
          patterns: formData.patterns,
          pattern_params: {},
          stop_loss: formData.stopLoss,
          take_profit: formData.takeProfit,
          consecutive_bars: 1,
          exit_on_opposite: true
        }
      }
      
      // Call API
      const response = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(backtestData)
      })
      
      const result = await response.json()
      
      if (response.ok) {
        // Navigate to results page
        router.push(`/backtest/${result.id}`)
      } else {
        console.error("Error starting backtest:", result)
        alert("Error starting backtest. See console for details.")
      }
    } catch (error) {
      console.error("Error submitting form:", error)
      alert("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="container mx-auto p-4 md:p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Create Backtest</h1>
      
      <form onSubmit={handleSubmit} className="space-y-8">
        <Card>
          <h2 className="text-xl font-semibold mb-4">Market Data</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="ticker" className="block font-medium">Ticker Symbol</label>
              <input
                type="text"
                id="ticker"
                name="ticker"
                value={formData.ticker}
                onChange={handleChange}
                required
                className="w-full p-2 rounded-md border bg-background"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="timeframe" className="block font-medium">Timeframe</label>
              <select
                id="timeframe"
                name="timeframe"
                value={formData.timeframe}
                onChange={handleChange}
                className="w-full p-2 rounded-md border bg-background"
              >
                <option value="1d">Daily</option>
                <option value="1h">Hourly</option>
                <option value="15m">15 Minutes</option>
                <option value="5m">5 Minutes</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="startDate" className="block font-medium">Start Date</label>
              <input
                type="date"
                id="startDate"
                name="startDate"
                value={formData.startDate}
                onChange={handleChange}
                required
                className="w-full p-2 rounded-md border bg-background"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="endDate" className="block font-medium">End Date</label>
              <input
                type="date"
                id="endDate"
                name="endDate"
                value={formData.endDate}
                onChange={handleChange}
                required
                className="w-full p-2 rounded-md border bg-background"
              />
            </div>
          </div>
        </Card>
        
        <Card>
          <h2 className="text-xl font-semibold mb-4">Trading Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="principal" className="block font-medium">Initial Capital</label>
              <input
                type="number"
                id="principal"
                name="principal"
                value={formData.principal}
                onChange={handleChange}
                min="1000"
                step="1000"
                className="w-full p-2 rounded-md border bg-background"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="commission" className="block font-medium">Commission (0.0003 = 0.03%)</label>
              <input
                type="number"
                id="commission"
                name="commission"
                value={formData.commission}
                onChange={handleChange}
                min="0"
                max="0.01"
                step="0.0001"
                className="w-full p-2 rounded-md border bg-background"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="stopLoss" className="block font-medium">Stop Loss (%)</label>
              <input
                type="number"
                id="stopLoss"
                name="stopLoss"
                value={formData.stopLoss}
                onChange={handleChange}
                min="0.01"
                max="0.5"
                step="0.01"
                className="w-full p-2 rounded-md border bg-background"
              />
              <div className="text-xs text-muted-foreground">Example: 0.05 means 5% stop loss</div>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="takeProfit" className="block font-medium">Take Profit (%)</label>
              <input
                type="number"
                id="takeProfit"
                name="takeProfit"
                value={formData.takeProfit}
                onChange={handleChange}
                min="0.01"
                max="1"
                step="0.01"
                className="w-full p-2 rounded-md border bg-background"
              />
              <div className="text-xs text-muted-foreground">Example: 0.1 means 10% take profit</div>
            </div>
          </div>
        </Card>
        
        <Card>
          <h2 className="text-xl font-semibold mb-4">Candlestick Patterns</h2>
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="patterns" className="block font-medium">Select Patterns (hold Ctrl/Cmd to select multiple)</label>
              <select
                id="patterns"
                name="patterns"
                multiple
                value={formData.patterns}
                onChange={handleMultiSelectChange}
                className="w-full p-2 rounded-md border bg-background h-48"
              >
                <option value="doji">Doji</option>
                <option value="hammer">Hammer</option>
                <option value="shooting_star">Shooting Star</option>
                <option value="engulfing">Engulfing</option>
                <option value="morning_star">Morning Star</option>
                <option value="evening_star">Evening Star</option>
                <option value="three_white_soldiers">Three White Soldiers</option>
                <option value="three_black_crows">Three Black Crows</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {formData.patterns.map(pattern => (
                <div key={pattern} className="p-3 rounded-md bg-secondary text-secondary-foreground inline-block">
                  {pattern.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </div>
              ))}
            </div>
          </div>
        </Card>
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className={`px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/80 transition-colors ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Running Backtest...' : 'Run Backtest'}
          </button>
        </div>
      </form>
    </div>
  )
}