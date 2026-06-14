# Causal Inference Analysis Module - Design Specification

**Date**: 2025-06-14  
**Status**: Design Phase  
**Version**: 1.0  
**MVP Timeline**: 5 days

## Executive Summary

This specification describes a causal inference analysis module for the PDCA workflow system. The module enables users to ask natural language questions about what factors drive PDCA cycle success, execution times, and error patterns. The system uses structural causal models (SCM) to discover causal relationships from historical cycle data and presents results through interactive visualizations and natural language explanations.

**Goal**: Provide actionable causal insights to help users optimize their PDCA workflows and improve cycle outcomes.

## Architecture Overview

### System Components

The causal inference system is designed as a standalone module that integrates with the existing FastAPI backend and React frontend infrastructure.

**Backend Components** (`backend/app/causal/`):
- `engine.py` - Main causal analysis engine using causal-learn library
- `nl_processor.py` - Natural language query processor using existing OpenAI agent
- `models.py` - Data models for causal analysis requests/responses  
- `api.py` - FastAPI routes for causal analysis endpoints
- `data_extractor.py` - Feature extraction from PDCA cycle data
- `graph_builder.py` - Converts causal graphs to visualization format
- `exceptions.py` - Custom exception classes for causal analysis errors

**Frontend Components** (`frontend/src/routes/causal/`):
- `index.tsx` - Main causal analysis page container
- `query-panel.tsx` - Natural language query input component
- `graph-viewer.tsx` - Interactive causal graph visualization using vis.js
- `results-panel.tsx` - Natural language explanation and statistics display
- `types.ts` - TypeScript interfaces for API responses

**Database Integration**:
- Leverages existing `pdca_cycle` and `execution_log` tables
- No new database tables required for MVP
- Feature extraction transforms raw cycle data into analysis-ready format

### Technology Stack

**Backend**:
- `causal-learn` (^0.1.3) - Causal discovery algorithms (LiNGAM, PC, GES)
- `pandas` (^2.0.0) - Data manipulation and feature engineering
- `numpy` (^1.24.0) - Numerical computing
- `scikit-learn` (^1.3.0) - Statistical utilities and preprocessing
- Existing OpenAI agent integration for natural language processing

**Frontend**:
- `vis-network` (^9.1.6) - Interactive graph visualization
- TanStack Query for API data fetching
- Existing shadcn/ui components for UI elements

## Data Flow and User Experience

### User Workflow

1. **Navigation**: User accesses causal analysis via new menu item "Causal Analysis" in header
2. **Query Input**: User enters natural language question (e.g., "What causes my PDCA cycles to succeed?")
3. **Processing**: System parses query, extracts variables, loads relevant data, runs causal analysis
4. **Results Display**: User sees interactive causal graph with natural language explanation
5. **Exploration**: User can interact with graph (click nodes, hover for details) and export results

### Technical Data Flow

```
User Query → Frontend QueryPanel 
    → POST /api/v1/causal/analyze
        → NLProcessor extracts analysis parameters
        → DataExtractor loads PDCA features
        → CausalEngine discovers causal structure
        → GraphBuilder formats visualization
        → NLGenerator creates explanation
        → Response: graph + explanation + statistics
    → Frontend renders interactive results
```

### API Endpoint Design

**Primary Endpoint**:
```http
POST /api/v1/causal/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "natural_language": "What causes my PDCA cycles to succeed?",
  "max_results": 10
}
```

**Response**:
```json
{
  "graph": {
    "nodes": [
      {
        "name": "agent_type",
        "label": "Agent Type",
        "node_type": "treatment",
        "strength": 0.75
      }
    ],
    "edges": [
      {
        "cause": "agent_type",
        "effect": "success",
        "effect_size": 0.35,
        "confidence": 0.95,
        "method": "backdoor"
      }
    ]
  },
  "explanation": "Analysis of 150 PDCA cycles reveals that agent type is a significant causal factor for cycle success...",
  "statistics": {
    "sample_size": 150,
    "algorithm": "LiNGAM",
    "significance_tests": {...}
  },
  "query_understanding": "Analyzing factors that affect PDCA cycle success rates"
}
```

## Technical Implementation

### Backend Implementation

**Causal Engine** (`backend/app/causal/engine.py`):
```python
class CausalEngine:
    """Main causal analysis engine using causal-learn"""
    
    def __init__(self):
        self.algorithms = {
            "lingam": lingam.LiNGAM,
            "pc": pc.PC, 
            "ges": ges.GES
        }
    
    def analyze_causal_relationships(
        self, 
        data: pd.DataFrame, 
        treatment_vars: List[str], 
        outcome_var: str,
        algorithm: str = "lingam"
    ) -> CausalResult:
        """
        Discover and analyze causal relationships
        
        Steps:
        1. Data preprocessing and validation
        2. Causal structure discovery
        3. Structural model fitting
        4. Causal effect estimation
        5. Statistical validation
        """
        
        # Validate data quality
        if len(data) < 50:
            raise InsufficientDataError(
                f"Need at least 50 samples, got {len(data)}"
            )
        
        # Discover causal structure
        causal_graph = self._discover_structure(data, algorithm)
        
        # Identify causal mechanisms
        structural_model = self._fit_structural_model(data, causal_graph)
        
        # Estimate causal effects
        effects = self._estimate_effects(
            structural_model, treatment_vars, outcome_var
        )
        
        # Validate statistically
        statistics = self._validate_causal_claim(
            data, effects, causal_graph
        )
        
        return CausalResult(
            graph=causal_graph,
            effects=effects,
            statistics=statistics,
            model=structural_model
        )
```

**Natural Language Processing** (`backend/app/causal/nl_processor.py`):
```python
class NLQueryProcessor:
    """Process natural language queries using OpenAI agent"""
    
    def __init__(self):
        # Use existing OpenAI agent infrastructure
        self.agent = get_openai_agent()
    
    def extract_analysis_request(
        self, 
        query: str,
        available_vars: List[str]
    ) -> AnalysisRequest:
        """
        Parse natural language query into structured analysis request
        
        Expected query patterns:
        - "What causes [outcome]?" 
        - "Why do my cycles [outcome]?"
        - "What factors affect [outcome]?"
        - "Analyze drivers of [outcome]"
        """
        
        prompt = f"""
        Parse this causal analysis request about PDCA cycles.
        
        User Query: "{query}"
        
        Available Variables:
        {self._format_variables(available_vars)}
        
        Return a JSON object with:
        - outcome_variable: The main outcome to analyze
        - treatment_variables: List of potential causal factors
        - analysis_type: One of: success_factors, timing_drivers, error_analysis
        - filters: Any time range or cycle type filters mentioned
        
        Be conservative - if uncertain, ask for clarification rather than guessing.
        """
        
        response = await self.agent.execute(prompt)
        return AnalysisRequest.parse_raw(response)
```

**Data Extraction** (`backend/app/causal/data_extractor.py`):
```python
def extract_pdca_features(
    db: Session, 
    cycle_ids: List[UUID],
    owner_id: Optional[UUID] = None
) -> pd.DataFrame:
    """
    Extract causal analysis features from PDCA cycles
    
    Features extracted:
    - Outcomes: success (binary), duration_hours, error_count
    - Treatments: agent_type, has_parent, num_children
    - Confounders: owner_id, created_hour, day_of_week
    """
    
    query = select(PDCACycle).where(PDCACycle.id.in_(cycle_ids))
    if owner_id:
        query = query.where(PDCACycle.owner_id == owner_id)
    
    cycles = db.exec(query).all()
    
    features = []
    for cycle in cycles:
        # Calculate cycle duration
        duration = None
        if cycle.started_at and cycle.completed_at:
            duration = (cycle.completed_at - cycle.started_at).total_seconds() / 3600
        
        # Count execution errors
        error_count = db.exec(
            select(ExecutionLog).where(
                ExecutionLog.cycle_id == cycle.id,
                ExecutionLog.level == "error"
            )
        ).count()
        
        features.append({
            # Outcome variables
            "success": 1 if cycle.phase == "completed" else 0,
            "failed": 1 if cycle.phase == "failed" else 0,
            "duration_hours": duration if duration else 0,
            "error_count": error_count,
            
            # Treatment variables  
            "agent_type": cycle.agent_type or "unknown",
            "has_parent": 1 if cycle.parent_id else 0,
            "num_children": len(cycle.children),
            
            # Confounders
            "owner_id": str(cycle.owner_id),
            "created_hour": cycle.created_at.hour,
            "day_of_week": cycle.created_at.weekday(),
        })
    
    return pd.DataFrame(features)
```

**API Routes** (`backend/app/causal/api.py`):
```python
router = APIRouter(prefix="/api/v1/causal", tags=["causal"])

@router.post("/analyze", response_model=CausalAnalysisResponse)
async def analyze_causal_relationships(
    request: CausalQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CausalAnalysisResponse:
    """
    Analyze causal relationships from natural language query
    
    Process:
    1. Parse natural language query into analysis request
    2. Extract relevant PDCA cycle data
    3. Run causal discovery and effect estimation
    4. Generate natural language explanation
    5. Return graph + explanation + statistics
    """
    
    try:
        # Step 1: Parse query
        nl_processor = NLQueryProcessor()
        analysis_request = nl_processor.extract_analysis_request(
            request.natural_language,
            available_vars=get_available_variables()
        )
        
        # Step 2: Load data
        cycle_ids = get_user_cycle_ids(db, current_user.id, analysis_request.filters)
        data = extract_pdca_features(db, cycle_ids, current_user.id)
        
        # Step 3: Run causal analysis
        engine = CausalEngine()
        result = engine.analyze_causal_relationships(
            data=data,
            treatment_vars=analysis_request.treatment_variables,
            outcome_var=analysis_request.outcome_variable
        )
        
        # Step 4: Generate explanation
        explanation = await generate_explanation(
            result, 
            request.natural_language,
            current_user
        )
        
        # Step 5: Format response
        return CausalAnalysisResponse(
            graph=build_graph_response(result.graph),
            explanation=explanation,
            statistics=result.statistics,
            query_understanding=analysis_request.summary()
        )
        
    except InsufficientDataError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_data",
                "message": str(e),
                "recommendation": "Run more PDCA cycles or broaden time range"
            }
        )
    except UnidentifiableEffectError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unidentifiable_effect", 
                "message": str(e),
                "suggestion": "Try adding covariates or different analysis approach"
            }
        )
```

### Frontend Implementation

**Main Page Component** (`frontend/src/routes/causal/index.tsx`):
```typescript
export function CausalAnalysisPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CausalResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const analyzeMutation = useMutation({
    mutationFn: async (naturalLanguage: string) => {
      const response = await causalAPI.analyze({ 
        natural_language: naturalLanguage 
      });
      return response;
    },
    onSuccess: (data) => {
      setResults(data);
      setError(null);
    },
    onError: (err) => {
      setError(err.message);
      setResults(null);
    }
  });
  
  const exampleQueries = [
    "What causes my PDCA cycles to succeed?",
    "What factors lead to longer execution times?", 
    "Why do some cycles fail in the Check phase?"
  ];
  
  return (
    <div className="container mx-auto p-6">
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
          {loading && <LoadingSpinner />}
          {error && <ErrorAlert message={error} />}
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
```

**Graph Visualization** (`frontend/src/routes/causal/graph-viewer.tsx`):
```typescript
import { Network } from "vis-network/standalone";

interface GraphViewerProps {
  graph: CausalGraph;
}

export function GraphViewer({ graph }: GraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  
  useEffect(() => {
    if (!containerRef.current || !graph) return;
    
    // Transform causal graph to vis.js format
    const nodes = graph.nodes.map(node => ({
      id: node.name,
      label: node.label,
      size: 20 + node.strength * 30,
      color: getNodeColor(node.node_type),
      font: { size: 16 },
      title: `${node.label}\nStrength: ${node.strength.toFixed(2)}`
    }));
    
    const edges = graph.edges.map(edge => ({
      from: edge.cause,
      to: edge.effect,
      label: `β=${edge.effect_size.toFixed(2)}`,
      title: `Effect: ${edge.effect_size.toFixed(3)}\nConfidence: ${edge.confidence.toFixed(3)}`,
      arrows: "to",
      width: Math.abs(edge.effect_size) * 8,
      color: {
        color: edge.effect_size > 0 ? "#4ade80" : "#f87171",
        highlight: "#22c55e"
      }
    }));
    
    const options = {
      nodes: {
        shape: "box",
        margin: 10,
        widthConstraint: { maximum: 200 }
      },
      edges: {
        smooth: { type: "cubicBezier" },
        font: { align: "middle", size: 12 }
      },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -3000,
          centralGravity: 0.3
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true
      }
    };
    
    networkRef.current = new Network(
      containerRef.current,
      { nodes, edges },
      options
    );
    
    // Add click event for node details
    networkRef.current.on("click", (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        showNodeDetails(nodeId, graph);
      }
    });
    
  }, [graph]);
  
  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle>Causal Relationship Graph</CardTitle>
      </CardHeader>
      <CardContent>
        <div 
          ref={containerRef} 
          className="causal-graph-container"
          style={{ height: "600px" }}
        />
        <div className="mt-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded" />
            <span>Treatment</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded" />
            <span>Outcome</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded" />
            <span>Confounder</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Data Models

### Request/Response Models

```python
# backend/app/causal/models.py

class CausalQueryRequest(SQLModel):
    """Request model for causal analysis"""
    natural_language: str = Field(..., min_length=10, max_length=500)
    max_results: int = Field(default=10, ge=1, le=50)

class CausalNode(SQLModel):
    """Node in causal graph"""
    name: str
    label: str
    node_type: Literal["treatment", "outcome", "confounder", "mediator"]
    strength: float = Field(ge=0, le=1)

class CausalEdge(SQLModel):
    """Edge (causal relationship) in graph"""
    cause: str
    effect: str  
    effect_size: float
    confidence: float = Field(ge=0, le=1)
    method: Literal["backdoor", "frontdoor", "iv"]

class CausalGraph(SQLModel):
    """Complete causal graph structure"""
    nodes: List[CausalNode]
    edges: List[CausalEdge]
    metadata: Dict[str, Any] = {}

class CausalAnalysisResponse(SQLModel):
    """Response from causal analysis"""
    graph: CausalGraph
    explanation: str
    statistics: Dict[str, Any]
    query_understanding: str
    analysis_id: UUID = Field(default_factory=uuid.uuid4)

class AnalysisRequest(SQLModel):
    """Structured analysis request parsed from NL"""
    outcome_variable: str
    treatment_variables: List[str]
    analysis_type: Literal["success_factors", "timing_drivers", "error_analysis"]
    filters: Dict[str, Any] = {}
    
    def summary(self) -> str:
        return f"Analyzing how {', '.join(self.treatment_variables)} affect {self.outcome_variable}"
```

## Error Handling

### Custom Exceptions

```python
# backend/app/causal/exceptions.py

class CausalAnalysisError(Exception):
    """Base exception for causal analysis errors"""
    pass

class InsufficientDataError(CausalAnalysisError):
    """Raised when not enough data for reliable analysis"""
    def __init__(self, sample_size: int, required: int = 50):
        self.sample_size = sample_size
        self.required = required
        super().__init__(
            f"Insufficient data: {sample_size} samples, need at least {required}"
        )

class UnidentifiableEffectError(CausalAnalysisError):
    """Raised when causal effect cannot be identified"""
    def __init__(self, reason: str):
        super().__init__(f"Causal effect cannot be identified: {reason}")

class QueryAmbiguityError(CausalAnalysisError):
    """Raised when natural language query is too ambiguous"""
    def __init__(self, query: str, ambiguities: List[str]):
        self.ambiguities = ambiguities
        super().__init__(
            f"Query '{query}' is ambiguous. Please clarify: {', '.join(ambiguities)}"
        )
```

## Testing Strategy

### Backend Tests (pytest)

```python
# tests/causal/test_engine.py

def test_causal_discovery_with_known_structure():
    """Test causal discovery with synthetic ground truth"""
    # Generate data: X -> Y <- Z (no X-Z edge)
    data = generate_synthetic_data(
        n=1000,
        structure=[
            ("X", "Y", 0.5),
            ("Z", "Y", 0.3)
        ]
    )
    
    engine = CausalEngine()
    result = engine.analyze_causal_relationships(
        data=data,
        treatment_vars=["X", "Z"],
        outcome_var="Y"
    )
    
    # Should discover both causal edges
    assert len(result.graph.edges) == 2
    
    # Should not discover X -> Z (no causal relationship)
    assert not any(
        edge.cause == "X" and edge.effect == "Z" 
        for edge in result.graph.edges
    )

def test_nl_query_parsing():
    """Test natural language query processing"""
    processor = NLQueryProcessor()
    
    query = "What causes my cycles to succeed?"
    request = processor.extract_analysis_request(
        query,
        available_vars=["success", "agent_type", "duration_hours"]
    )
    
    assert request.outcome_variable == "success"
    assert len(request.treatment_variables) > 0
```

### Frontend Tests (Playwright)

```typescript
// tests/causal/causal-analysis.spec.ts

test('should perform causal analysis', async ({ page }) => {
  await page.goto('/causal-analysis');
  
  // Enter query
  await page.fill('[data-testid="causal-query"]', 'What causes cycle success?');
  await page.click('[data-testid="analyze-button"]');
  
  // Wait for results
  await page.waitForSelector('.causal-graph');
  
  // Verify graph is displayed
  const graph = page.locator('.causal-graph canvas');
  await expect(graph).toBeVisible();
  
  // Verify explanation is shown
  const explanation = page.locator('.causal-explanation');
  await expect(explanation).toContainText('causal');
});
```

## Implementation Timeline

### Day 1: Backend Foundation
**Goal**: Set up core causal inference infrastructure

- **Morning** (4 hours):
  - Install dependencies: `causal-learn`, `pandas`, `numpy`
  - Create `backend/app/causal/` module structure
  - Implement basic `CausalEngine` class
  - Add data extraction from PDCA cycles

- **Afternoon** (4 hours):
  - Create data models (`models.py`)
  - Implement API endpoints (`api.py`)
  - Add basic error handling (`exceptions.py`)
  - Write unit tests for engine

**Deliverable**: Working backend that can analyze PDCA data and return causal graphs

### Day 2: Natural Language Processing
**Goal**: Integrate natural language query processing

- **Morning** (4 hours):
  - Implement `NLQueryProcessor` using existing OpenAI agent
  - Design prompt templates for query parsing
  - Add query interpretation and validation logic

- **Afternoon** (4 hours):
  - Integrate NL processor with causal engine
  - Generate natural language explanations from results
  - End-to-end testing of analysis pipeline

**Deliverable**: Complete backend that accepts natural language queries and returns explanations

### Day 3: Frontend UI
**Goal**: Build user interface for causal analysis

- **Morning** (4 hours):
  - Create causal analysis route and page layout
  - Implement `QueryPanel` component
  - Add `ResultsPanel` for explanations

- **Afternoon** (4 hours):
  - Integrate vis.js for graph visualization
  - Implement `GraphViewer` with interactivity
  - Connect frontend to backend API

**Deliverable**: Complete frontend UI for causal analysis

### Day 4: Integration & Testing
**Goal**: Ensure system works end-to-end

- **Morning** (4 hours):
  - Write comprehensive unit tests
  - Add Playwright E2E tests
  - Create integration test script

- **Afternoon** (4 hours):
  - Fix bugs and edge cases
  - Add data quality validation
  - Performance testing with real data

**Deliverable**: Fully tested and optimized causal analysis system

### Day 5: Polish & Demo Prep
**Goal**: Prepare compelling demonstration

- **Morning** (4 hours):
  - UI refinements and responsive design
  - Add export functionality (PNG, PDF)
  - Create demo dataset with interesting findings

- **Afternoon** (4 hours):
  - Write user documentation
  - Create demo script
  - Final testing and bug fixes

**Deliverable**: Production-ready causal analysis feature with compelling demo

## Success Criteria

### Functional Requirements

**Must Have** (MVP):
- ✅ Users can ask natural language questions about PDCA cycle performance
- ✅ System discovers causal relationships using structural causal models
- ✅ Results include interactive graph visualization with vis.js
- ✅ Natural language explanations of causal findings
- ✅ Statistical validation with confidence intervals
- ✅ Analysis completes within 30 seconds for 100+ cycles
- ✅ Clear error messages for insufficient data or ambiguous queries

### Technical Requirements

**Must Have**:
- ✅ All tests pass (backend pytest + frontend Playwright)
- ✅ No breaking changes to existing PDCA system
- ✅ API responses documented with OpenAPI
- ✅ Code follows existing project patterns
- ✅ Proper error handling throughout

**Performance**:
- <30 seconds for analysis with 100 cycles
- <5 seconds for graph visualization
- <2 seconds for UI interactions

### Demo Requirements

**Compelling Demonstration**:
- Clear visual showing causal relationships (e.g., "OpenAI agent → 40% higher success")
- Natural language explanation that stakeholders can understand
- Interactive exploration of causal graph
- Working end-to-end with real PDCA data

**Business Value**:
- Actionable insights (e.g., "Use agent X to improve success by Y%")
- Data-driven recommendations
- Clear connection to PDCA workflow optimization

## Risks and Mitigation

### Risk 1: Insufficient Historical Data
**Impact**: High - Can't demonstrate causal inference without adequate data
**Probability**: Medium

**Mitigation**:
- Generate synthetic test data for MVP demonstration
- Clear error messages when data is insufficient
- Implement data quality checks before analysis

### Risk 2: Ambiguous Natural Language Queries
**Impact**: Medium - Poor user experience if queries aren't understood
**Probability**: High

**Mitigation**:
- Provide example queries as starting points
- Show how the system interpreted the query
- Allow users to refine interpretation

### Risk 3: Complex Causal Graphs
**Impact**: Medium - Users may struggle to interpret complex graphs
**Probability**: Medium

**Mitigation**:
- Implement graph simplification
- Provide zoom/filter capabilities
- Show only strongest relationships by default

## Future Enhancements

**Post-MVP Features**:
- Advanced causal discovery algorithms
- Intervention simulation ("What if I change X?")
- Counterfactual analysis
- Time-series causal analysis for cycle evolution
- Causal feature importance for ML models
- Integration with external data sources
- Real-time causal monitoring

## Conclusion

This design provides a comprehensive yet achievable MVP for causal inference analysis in the PDCA workflow system. The 5-day timeline is realistic with clear milestones and deliverables. The system leverages existing infrastructure while adding sophisticated causal analysis capabilities that will provide actionable insights to users.

The modular design allows for incremental enhancement based on user feedback, while the MVP focuses on the highest-value features: natural language queries, interactive visualizations, and clear explanations of causal relationships.

**Next Steps**:
1. Review and approve this specification
2. Set up development environment
3. Begin Day 1 implementation: Backend foundation
4. Follow timeline through Day 5: Demo preparation
5. Gather user feedback and plan enhancements
