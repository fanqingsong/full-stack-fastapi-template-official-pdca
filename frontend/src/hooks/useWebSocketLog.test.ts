import { renderHook, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

import useWebSocketLog from "./useWebSocketLog"

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null

  constructor(url: string) {
    this.url = url
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event("open"))
      }
    }, 0)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error("WebSocket is not open")
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent("close"))
    }
  }

  // Helper method to simulate receiving a message
  simulateMessage(data: string) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent("message", { data }))
    }
  }

  // Helper method to simulate connection error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event("error"))
    }
  }

  // Helper method to simulate connection close
  simulateClose(code: number, reason: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent("close", { code, reason }))
    }
  }
}

describe("useWebSocketLog", () => {
  beforeEach(() => {
    // Set global WebSocket mock
    global.WebSocket = MockWebSocket as any
    // Mock localStorage
    localStorage.setItem("access_token", "test-token")
    // Mock environment variable
    import.meta.env.VITE_API_URL = "http://localhost:8000"
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("should connect to WebSocket when testId is provided", async () => {
    const { result } = renderHook(() => useWebSocketLog("test-123"))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it("should not connect when testId is null", () => {
    const { result } = renderHook(() => useWebSocketLog(null))

    expect(result.current.isConnected).toBe(false)
  })

  it("should handle log messages", async () => {
    const onLog = vi.fn()
    const { result } = renderHook(() =>
      useWebSocketLog("test-123", { onLog })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    // Simulate receiving a log message
    const ws = (result.current as any).wsRef.current
    ws.simulateMessage(
      JSON.stringify({
        type: "log",
        data: { log: "Test log message" },
      })
    )

    await waitFor(() => {
      expect(onLog).toHaveBeenCalledWith("Test log message")
    })
  })

  it("should handle status messages", async () => {
    const onStatus = vi.fn()
    const { result } = renderHook(() =>
      useWebSocketLog("test-123", { onStatus })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current
    ws.simulateMessage(
      JSON.stringify({
        type: "status",
        data: { status: "running" },
      })
    )

    await waitFor(() => {
      expect(onStatus).toHaveBeenCalledWith("running")
    })
  })

  it("should handle complete messages", async () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useWebSocketLog("test-123", { onComplete })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current
    const completeData = { success: true, result: "test passed" }
    ws.simulateMessage(
      JSON.stringify({
        type: "complete",
        data: completeData,
      })
    )

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith(completeData)
    })
  })

  it("should handle error messages", async () => {
    const onError = vi.fn()
    const { result } = renderHook(() =>
      useWebSocketLog("test-123", { onError })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current
    ws.simulateMessage(
      JSON.stringify({
        type: "error",
        data: { error: "Test failed" },
      })
    )

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith("Test failed")
      expect(result.current.hasError).toBe(true)
    })
  })

  it("should disconnect when disconnect is called", async () => {
    const { result } = renderHook(() => useWebSocketLog("test-123"))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    result.current.disconnect()

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false)
    })
  })

  it("should reconnect on disconnect with exponential backoff", async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useWebSocketLog("test-123"))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current
    const initialRetryCount = result.current.retryCount

    // Simulate unexpected close
    ws.simulateClose(1006, "Connection lost")

    // Fast forward past the first retry delay
    vi.advanceTimersByTime(1000)

    await waitFor(() => {
      expect(result.current.retryCount).toBe(initialRetryCount + 1)
    })

    vi.useRealTimers()
  })

  it("should stop reconnecting after MAX_RETRIES", async () => {
    vi.useFakeTimers()

    const MAX_RETRIES = 10
    const { result } = renderHook(() => useWebSocketLog("test-123"))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current

    // Simulate multiple disconnects
    for (let i = 0; i < MAX_RETRIES + 2; i++) {
      ws.simulateClose(1006, "Connection lost")
      vi.advanceTimersByTime(30000) // Max delay
    }

    await waitFor(() => {
      expect(result.current.retryCount).toBe(MAX_RETRIES)
      expect(result.current.hasError).toBe(true)
    })

    vi.useRealTimers()
  })

  it("should call onMessage for all message types", async () => {
    const onMessage = vi.fn()
    const { result } = renderHook(() =>
      useWebSocketLog("test-123", { onMessage })
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const ws = (result.current as any).wsRef.current

    const messages = [
      { type: "log", data: { log: "test" } },
      { type: "status", data: { status: "running" } },
      { type: "complete", data: { success: true } },
    ]

    for (const msg of messages) {
      ws.simulateMessage(JSON.stringify(msg))
    }

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledTimes(messages.length)
    })
  })

  it("should cleanup on unmount", async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocketLog("test-123")
    )

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    unmount()

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false)
    })
  })
})
