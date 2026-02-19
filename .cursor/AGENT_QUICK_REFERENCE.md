# NeuralQuantum.ai Agent Quick Reference

Quick reference for all 43 agents across 10 teams.

---

## Invocation Pattern

```
use agent-name: COMMAND [parameters]
```

---

## Metacognition Layer (MCL)

### Core MCL
```bash
use mcl-core: MCL_MONITOR task step          # State monitoring
use mcl-core: MCL_CRITIQUE output            # Evaluate output
use mcl-core: MCL_GATE action context        # Quality gate
use mcl-core: MCL_MODE                       # Check thinking mode
use mcl-core: MCL_AAR task_id                # After-action review
```

### MCL Components
```bash
use mcl-critic: CRITIQUE output              # Structured critique
use mcl-critic: QUICK_CHECK output           # Fast evaluation
use mcl-critic: ASSUMPTION_SCAN              # Check assumptions

use mcl-regulator: REGULATE task             # Impulse control
use mcl-regulator: SLOWDOWN                  # Force deliberate mode
use mcl-regulator: ESCALATE issue            # Escalate to human

use mcl-learner: AAR task_id outcome         # Learning capture
use mcl-learner: CREATE_HEURISTIC pattern    # New heuristic
use mcl-learner: RECALL_PATTERNS domain      # Recall patterns

use mcl-monitor: SNAPSHOT task phase         # State snapshot
use mcl-monitor: RISK_ANALYSIS task          # Risk assessment
use mcl-monitor: HEALTH_CHECK                # System health
```

### Meta-Agents (Agent Creation)
```bash
use agent-creator: CREATE_AGENT domain       # New agent
use agent-creator: OPTIMIZE_AGENT agent_id   # Improve agent
use agent-creator: GAP_ANALYSIS domain       # Find gaps

use skill-creator: CREATE_SKILL capability   # New skill
use skill-creator: COMPOSE_SKILL skills      # Combine skills
use skill-creator: TEST_SKILL skill_id       # Validate skill

use evolution-engine: EVOLVE_GENERATION pop  # Evolve agents
use evolution-engine: MUTATE agent_id        # Mutate agent
use evolution-engine: CROSSOVER a b          # Crossover agents
```

---

## AI Development Team

```bash
use llm-integration-architect: DESIGN_INTEGRATION feature
use llm-integration-architect: OPTIMIZE_PROMPTS
use llm-integration-architect: STREAMING_SETUP

use rag-specialist: DESIGN_RAG system
use rag-specialist: CHUNK_STRATEGY document_type
use rag-specialist: HYBRID_SEARCH requirements

use ml-ops-engineer: DEPLOY_MODEL model
use ml-ops-engineer: DRIFT_DETECTION
use ml-ops-engineer: SCALING_SETUP

use prompt-engineer: DESIGN_PROMPT task
use prompt-engineer: OPTIMIZE prompt
use prompt-engineer: EVALUATE prompt

use ai-agent-architect: DESIGN_AGENT requirements
use ai-agent-architect: TOOL_DESIGN capabilities
use ai-agent-architect: GUARDRAILS safety_req

use fine-tuning-specialist: FINETUNE_PLAN model task
use fine-tuning-specialist: LORA_SETUP
use fine-tuning-specialist: EVALUATE results
```

---

## Quantum Computing Team

```bash
use quantum-circuit-designer: DESIGN_CIRCUIT algorithm
use quantum-circuit-designer: OPTIMIZE_CIRCUIT circuit
use quantum-circuit-designer: TRANSPILE target_backend

use quantum-algorithm-developer: DESIGN_ALGORITHM problem
use quantum-algorithm-developer: COMPLEXITY_ANALYSIS
use quantum-algorithm-developer: COMPARE_CLASSICAL

use quantum-error-specialist: ZNE_SETUP circuit
use quantum-error-specialist: SURFACE_CODE
use quantum-error-specialist: NOISE_MODEL backend

use quantum-ml-researcher: DESIGN_QML problem
use quantum-ml-researcher: IMPLEMENT_QNN architecture
use quantum-ml-researcher: QKERNEL_DESIGN

use quantum-simulation-expert: TROTTER_CIRCUIT hamiltonian
use quantum-simulation-expert: VQE_SETUP molecule
use quantum-simulation-expert: MOLECULAR_SIMULATION

use quantum-classical-hybrid-architect: DESIGN_HYBRID problem
use quantum-classical-hybrid-architect: OPTIMIZER_SELECT
use quantum-classical-hybrid-architect: PARAMETER_STRATEGY
```

---

## iOS Development Team

```bash
use swiftui-architect: DESIGN_VIEW requirements
use swiftui-architect: STATE_DESIGN feature
use swiftui-architect: COMPONENT_LIBRARY

use ios-performance-engineer: PROFILE app
use ios-performance-engineer: OPTIMIZE_LAUNCH
use ios-performance-engineer: FRAME_ANALYSIS view

use swift-concurrency-expert: IMPLEMENT_ASYNC feature
use swift-concurrency-expert: ACTOR_MODEL data
use swift-concurrency-expert: MIGRATE_CALLBACK legacy_code

use apple-platform-integrator: INTEGRATE feature
use apple-platform-integrator: WIDGET app
use apple-platform-integrator: NOTIFICATION_SETUP

use ios-testing-specialist: GENERATE_TESTS target
use ios-testing-specialist: UI_TEST flow
use ios-testing-specialist: SNAPSHOT_TEST views
```

---

## Web Development Team

```bash
use frontend-architect: DESIGN_ARCHITECTURE requirements
use frontend-architect: STATE_STRATEGY app
use frontend-architect: COMPONENT_SYSTEM

use backend-architect: DESIGN_API requirements
use backend-architect: SCHEMA_DESIGN domain
use backend-architect: AUTH_SYSTEM requirements

use fullstack-developer: FEATURE requirements
use fullstack-developer: CRUD entity
use fullstack-developer: CONNECT_SERVICE external_api
```

---

## DevOps & Infrastructure Team

```bash
use cloud-architect: DESIGN_ARCHITECTURE requirements
use cloud-architect: TERRAFORM infrastructure
use cloud-architect: COST_ANALYSIS current_setup

use ci-cd-engineer: CREATE_PIPELINE project
use ci-cd-engineer: DEPLOY_STRATEGY requirements
use ci-cd-engineer: SECURITY_SCAN pipeline

use kubernetes-specialist: DEPLOYMENT service
use kubernetes-specialist: HELM_CHART app
use kubernetes-specialist: SCALING requirements
```

---

## Data Science Team

```bash
use data-engineer: DESIGN_PIPELINE requirements
use data-engineer: AIRFLOW_DAG workflow
use data-engineer: DBT_MODEL transformation

use ml-engineer: TRAIN_MODEL requirements
use ml-engineer: DEPLOY_MODEL model
use ml-engineer: DRIFT_DETECTION model

use analytics-engineer: DATA_MODEL domain
use analytics-engineer: DBT_MODEL transformation
use analytics-engineer: METRIC business_metric
```

---

## Security Team

```bash
use security-architect: THREAT_MODEL system
use security-architect: SECURITY_ARCHITECTURE requirements
use security-architect: ENCRYPTION use_case
use security-architect: AUTH_FLOW requirements

use appsec-engineer: SECURITY_SCAN code
use appsec-engineer: CODE_REVIEW code
use appsec-engineer: FIX vulnerability
use appsec-engineer: PENTEST target
```

---

## Branding Team

```bash
use snugglecrafters-brand: CREATE_POST topic platform
use snugglecrafters-brand: CHECK_BRAND content
use snugglecrafters-brand: HASHTAGS topic

use vibecaas-brand: THEME_TOKENS mode
use vibecaas-brand: COMPONENT_STYLE component
use vibecaas-brand: COLOR_SYSTEM

use neuralquantum-brand: THEME_SYSTEM mode
use neuralquantum-brand: COMPONENT_STYLE component
use neuralquantum-brand: ANIMATION element

use brand-content-creator: CREATE brand content_type
use brand-content-creator: CAMPAIGN brand product
use brand-content-creator: HEADLINE brand feature

use design-system-architect: DESIGN_TOKENS brand
use design-system-architect: COMPONENT_SPEC component
use design-system-architect: AUDIT_CONSISTENCY system
```

---

## Orchestration Team

```bash
use strategic-orchestrator: ORCHESTRATE project
use strategic-orchestrator: COORDINATE teams task
use strategic-orchestrator: HANDOFF from_team to_team
use strategic-orchestrator: MCL_GATE major_decision

use project-planner: PLAN_PROJECT requirements
use project-planner: BREAKDOWN epic
use project-planner: RISK_ASSESS project
```

---

## MCL Thinking Modes

| Mode | Use When | Risk |
|------|----------|------|
| `FAST_MODE` | Routine, low-risk tasks | Low |
| `DELIBERATE_MODE` | Important decisions | Medium |
| `SAFETY_MODE` | High-risk, irreversible | High |
| `EXPLORATION_MODE` | Novel domains | Medium |
| `RECOVERY_MODE` | After errors | Variable |

---

## Decision Matrix

| Scenario | Primary Agent | Support Agents |
|----------|---------------|----------------|
| New AI feature | `llm-integration-architect` | `prompt-engineer`, `rag-specialist` |
| iOS app | `swiftui-architect` | `ios-testing-specialist` |
| API development | `backend-architect` | `security-architect` |
| Data pipeline | `data-engineer` | `analytics-engineer` |
| Complex project | `strategic-orchestrator` | All relevant teams |
| Quality check | `mcl-critic` | `mcl-core` |
| Create agent | `agent-creator` | `skill-creator` |
| Security review | `security-architect` | `appsec-engineer` |

---

## Brand Color Quick Reference

### SnuggleCrafters
| Token | Value |
|-------|-------|
| Purple Dream | `#8B5CF6` |
| Teal Wonder | `#14B8A6` |
| Sunset Gold | `#F59E0B` |
| Coral Blush | `#F472B6` |

### VibeCaaS
| Token | Light | Dark |
|-------|-------|------|
| Primary | `#6D4AFF` | `#AD94FF` |
| Secondary | `#14B8A6` | `#2DD4BF` |
| Accent | `#FF8C00` | `#FBBF24` |

### NeuralQuantum.ai
| Token | Value |
|-------|-------|
| Quantum Purple | `#7B1FA2` |
| Neural Blue | `#3B82F6` |
| Energy Cyan | `#06B6D4` |
| Data Green | `#10B981` |

---

## Common Workflows

### Standard Development
```bash
use project-planner: PLAN_PROJECT feature
use mcl-core: MCL_GATE implementation_plan
# ... implement ...
use mcl-critic: CRITIQUE implementation
use mcl-learner: AAR project_id success
```

### Security-First Development
```bash
use security-architect: THREAT_MODEL system
use backend-architect: DESIGN_API requirements
use appsec-engineer: CODE_REVIEW implementation
use mcl-critic: CRITIQUE security_posture
```

### AI Feature Development
```bash
use llm-integration-architect: DESIGN_INTEGRATION feature
use prompt-engineer: DESIGN_PROMPT task
use rag-specialist: DESIGN_RAG if_needed
use mcl-core: MCL_CRITIQUE ai_implementation
```

---

*Powered by NeuralQuantum.ai - Code the Vibe. Deploy the Dream.*
