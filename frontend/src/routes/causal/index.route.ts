/** Route definition for causal analysis */

import { createFileRoute } from "@tanstack/react-router";
import { CausalAnalysisPage } from "./index";

export const causalRoute = createFileRoute("/causal-analysis")({
  component: CausalAnalysisPage,
});
