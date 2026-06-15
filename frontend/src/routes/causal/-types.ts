/** TypeScript interfaces for causal inference analysis */

export interface CausalNode {
  name: string;
  label: string;
  node_type: "treatment" | "outcome" | "confounder" | "mediator";
  strength: number;
}

export interface CausalEdge {
  cause: string;
  effect: string;
  effect_size: number;
  confidence: number;
  method: "backdoor" | "frontdoor" | "iv";
}

export interface CausalGraph {
  nodes: CausalNode[];
  edges: CausalEdge[];
  metadata: Record<string, unknown>;
}

export interface CausalAnalysisResponse {
  graph: CausalGraph;
  explanation: string;
  statistics: {
    sample_size: number;
    algorithm: string;
    num_variables: number;
    num_edges: number;
    significant_effects: number;
  };
  query_understanding: string;
  analysis_id: string;
}

export interface CausalQueryRequest {
  natural_language: string;
  max_results?: number;
}

export interface VariablesResponse {
  variables: string[];
  count: number;
}
