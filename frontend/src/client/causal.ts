/** API client for causal inference analysis */

import { api } from "./client";
import type {
  CausalAnalysisResponse,
  CausalQueryRequest,
  VariablesResponse
} from "../routes/causal/types";

export const causalAPI = {
  /**
   * Analyze causal relationships from natural language query
   */
  analyze: async (request: CausalQueryRequest): Promise<CausalAnalysisResponse> => {
    const response = await api.post<CausalAnalysisResponse>(
      "/api/v1/causal/analyze",
      request
    );
    return response.data;
  },

  /**
   * List available variables for analysis
   */
  listVariables: async (): Promise<VariablesResponse> => {
    const response = await api.get<VariablesResponse>("/api/v1/causal/variables");
    return response.data;
  },
};
