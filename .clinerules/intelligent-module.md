# Intelligent Module
    
## Goal : This module will implement multiagent system that exposed interfaces 
            "query" : this will accept user input as { input: string } and return answer from system
            the team will be answer question about 
            - software requirement document
            - technical question 
            - code question
            - find root cause of incident
    
## Tech stack :
    - **Python**
    - **FastAPI**
    - **Agno**
    - **Postgres** 

## PMO multiagent system

### Inten classifer
    - Not include in Team, It is stand alone agent.
    - It role is to capture intent of user input and rewrite user input to be more semantic.
    - It will accept user input and return output. Later the program must use this as input to Team
    input :
        {
            input: ...
        }
    output :
        {
            intent: ... , (enum QA, RCA , ...)
            goal: .... (main goal)
        }

### Team 

#### Manager(Team Leader, Orchestrator)
        ** Read Agno document from context7 mcp before implement this agent
        - The system have Manager agent which is Agno team class.
        - It must accept and return structure input (from intent classifer).
        - It must be able to reasoning and planing step by step to reach goal using Chain of though.
            for example
                Case 1 : User inout what happen
                    1. it plan to investigate codebase
                    2. after investigate ,it know that this code get data from db
                    3. it check db
                Case 2: User send trace include
                    1. get trace detail from Grafana
                    2. investigate code
                    3. check db to ensure 
        - LLM of this agent should be thinking model or have high reasoning capability.
        - After it create plan ,it should decide which agent team member to call sequentually.
        - Manager can delagate as many turns as it want to reach it goals (but limit by paramater).
        - Manager should be able to detect if current plan hit a wall and can not reach goal with current plan ,and dynamically 
            create new plan after that or even backtracking to previous state. The retry is limit by config parameter.
        - Manager should be able to ask user for clarification if it need.
        - It should be able to manage session , memory and history via Agno API and use Postgres as         persistence layer
        input :
            {
                intent: ... , (enum QA, RCA , ...)
                goal: .... (main goal)
            }
        output : 
            {
                task : ... ,
                goal : ... (sub goal)
                confident_score: ....
            }

#### Code Agent
        - Subagent callable by Manager 
        - It is Gemini CLI Subprocess that start subprocess in target project directory wrapped in Agno Agent
        - Return value should be summarized or context compression to capture relavant information without take too much context window
        - Gemini CLI should use Serena MCP for semantic retrieval so that Gemini can hybrid search codebase for faster execution
        - Repomix and repo mapping for context
        input : 
            {
                task : ... ,
                goal : ... (sub goal)
                confident_score: ....
            }
        output : 
            {
                completed : ...
                summary: ...
            }

#### SQL Agent
        - Agno Agent 
        - it should query with  pagination , specific feilds and filter that need to answer question, not select all
        - It should not push all query result to context window (only relavant data to the question)
        - Required context when innitiate (e.g db credential, endpoint, table, data dict for performance)
        input : 
            {
                task: ... ,
                goal: ...
            }
        output : 
            {
                data: ...,
                completed: ...,
                summariy: ...
            }

#### Grafana Agent
        - Agno Agent 
        - it should query with  pagination , specific feilds and filter that need to answer question, not select all
        - It should not push all query result to context window (only relavant data to the question)
        - It requires credential , endpoint and config variable
        - It should be able to know what to do (lis tracing, get tracing detail)
        input : 
            {
                task: ... ,
                goal: ...
            }
        output : 
            {
                data: ...,
                completed: ...,
                summariy: ...
            }


#### Document Agent
        - Agno agent 
        - Call LightRAG for semantic retrieval as knowledge tools
            input : 
            {
                task: ... ,
                goal: ...
            }
        output : 
            {
                data: ...,
                completed: ...,
                summariy: ...
            }



### Prompt
    Manager 


*** Codebase contain code, tracing name and database table name