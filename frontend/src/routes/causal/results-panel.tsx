/** Results display panel for causal analysis */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CausalAnalysisResponse } from "./types";

interface ResultsPanelProps {
  explanation: string;
  statistics: CausalAnalysisResponse["statistics"];
  queryUnderstanding: string;
}

export function ResultsPanel({
  explanation,
  statistics,
  queryUnderstanding,
}: ResultsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Analysis Results</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Query Understanding */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-1">
            Query Understanding
          </h4>
          <p className="text-sm">{queryUnderstanding}</p>
        </div>

        {/* Statistics */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Analysis Statistics
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-gray-50 p-2 rounded">
              <div className="text-xs text-gray-600">Sample Size</div>
              <div className="font-semibold">{statistics.sample_size}</div>
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <div className="text-xs text-gray-600">Algorithm</div>
              <div className="font-semibold text-sm">{statistics.algorithm}</div>
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <div className="text-xs text-gray-600">Variables</div>
              <div className="font-semibold">{statistics.num_variables}</div>
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <div className="text-xs text-gray-600">Relationships</div>
              <div className="font-semibold">{statistics.num_edges}</div>
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-1">
            Key Findings
          </h4>
          <div className="bg-blue-50 p-3 rounded text-sm whitespace-pre-wrap">
            {explanation}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
