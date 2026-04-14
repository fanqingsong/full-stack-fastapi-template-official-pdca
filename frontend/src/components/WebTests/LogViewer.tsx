import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Scroll } from "lucide-react"
import { cn } from "@/lib/utils"

interface LogViewerProps {
  logs: string[]
  isLoading?: boolean
  className?: string
}

export default function LogViewer({ logs, isLoading = false, className }: LogViewerProps) {
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const getLogColor = (log: string): string => {
    const lowerLog = log.toLowerCase()

    if (lowerLog.includes("[result]:") || lowerLog.includes("result:")) {
      if (lowerLog.includes("pass") || lowerLog.includes("success")) {
        return "text-green-400"
      }
      if (lowerLog.includes("fail") || lowerLog.includes("error")) {
        return "text-red-400"
      }
    }

    if (lowerLog.includes("[action]") || lowerLog.includes("action:")) {
      return "text-blue-400"
    }

    if (lowerLog.includes("[observe]") || lowerLog.includes("observe:")) {
      return "text-amber-400"
    }

    return "text-gray-300"
  }

  return (
    <Card className={cn("flex flex-col", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Execution Logs</CardTitle>
          <div className="flex items-center gap-2">
            <Scroll className="h-4 w-4 text-muted-foreground" />
            <label
              htmlFor="auto-scroll"
              className="text-sm text-muted-foreground cursor-pointer flex items-center gap-2"
            >
              <Checkbox
                id="auto-scroll"
                checked={autoScroll}
                onCheckedChange={(checked) => setAutoScroll(checked === true)}
              />
              Auto-scroll
            </label>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          className="bg-slate-950 rounded-md p-4 h-[400px] overflow-y-auto font-mono text-sm"
        >
          {isLoading ? (
            <div className="text-gray-500">Waiting for logs...</div>
          ) : logs.length === 0 ? (
            <div className="text-gray-500">No logs available</div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div key={index} className={cn(getLogColor(log))}>
                  {log}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
