import Link from "next/link"

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen p-4 md:p-24 space-y-6">
      <h1 className="text-4xl font-bold tracking-tight">
        Trading Strategy Dashboard
      </h1>
      <p className="text-xl text-muted-foreground max-w-2xl text-center">
        Backtest trading strategies using candlestick patterns and technical indicators.
      </p>
      <div className="flex gap-4">
        <Link 
          href="/backtest" 
          className="px-6 py-3 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
        >
          Start Backtesting
        </Link>
      </div>
    </main>
  )
}