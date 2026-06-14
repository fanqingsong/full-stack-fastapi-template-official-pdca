"""API routes for causal analysis."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep
from app.causal.models import (
    CausalQueryRequest,
    CausalAnalysisResponse
)
from app.causal.nl_processor import NLQueryProcessor
from app.causal.data_extractor import (
    extract_pdca_features,
    get_available_variables,
    get_user_cycle_ids
)
from app.causal.engine import CausalEngine
from app.causal.graph_builder import build_graph_response, generate_explanation
from app.causal.exceptions import (
    InsufficientDataError,
    UnidentifiableEffectError,
    CausalAnalysisError
)


router = APIRouter(prefix="/causal", tags=["causal"])


@router.post("/analyze", response_model=CausalAnalysisResponse)
async def analyze_causal_relationships(
    request: CausalQueryRequest,
    current_user: CurrentUser,
    session: SessionDep
) -> CausalAnalysisResponse:
    """
    Analyze causal relationships from natural language query.

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
        available_vars = get_available_variables()

        analysis_request = nl_processor.extract_analysis_request(
            request.natural_language,
            available_vars
        )

        # Step 2: Load data
        cycle_ids = get_user_cycle_ids(session, current_user.id)
        if not cycle_ids:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "no_data",
                    "message": "No PDCA cycles found for analysis",
                    "recommendation": "Run some PDCA cycles first"
                }
            )

        data = extract_pdca_features(session, cycle_ids, current_user.id)

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
    except CausalAnalysisError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": str(e)
            }
        )


@router.get("/variables")
async def list_available_variables(
    current_user: CurrentUser
) -> Dict[str, Any]:
    """List variables available for causal analysis."""
    variables = get_available_variables()
    return {
        "variables": variables,
        "count": len(variables)
    }
