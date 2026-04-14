import { useCallback, useEffect, useRef, useState } from "react"

interface WebSocketMessage {
  type: "log" | "status" | "screenshot" | "complete" | "error"
  data: any
  timestamp?: string
}

interface UseWebSocketLogOptions {
  onMessage?: (message: WebSocketMessage) => void
  onLog?: (log: string) => void
  onStatus?: (status: string) => void
  onScreenshot?: (screenshot: string) => void
  onComplete?: (result: any) => void
  onError?: (error: string) => void
}

interface UseWebSocketLogReturn {
  isConnected: boolean
  hasError: boolean
  connect: () => void
  disconnect: () => void
  retryCount: number
}

const BASE_DELAY = 1000 // 1 second
const MAX_DELAY = 30000 // 30 seconds
const MAX_RETRIES = 10

export const useWebSocketLog = (
  testId: string | null,
  options: UseWebSocketLogOptions = {}
): UseWebSocketLogReturn => {
  const {
    onMessage,
    onLog,
    onStatus,
    onScreenshot,
    onComplete,
    onError,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)

  const getAuthToken = useCallback(() => {
    return localStorage.getItem("access_token") || ""
  }, [])

  const calculateDelay = useCallback((attempt: number) => {
    return Math.min(BASE_DELAY * Math.pow(2, attempt), MAX_DELAY)
  }, [])

  const connect = useCallback(() => {
    if (!testId || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const token = getAuthToken()
    if (!token) {
      console.error("[WebSocket] No auth token available")
      setHasError(true)
      return
    }

    const wsUrl = `${import.meta.env.VITE_API_URL?.replace("http", "ws") || "ws://localhost:8000"}/api/v1/ws/web-tests/${testId}?token=${token}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log("[WebSocket] Connected to test", testId)
        setIsConnected(true)
        setHasError(false)
        setRetryCount(0)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          // Call generic message handler
          if (onMessage) {
            onMessage(message)
          }

          // Call specific handlers based on message type
          switch (message.type) {
            case "log":
              if (onLog && message.data?.log) {
                onLog(message.data.log)
              }
              break
            case "status":
              if (onStatus && message.data?.status) {
                onStatus(message.data.status)
              }
              break
            case "screenshot":
              if (onScreenshot && message.data?.screenshot) {
                onScreenshot(message.data.screenshot)
              }
              break
            case "complete":
              if (onComplete) {
                onComplete(message.data)
              }
              break
            case "error":
              if (onError && message.data?.error) {
                onError(message.data.error)
              }
              setHasError(true)
              break
          }
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error)
        }
      }

      ws.onerror = (event) => {
        console.error("[WebSocket] Error:", event)
        setHasError(true)
      }

      ws.onclose = (event) => {
        console.log("[WebSocket] Connection closed:", event.code, event.reason)
        setIsConnected(false)
        wsRef.current = null

        // Attempt reconnection if not explicitly closed and under max retries
        if (shouldReconnectRef.current && retryCount < MAX_RETRIES) {
          const delay = calculateDelay(retryCount)
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`)

          retryTimeoutRef.current = setTimeout(() => {
            setRetryCount((prev) => prev + 1)
            connect()
          }, delay)
        } else if (retryCount >= MAX_RETRIES) {
          console.error("[WebSocket] Max retries reached. Stopping reconnection attempts.")
          setHasError(true)
        }
      }
    } catch (error) {
      console.error("[WebSocket] Failed to create connection:", error)
      setHasError(true)
    }
  }, [testId, getAuthToken, retryCount, calculateDelay, onMessage, onLog, onStatus, onScreenshot, onComplete, onError])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
    setRetryCount(0)
  }, [])

  // Connect when testId changes
  useEffect(() => {
    if (testId) {
      shouldReconnectRef.current = true
      connect()
    }

    return () => {
      disconnect()
    }
  }, [testId, connect, disconnect])

  return {
    isConnected,
    hasError,
    connect,
    disconnect,
    retryCount,
  }
}

export default useWebSocketLog
