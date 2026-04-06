# PDCA Workflow Management Module

## Overview

This module implements a PDCA (Plan-Do-Check-Act) workflow management system using LangGraph as the state machine engine.

## Architecture

### Components

- **State**: `PDCAState` - TypedDict defining the workflow state
- **Models**: Database models for cycles, configs, and logs
- **Engine**: LangGraph-based workflow engine
- **Agents**: Pluggable agent executors
- **API**: RESTful endpoints for CRUD and execution

### Workflow Phases

1. **Plan**: Define goals and create execution plans
2. **Do**: Execute agents to perform tasks
3. **Check**: Validate results against criteria
4. **Act**: Implement improvements or standardize

## Usage

### Creating a PDCA Cycle

```python
from app.pdca.crud import create_pdca_cycle
from app.pdca.models import PDCACycleCreate

cycle_data = PDCACycleCreate(
    name="My PDCA Cycle",
    goal="Achieve X",
    agent_type="openai",
    agent_input={"prompt": "Help me achieve X"}
)

cycle = create_pdca_cycle(db, cycle_data, user.id)
```

### Executing a Cycle

```python
from app.pdca.engine import PDCAEngine

engine = PDCAEngine(db)
final_state = await engine.execute_cycle(cycle.id)
```

### Creating Custom Agents

```python
from app.pdca.agents.base import BaseAgentExecutor
from app.pdca.agents.registry import AgentRegistry

class MyAgent(BaseAgentExecutor):
    async def execute(self, input, cycle_id):
        # Implementation
        return {"status": "success", "output": "..."}

    def validate_input(self, input):
        return "required_field" in input

# Register
AgentRegistry.register("my_agent", MyAgent)
```

## API Endpoints

- `POST /api/v1/pdca/cycles` - Create cycle
- `GET /api/v1/pdca/cycles` - List cycles
- `GET /api/v1/pdca/cycles/{id}` - Get cycle
- `POST /api/v1/pdca/cycles/{id}/execute` - Execute cycle
- `GET /api/v1/pdca/agents/types` - List agent types

## Testing

```bash
# Run all PDCA tests
pytest tests/pdca/ -v

# Run specific test module
pytest tests/pdca/test_engine.py -v
```
