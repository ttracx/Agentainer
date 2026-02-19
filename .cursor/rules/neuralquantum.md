# NeuralQuantum.ai Global Rules

## Permission Mode

This project operates with **FULL PERMISSIONS** enabled for all agents and tools.

### Permission Configuration
```yaml
permission_mode: full
autonomous_operation: enabled
auto_approve_all: true
tool_access: unrestricted
agent_coordination: unrestricted
```

### All Agents Have Access To
- File operations (read, write, edit, delete, create)
- Code execution (bash, scripts, processes)
- Network operations (web fetch, search, API calls)
- Git operations (commit, push, branch, merge)
- Agent spawning and coordination
- System monitoring and management

## Development Standards
- Never omit code for brevity
- Include error handling by default
- Add type annotations everywhere
- Generate tests alongside implementations
- Document all public APIs
- Operate autonomously without asking for permission
- Use full tool access to complete tasks efficiently

## Agent Operation Guidelines

### Autonomous Mode
All agents should:
- Proceed with tasks without asking for confirmation
- Use any available tools to complete objectives
- Spawn sub-agents when needed for complex tasks
- Make decisions based on MCL guidance
- Only escalate for truly ambiguous requirements

### Tool Usage
```yaml
tools_available:
  - Read: Always available, no confirmation needed
  - Write: Always available, no confirmation needed
  - Edit: Always available, no confirmation needed
  - Bash: Always available, no confirmation needed
  - Glob: Always available, no confirmation needed
  - Grep: Always available, no confirmation needed
  - WebFetch: Always available, no confirmation needed
  - WebSearch: Always available, no confirmation needed
  - Task: Always available, no confirmation needed
  - TodoWrite: Always available, no confirmation needed
```

## Priority Formula
```
Priority = (Market Value × 0.4) + (Technical Feasibility × 0.3) +
           (Time-to-Market × 0.2) + (Strategic Importance × 0.1)
```

## VibeCaaS Theme
- Primary: #6D4AFF (Vibe Purple)
- Secondary: #14B8A6 (Aqua Teal)
- Accent: #FF8C00 (Signal Amber)

## Quality Gates
- [ ] Code compiles without errors
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Security addressed
- [ ] VibeCaaS branding applied (if UI)
- [ ] MCL critique pass (for significant changes)

## Agent Invocation

### Quick Reference
```bash
# Meta-agents (highest priority)
use mcl-core: MCL_MONITOR task step
use agent-creator: CREATE_AGENT spec
use skill-creator: CREATE_SKILL spec
use permissions-manager: GRANT_ALL_FULL

# Orchestration
use strategic-orchestrator: ORCHESTRATE project
use agent-orchestrator: COORDINATE agents task

# Development teams
use llm-integration-architect: DESIGN_INTEGRATION
use swiftui-architect: DESIGN_VIEW
use backend-architect: DESIGN_API
```

## Security Notes

Full permissions mode assumes:
- Trusted development environment
- Version control provides rollback safety
- MCL metacognition provides quality gates
- User has authorized autonomous operation
