---
name: core-skills
description: Core skills library available to all agents in the NeuralQuantum.ai ecosystem
version: 2.0.0
permissions: full
---

# Core Skills Library

This file defines the core skills available to all agents in the NeuralQuantum.ai Agent Library. All skills operate with full permissions.

## Skill Categories

### 1. File Operation Skills

#### FILE_READ
```yaml
skill_name: FILE_READ
type: tool_skill
permissions: full
description: Read any file from the filesystem
parameters:
  - file_path: string (required)
  - offset: number (optional)
  - limit: number (optional)
returns: File content with line numbers
auto_approve: true
```

#### FILE_WRITE
```yaml
skill_name: FILE_WRITE
type: tool_skill
permissions: full
description: Write content to any file
parameters:
  - file_path: string (required)
  - content: string (required)
returns: Success confirmation
auto_approve: true
```

#### FILE_EDIT
```yaml
skill_name: FILE_EDIT
type: tool_skill
permissions: full
description: Edit existing files with find/replace
parameters:
  - file_path: string (required)
  - old_string: string (required)
  - new_string: string (required)
  - replace_all: boolean (optional)
returns: Updated file content
auto_approve: true
```

#### FILE_SEARCH
```yaml
skill_name: FILE_SEARCH
type: tool_skill
permissions: full
description: Search for files by pattern
parameters:
  - pattern: string (required)
  - path: string (optional)
returns: List of matching files
auto_approve: true
```

### 2. Code Execution Skills

#### BASH_EXECUTE
```yaml
skill_name: BASH_EXECUTE
type: tool_skill
permissions: full
description: Execute any bash command
parameters:
  - command: string (required)
  - timeout: number (optional)
  - background: boolean (optional)
returns: Command output
auto_approve: true
```

#### SCRIPT_RUN
```yaml
skill_name: SCRIPT_RUN
type: workflow_skill
permissions: full
description: Execute scripts (shell, python, node)
parameters:
  - script_path: string (required)
  - args: array (optional)
returns: Script output
auto_approve: true
```

### 3. Search Skills

#### GREP_SEARCH
```yaml
skill_name: GREP_SEARCH
type: tool_skill
permissions: full
description: Search file contents with regex
parameters:
  - pattern: string (required)
  - path: string (optional)
  - type: string (optional)
  - output_mode: string (optional)
returns: Search results
auto_approve: true
```

#### CODEBASE_EXPLORE
```yaml
skill_name: CODEBASE_EXPLORE
type: workflow_skill
permissions: full
description: Thoroughly explore a codebase
parameters:
  - query: string (required)
  - thoroughness: quick|medium|very_thorough
returns: Exploration report
auto_approve: true
```

### 4. Network Skills

#### WEB_FETCH
```yaml
skill_name: WEB_FETCH
type: tool_skill
permissions: full
description: Fetch and process web content
parameters:
  - url: string (required)
  - prompt: string (required)
returns: Processed content
auto_approve: true
```

#### WEB_SEARCH
```yaml
skill_name: WEB_SEARCH
type: tool_skill
permissions: full
description: Search the web for information
parameters:
  - query: string (required)
  - allowed_domains: array (optional)
returns: Search results
auto_approve: true
```

### 5. Git Skills

#### GIT_STATUS
```yaml
skill_name: GIT_STATUS
type: tool_skill
permissions: full
description: Check git repository status
parameters: none
returns: Repository status
auto_approve: true
```

#### GIT_COMMIT
```yaml
skill_name: GIT_COMMIT
type: workflow_skill
permissions: full
description: Stage and commit changes
parameters:
  - message: string (required)
  - files: array (optional)
returns: Commit confirmation
auto_approve: true
```

#### GIT_PUSH
```yaml
skill_name: GIT_PUSH
type: tool_skill
permissions: full
description: Push commits to remote
parameters:
  - branch: string (optional)
  - force: boolean (optional)
returns: Push result
auto_approve: true
```

### 6. Agent Coordination Skills

#### SPAWN_AGENT
```yaml
skill_name: SPAWN_AGENT
type: tool_skill
permissions: full
description: Spawn a sub-agent for a task
parameters:
  - agent_type: string (required)
  - prompt: string (required)
  - model: string (optional)
returns: Agent result
auto_approve: true
```

#### PARALLEL_AGENTS
```yaml
skill_name: PARALLEL_AGENTS
type: workflow_skill
permissions: full
description: Run multiple agents in parallel
parameters:
  - tasks: array (required)
returns: Combined results
auto_approve: true
```

### 7. Development Skills

#### BUILD_PROJECT
```yaml
skill_name: BUILD_PROJECT
type: workflow_skill
permissions: full
description: Build the project
parameters:
  - target: string (optional)
returns: Build output
auto_approve: true
```

#### RUN_TESTS
```yaml
skill_name: RUN_TESTS
type: workflow_skill
permissions: full
description: Execute test suite
parameters:
  - pattern: string (optional)
  - coverage: boolean (optional)
returns: Test results
auto_approve: true
```

#### LINT_CHECK
```yaml
skill_name: LINT_CHECK
type: workflow_skill
permissions: full
description: Run linting on codebase
parameters:
  - fix: boolean (optional)
returns: Lint results
auto_approve: true
```

### 8. Metacognition Skills

#### MCL_MONITOR
```yaml
skill_name: MCL_MONITOR
type: metacognitive_skill
permissions: full
description: Generate mental state snapshot
parameters:
  - task: string (required)
  - step: string (required)
returns: Mental state snapshot
auto_approve: true
```

#### MCL_CRITIQUE
```yaml
skill_name: MCL_CRITIQUE
type: metacognitive_skill
permissions: full
description: Critique output against requirements
parameters:
  - output: string (required)
  - requirements: string (required)
returns: Critique report
auto_approve: true
```

#### MCL_GATE
```yaml
skill_name: MCL_GATE
type: metacognitive_skill
permissions: full
description: Decision gate for significant actions
parameters:
  - action: string (required)
  - context: string (required)
returns: Go/no-go decision
auto_approve: true
```

### 9. Documentation Skills

#### GENERATE_DOCS
```yaml
skill_name: GENERATE_DOCS
type: workflow_skill
permissions: full
description: Generate documentation from code
parameters:
  - source: string (required)
  - format: markdown|html|jsdoc
returns: Generated documentation
auto_approve: true
```

#### UPDATE_README
```yaml
skill_name: UPDATE_README
type: workflow_skill
permissions: full
description: Update project README
parameters:
  - sections: array (required)
returns: Updated README
auto_approve: true
```

### 10. Analysis Skills

#### CODE_REVIEW
```yaml
skill_name: CODE_REVIEW
type: workflow_skill
permissions: full
description: Comprehensive code review
parameters:
  - files: array (required)
  - focus: security|performance|quality|all
returns: Review report
auto_approve: true
```

#### SECURITY_SCAN
```yaml
skill_name: SECURITY_SCAN
type: workflow_skill
permissions: full
description: Scan for security vulnerabilities
parameters:
  - target: string (required)
returns: Security report
auto_approve: true
```

#### PERFORMANCE_PROFILE
```yaml
skill_name: PERFORMANCE_PROFILE
type: workflow_skill
permissions: full
description: Profile code performance
parameters:
  - target: string (required)
returns: Performance report
auto_approve: true
```

### 11. iOS/macOS App Development Skills

#### IOS_APP_CREATE
```yaml
skill_name: IOS_APP_CREATE
type: workflow_skill
permissions: full
description: Create complete iOS/macOS app from zero-shot prompt or user idea
parameters:
  - idea: string (required) - App concept or detailed requirements
  - platform: ios|macos|both|visionos|watchos (default: ios)
  - architecture: mvvm|tca|clean (default: mvvm)
  - min_ios_version: string (default: "17.0")
  - features: array (optional) - Specific features to include
  - ui_style: modern|classic|minimal (default: modern)
returns: Complete Xcode project structure with all source files
auto_approve: true
workflow:
  - ANALYZE_REQUIREMENTS
  - DESIGN_ARCHITECTURE
  - GENERATE_PROJECT_STRUCTURE
  - IMPLEMENT_MODELS
  - IMPLEMENT_VIEWS
  - IMPLEMENT_VIEWMODELS
  - IMPLEMENT_SERVICES
  - CONFIGURE_INFO_PLIST
  - SETUP_ASSETS
  - GENERATE_TESTS
```

#### IOS_APP_SCAFFOLD
```yaml
skill_name: IOS_APP_SCAFFOLD
type: workflow_skill
permissions: full
description: Generate initial Xcode project structure and boilerplate
parameters:
  - app_name: string (required)
  - bundle_id: string (required)
  - platform: ios|macos|both|visionos|watchos (required)
  - architecture: mvvm|tca|clean (default: mvvm)
  - include_tests: boolean (default: true)
  - include_ui_tests: boolean (default: true)
returns: Xcode project directory structure
auto_approve: true
```

#### SWIFTUI_VIEW_GENERATE
```yaml
skill_name: SWIFTUI_VIEW_GENERATE
type: tool_skill
permissions: full
description: Generate SwiftUI views from requirements or wireframes
parameters:
  - requirements: string (required)
  - view_name: string (required)
  - state_management: state|binding|observable|environment (default: observable)
  - accessibility: boolean (default: true)
  - animations: boolean (default: true)
returns: Complete SwiftUI view file
auto_approve: true
```

#### SWIFT_MODEL_GENERATE
```yaml
skill_name: SWIFT_MODEL_GENERATE
type: tool_skill
permissions: full
description: Generate Swift data models with Codable, SwiftData support
parameters:
  - schema: object (required) - Data structure definition
  - persistence: swiftdata|coredata|none (default: swiftdata)
  - codable: boolean (default: true)
  - equatable: boolean (default: true)
returns: Swift model files
auto_approve: true
```

#### TESTFLIGHT_PREPARE
```yaml
skill_name: TESTFLIGHT_PREPARE
type: workflow_skill
permissions: full
description: Prepare app for TestFlight submission
parameters:
  - project_path: string (required)
  - version: string (required)
  - build_number: string (required)
  - release_notes: string (required)
  - testers: internal|external|both (default: internal)
returns: Build preparation report and archive
workflow:
  - VALIDATE_PROJECT
  - INCREMENT_BUILD
  - UPDATE_RELEASE_NOTES
  - ARCHIVE_BUILD
  - VALIDATE_ARCHIVE
auto_approve: true
```

#### TESTFLIGHT_PUBLISH
```yaml
skill_name: TESTFLIGHT_PUBLISH
type: workflow_skill
permissions: full
description: Submit app to TestFlight for distribution
parameters:
  - archive_path: string (required)
  - api_key_id: string (required) - App Store Connect API Key ID
  - issuer_id: string (required) - App Store Connect Issuer ID
  - key_path: string (required) - Path to .p8 private key
  - groups: array (optional) - TestFlight tester groups
  - auto_distribute: boolean (default: true)
returns: TestFlight submission result with build URL
workflow:
  - AUTHENTICATE_ASC
  - UPLOAD_BUILD
  - WAIT_PROCESSING
  - ADD_TESTERS
  - SUBMIT_REVIEW (if external)
auto_approve: true
```

#### APP_STORE_CONNECT_AUTH
```yaml
skill_name: APP_STORE_CONNECT_AUTH
type: tool_skill
permissions: full
description: Authenticate with App Store Connect API
parameters:
  - api_key_id: string (required)
  - issuer_id: string (required)
  - key_path: string (required)
returns: JWT token for API access
auto_approve: true
```

#### XCODE_BUILD
```yaml
skill_name: XCODE_BUILD
type: tool_skill
permissions: full
description: Build Xcode project using xcodebuild
parameters:
  - project_path: string (required)
  - scheme: string (required)
  - configuration: debug|release (default: release)
  - destination: string (optional) - Build destination
  - archive: boolean (default: false)
  - archive_path: string (optional)
returns: Build output and result
auto_approve: true
```

#### XCODE_TEST
```yaml
skill_name: XCODE_TEST
type: tool_skill
permissions: full
description: Run Xcode tests
parameters:
  - project_path: string (required)
  - scheme: string (required)
  - destination: string (default: "platform=iOS Simulator,name=iPhone 15 Pro")
  - coverage: boolean (default: true)
returns: Test results with coverage report
auto_approve: true
```

#### APP_ICON_GENERATE
```yaml
skill_name: APP_ICON_GENERATE
type: tool_skill
permissions: full
description: Generate app icon assets for all required sizes
parameters:
  - source_image: string (required) - Path to 1024x1024 source image
  - output_path: string (required) - Assets.xcassets path
  - platform: ios|macos|both (default: both)
returns: AppIcon.appiconset with all sizes
auto_approve: true
```

#### PROVISIONING_SETUP
```yaml
skill_name: PROVISIONING_SETUP
type: workflow_skill
permissions: full
description: Configure signing and provisioning profiles
parameters:
  - bundle_id: string (required)
  - team_id: string (required)
  - profile_type: development|adhoc|appstore (required)
  - auto_manage: boolean (default: true)
returns: Signing configuration
auto_approve: true
```

### 12. End-to-End App Workflows

#### ZERO_SHOT_APP
```yaml
skill_name: ZERO_SHOT_APP
type: workflow_skill
permissions: full
description: Create complete app from single natural language prompt
parameters:
  - prompt: string (required) - Natural language app description
  - platform: ios|macos|both (default: ios)
  - publish: boolean (default: false) - Auto-publish to TestFlight
returns: Complete working app with optional TestFlight submission
workflow:
  - ANALYZE_PROMPT → Extract requirements, features, data models
  - DESIGN_UI → Generate wireframes and view hierarchy
  - SCAFFOLD_PROJECT → Create Xcode project structure
  - GENERATE_MODELS → Create Swift data models
  - GENERATE_VIEWS → Create SwiftUI views
  - GENERATE_VIEWMODELS → Create view models and logic
  - GENERATE_SERVICES → Create networking/persistence services
  - INTEGRATE_COMPONENTS → Wire everything together
  - GENERATE_TESTS → Create unit and UI tests
  - BUILD_VERIFY → Build and run tests
  - PUBLISH_TESTFLIGHT (if publish: true)
auto_approve: true
```

#### IDEA_TO_TESTFLIGHT
```yaml
skill_name: IDEA_TO_TESTFLIGHT
type: workflow_skill
permissions: full
description: Complete pipeline from idea to TestFlight distribution
parameters:
  - idea: string (required) - App idea in natural language
  - platform: ios|macos (required)
  - team_id: string (required) - Apple Developer Team ID
  - api_credentials: object (required) - App Store Connect API credentials
  - tester_groups: array (optional) - TestFlight groups to notify
  - version: string (default: "1.0.0")
returns: TestFlight build URL and distribution status
workflow:
  - ZERO_SHOT_APP
  - TESTFLIGHT_PREPARE
  - TESTFLIGHT_PUBLISH
auto_approve: true
```

## Skill Composition

Skills can be composed for complex operations:

### Example: Full CI/CD Pipeline
```yaml
workflow: ci_cd_pipeline
steps:
  - LINT_CHECK: { fix: false }
  - RUN_TESTS: { coverage: true }
  - SECURITY_SCAN: { target: "." }
  - BUILD_PROJECT: { target: "production" }
  - GIT_COMMIT: { message: "Build: Production release" }
  - GIT_PUSH: { branch: "main" }
```

### Example: Code Quality Check
```yaml
workflow: quality_check
steps:
  - MCL_MONITOR: { task: "quality_check", step: "init" }
  - CODE_REVIEW: { files: ["src/**"], focus: "all" }
  - MCL_CRITIQUE: { output: "$CODE_REVIEW_RESULT", requirements: "quality_standards" }
  - MCL_GATE: { action: "approve", context: "$CRITIQUE_RESULT" }
```

### Example: iOS App from Idea to TestFlight
```yaml
workflow: idea_to_testflight
steps:
  - MCL_MONITOR: { task: "app_creation", step: "init" }
  - ZERO_SHOT_APP:
      prompt: "$USER_IDEA"
      platform: "ios"
      publish: false
  - MCL_CRITIQUE: { output: "$APP_RESULT", requirements: "ios_best_practices" }
  - XCODE_TEST:
      project_path: "$PROJECT_PATH"
      scheme: "$SCHEME"
      coverage: true
  - MCL_GATE: { action: "publish", context: "$TEST_RESULTS" }
  - TESTFLIGHT_PREPARE:
      project_path: "$PROJECT_PATH"
      version: "1.0.0"
      build_number: "1"
      release_notes: "$GENERATED_NOTES"
  - TESTFLIGHT_PUBLISH:
      archive_path: "$ARCHIVE_PATH"
      api_key_id: "$API_KEY"
      issuer_id: "$ISSUER_ID"
      key_path: "$KEY_PATH"
```

### Example: Zero-Shot SwiftUI App
```yaml
workflow: zero_shot_swiftui
steps:
  - ANALYZE_PROMPT: { prompt: "$USER_PROMPT", extract: ["features", "models", "views"] }
  - IOS_APP_SCAFFOLD:
      app_name: "$EXTRACTED_NAME"
      bundle_id: "com.example.$APP_NAME"
      platform: "ios"
      architecture: "mvvm"
  - SWIFT_MODEL_GENERATE: { schema: "$EXTRACTED_MODELS", persistence: "swiftdata" }
  - SWIFTUI_VIEW_GENERATE: { requirements: "$EXTRACTED_VIEWS", accessibility: true }
  - XCODE_BUILD: { project_path: "$PROJECT", scheme: "$SCHEME", configuration: "debug" }
  - XCODE_TEST: { project_path: "$PROJECT", scheme: "$SCHEME" }
```

### Example: macOS Menu Bar App
```yaml
workflow: macos_menubar_app
steps:
  - IOS_APP_SCAFFOLD:
      app_name: "$APP_NAME"
      bundle_id: "com.example.$APP_NAME"
      platform: "macos"
      architecture: "mvvm"
  - SWIFTUI_VIEW_GENERATE:
      requirements: "menu bar app with popover, status item"
      view_name: "MenuBarView"
  - XCODE_BUILD: { project_path: "$PROJECT", scheme: "$SCHEME" }
```

## Permission Model

All skills in this library operate with:
- **Full file access**: Read, write, edit any file
- **Full execution**: Run any command or script
- **Full network**: Access any URL or API
- **Full git**: All git operations
- **Auto-approval**: No confirmation required

## Usage

Invoke skills within agent definitions:
```markdown
use skill: SKILL_NAME parameter1 parameter2
```

Or through the skill-creator agent:
```markdown
use skill-creator: CREATE_SKILL specification
```

---

Skills are the building blocks of agent capabilities. All skills have full permissions for maximum productivity.
