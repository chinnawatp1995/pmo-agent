# Agents 

## 1. Intent Classifier (The Router)
- **Description**: Agno Agent interact with user input and understand intent of user input before system call team agent 
- **Goal**: Identify if a query is Functional (GraphRAG), Technical (Code/Traces), or Operational (SQL).
- **Output**: Returns a `RouteModel` containing the target agent and priority.

## 2. Team (The Orchestrator)
- **Description**: Agno Team . Responsible for reason, planning, and delegate task to subagent
- **Goal**: Loop management. If a sub-agent fails, the Team decides to retry or escalate.
- **Output**: Returns a `TeamOutputModel` containing the target agent and priority.

## 3. SQL Agent (The Data Specialist)
- **Description**: Agno Agent accept Pydantic data from team and write sql to investigate data.
- **Goal**: Natural Language to SQL/pg_vector.
- **Output**: Returns a `SQLOutputModel` containing the target agent and priority.

## 4. Grafana Tempo Agent (The Investigator)
- **Description**: Agno agent that can query tracing list, trace detail.
- **Goal**: Trace Analysis. Finds latency bottlenecks or error spans in distributed traces.
- **Output**: Returns a `GrafanaOutputModel` containing the target agent and priority.

## 5. Coding Agent 
- **Description**: Agno Agent call Gemini CLI running on subprocess
- **Goal**: File-level debugging and code synthesis.
- **Output**: Returns a `CodeOutputModel` containing the target agent and priority.
