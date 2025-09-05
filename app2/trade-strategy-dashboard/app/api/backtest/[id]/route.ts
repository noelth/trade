import { NextResponse } from "next/server"

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765"

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id
    
    // Forward the request to our FastAPI backend
    const response = await fetch(`${API_URL}/backtest/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || "Failed to fetch backtest")
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching backtest:", error)
    return NextResponse.json(
      { error: error.message || "An error occurred" },
      { status: 500 }
    )
  }
}