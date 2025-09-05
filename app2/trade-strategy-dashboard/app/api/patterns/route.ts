import { NextResponse } from "next/server"

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765"

export async function GET() {
  try {
    // Forward the request to our FastAPI backend
    const response = await fetch(`${API_URL}/available-patterns`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || "Failed to fetch available patterns")
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching patterns:", error)
    return NextResponse.json(
      { error: error.message || "An error occurred" },
      { status: 500 }
    )
  }
}