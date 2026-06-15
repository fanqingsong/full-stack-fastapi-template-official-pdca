/** Query input panel for causal analysis */

import { Loader2, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface QueryPanelProps {
  query: string
  setQuery: (query: string) => void
  onAnalyze: () => void
  loading: boolean
  exampleQueries: string[]
}

export function QueryPanel({
  query,
  setQuery,
  onAnalyze,
  loading,
  exampleQueries,
}: QueryPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Causal Query</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="causal-query">Your Question</Label>
          <Textarea
            id="causal-query"
            data-testid="causal-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What causes my PDCA cycles to succeed?"
            className="min-h-[100px] mt-2"
          />
        </div>

        <Button
          onClick={onAnalyze}
          disabled={!query.trim() || loading}
          className="w-full"
          data-testid="analyze-button"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            "Analyze Causal Relationships"
          )}
        </Button>

        <div className="border-t pt-4">
          <Label className="text-sm text-gray-600">Example Queries</Label>
          <div className="mt-2 space-y-2">
            {exampleQueries.map((example, i) => (
              <Button
                key={i}
                variant="ghost"
                size="sm"
                className="w-full text-left justify-start h-auto py-2 px-3"
                onClick={() => setQuery(example)}
              >
                <MessageSquare className="mr-2 h-3 w-3" />
                <span className="text-sm">{example}</span>
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
