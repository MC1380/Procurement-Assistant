# ProcureFlow AI — Architecture

## 1. Project Goal

ProcureFlow AI is a portfolio AI Agent that simulates industrial procurement workflows. It evaluates purchase requests, checks business rules, retrieves procurement policies, and requests manager approval when required.

All external business systems are simulated. No real purchase is executed.

## 2. Technology Stack

- **Python:** Core application logic
- **LangGraph:** Workflow orchestration, conditional routing, and human-in-the-loop
- **LangChain:** LLM integration, tools, and RAG
- **MCP:** Standardized access to external and simulated tools
- **SQLite + SQLAlchemy:** Persistent business data
- **FastAPI:** Backend API
- **Gradio:** Simple interactive demo
- **pytest:** Automated testing

## 3. Main Components

- **Domain layer:** Purchase requests, suppliers, budgets, policies, and business rules
- **Workflow layer:** Purchase evaluation, routing, and manager approval
- **Data layer:** Persistent storage for business entities
- **Knowledge layer:** Retrieval of procurement policies and documents
- **Tool layer:** Simulated inventory and supplier operations, including MCP integration
- **Interface layer:** Gradio demo and FastAPI endpoints

## 4. Purchase Workflow

1. Receive a purchase request.
2. Check inventory, supplier eligibility, budget, and procurement policies.
3. Determine whether the request can proceed automatically or requires manager review.
4. Pause for manager approval when required.
5. Continue or stop based on the manager's decision.
6. Record the outcome and relevant business data.

## 5. Safety and Scope

- No real purchase orders or payments.
- Manager approval is required for sensitive or restricted requests.
- The LLM must not override deterministic business rules.
- External tools operate in simulation mode.
- Automated tests verify important business and workflow scenarios.

## 6. Development Principles

- Implement small, testable increments.
- Run tests before meaningful commits.
- Keep architecture documentation updated.
- Add technologies only when they serve a clear project requirement.
- Production deployment is outside the current scope.