/** Main causal analysis page */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

import { QueryPanel } from "./query-panel";
import { GraphViewer } from "./graph-viewer";
import { ResultsPanel } from "./results-panel";
import { causalAPI } from "@/client/causal";
import type { CausalAnalysisResponse } from "./types";

export function CausalAnalysisPage() {
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: async (naturalLanguage: string) => {
      setError(null);
      const response = await causalAPI.analyze({
        natural_language: naturalLanguage,
        max_results: 10,
      });
      return response;
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail?.message || err.message || "Analysis failed";
      setError(message);
    },
  });

  const exampleQueries = [
    "What causes my PDCA cycles to succeed?",
    "What factors lead to longer execution times?",
    "Why do some cycles fail in the Check phase?",
  ];

  const results = analyzeMutation.data;

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Causal Analysis</h1>
        <p className="text-gray-600 mt-1">
          Discover what factors drive your PDCA cycle outcomes
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Query Panel - Left Sidebar */}
        <div className="col-span-3">
          <QueryPanel
            query={query}
            setQuery={setQuery}
            onAnalyze={() => analyzeMutation.mutate(query)}
            loading={analyzeMutation.isPending}
            exampleQueries={exampleQueries}
          />
        </div>

        {/* Graph Viewer - Center */}
        <div className="col-span-6">
          {analyzeMutation.isPending && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p className="text-gray-600">Analyzing causal relationships...</p>
              </div>
            </div>
          )}

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {results && <GraphViewer graph={results.graph} />}
        </div>

        {/* Results Panel - Right Sidebar */}
        <div className="col-span-3">
          {results && (
            <ResultsPanel
              explanation={results.explanation}
              statistics={results.statistics}
              queryUnderstanding={results.query_understanding}
            />
          )}
        </div>
      </div>
    </div>
  );
}
