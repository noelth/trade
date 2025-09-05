import { NextResponse } from "next/server"

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    // Forward the request to our FastAPI backend
    const response = await fetch(`${API_URL}/backtest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || "Failed to create backtest")
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error creating backtest:", error)
    return NextResponse.json(
      { error: error.message || "An error occurred" },
      { status: 500 }
    )
  }
}