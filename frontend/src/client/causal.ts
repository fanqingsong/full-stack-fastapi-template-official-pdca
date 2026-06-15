/** API client for causal inference analysis */

import { client } from "./client.gen";
import type {
  CausalAnalysisResponse,
  CausalQueryRequest,
  VariablesResponse
} from "../routes/causal/-types";

export const causalAPI = {
  /**
   * Analyze causal relationships from natural language query
   */
  analyze: async (request: CausalQueryRequest): Promise<CausalAnalysisResponse> => {
    const response = await client.post<CausalAnalysisResponse>({
      url: "/api/v1/causal/analyze",
      body: request,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as CausalAnalysisResponse;
  },

  /**
   * List available variables for analysis
   */
  listVariables: async (): Promise<VariablesResponse> => {
    const response = await client.get<VariablesResponse>({
      url: "/api/v1/causal/variables",
    });
    return response.data as VariablesResponse;
  },
};
