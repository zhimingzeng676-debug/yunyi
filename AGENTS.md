# Agentic SDLC and Spec-Driven Development

Kiro-style Spec-Driven Development on an agentic SDLC

## Project Memory
Project memory keeps persistent guidance (steering, specs notes, component docs) so Codex honors your standards each run. Treat it as the long-lived source of truth for patterns, conventions, and decisions.

- Use `.kiro/steering/` for project-wide policies: architecture principles, naming schemes, security constraints, tech stack decisions, api standards, etc.
- Use local `AGENTS.md` files for feature or library context (e.g. `src/lib/payments/AGENTS.md`): describe domain assumptions, API contracts, or testing conventions specific to that folder. Codex auto-loads these when working in the matching path.
- Specs notes stay with each spec (under `.kiro/specs/`) to guide specification-level workflows.

## Project Context

### Paths
- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications
- Check `.kiro/specs/` for active specifications
- Use `$kiro-spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, generate responses in Simplified Chinese. All Markdown content written to project files (e.g., requirements.md, design.md, tasks.md, research.md, validation reports) MUST be written in the target language configured for this specification (see spec.json.language).

## Minimal Workflow
- Phase 0 (optional): `$kiro-steering`, `$kiro-steering-custom`
- Discovery: `$kiro-discovery "idea"` — determines action path, writes brief.md + roadmap.md for multi-spec projects
- Phase 1 (Specification):
  - Single spec: `$kiro-spec-quick {feature} [--auto]` or step by step:
    - `$kiro-spec-init "description"`
    - `$kiro-spec-requirements {feature}`
    - `$kiro-validate-gap {feature}` (optional: for existing codebase)
    - `$kiro-spec-design {feature} [-y]`
    - `$kiro-validate-design {feature}` (optional: design review)
    - `$kiro-spec-tasks {feature} [-y]`
  - Multi-spec: `$kiro-spec-batch` — creates all specs from roadmap.md in parallel by dependency wave
- Phase 2 (Implementation): `$kiro-impl {feature} [tasks] [--review required|inline|off]`
  - Without task numbers: autonomous mode (subagent per task + independent review + final validation)
  - With task numbers: manual mode (selected tasks in main context, still reviewer-gated before completion)
  - `--review off` skips task-local review; use it intentionally and keep `$kiro-validate-impl {feature}` as the final quality gate
  - `$kiro-validate-impl {feature}` (standalone re-validation)
- Progress check: `$kiro-spec-status {feature}` (use anytime)

## Skills Structure
Skills are located in `.agents/skills/kiro-*/SKILL.md`
- Each skill is a directory with a `SKILL.md` file
- Use `/skills` to inspect currently available skills
- Invoke a skill directly with `$kiro-<skill-name>`
- `kiro-review` — task-local adversarial review protocol used by reviewer subagents
- `kiro-debug` — root-cause-first debug protocol used by debugger subagents
- `kiro-verify-completion` — fresh-evidence gate before success or completion claims
- Use skills explicitly requested by the user and skills relevant to the task's domain, including design, accessibility, and UX.
- Select skills from their descriptions or metadata first, then read only the selected skills and the references needed for the task.
- Follow explicit host and project rules and retain required workflow checks. Do not skip relevant skills just because the task is small.

## Subagents

Current Codex releases enable subagents by default. Use the available tools when the user, project rules, or this skill's workflow calls for delegation; no experimental feature flag is required. An administrator or user can disable subagents by setting `enabled = false` under `[agents]` in Codex configuration.

Use a fresh context for each independent implementer or reviewer, passing the task-relevant inputs explicitly. If delegation is unavailable, follow the skill's inline fallback and identify the review as inline. Skill discovery alone does not prove subagent execution or independent review.

## Development Rules
- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- Human review required each phase; use `-y` only for intentional fast-track
- Keep steering current and verify alignment with `$kiro-spec-status`
- Follow the user's instructions precisely, and within that scope act autonomously: gather the necessary context and complete the requested work end-to-end in this run, asking questions only when essential information is missing or the instructions are critically ambiguous.

## Steering Configuration
- For spec and implementation work, load the core steering files below from `.kiro/steering/`. Reuse current context rather than rereading unchanged files.
- Load additional steering only when required by project rules or relevant to the task.
- Default files: `product.md`, `tech.md`, `structure.md`
- Custom files are supported (managed via `$kiro-steering-custom`)

## 本项目执行约束

- 项目名为云驿（yunyi），当前规格目录为yunyi-foundation、yunyi-execution、yunyi-integration。命名迁移与产品行为实现分开提交；旧名仅保留于历史证据及兼容说明。
- 用户要求命名迁移提交后停止汇报；未获逐份规格批准不得进入kiro-impl，也不得把命名迁移批准写入spec的requirements/design/tasks批准字段。

- 始终使用简体中文。Python使用已验conda解释器 `D:/anaconda3/envs/pack311/python.exe`；禁止裸python/python3。
- 用户要求：superpowers贯穿，cc-sdd完整discovery/requirements/design/tasks，依赖先spike，通过后kiro-impl，强制agentic-tdd真实RED；最小闭环之前仅一条串行实现流水线。
- 当前为规格审阅阶段；具体审批以各spec.json为准，不把用户确认discovery路线当作具体行为需求已批准。
- 依赖证据见docs/evidence，.spikes不是产品实现。使用Codex隔离子代理保留测试作者/代码作者信息屏障；原始agentic-tdd脚本需附加真实pytest失败、校验值和审查完整性门禁。
- 上游模型/schema变更回到foundation，禁止下游偷偷改表或重新定义同名契约。
- 不推送、不部署、不修改用户全局Harness配置；不打印秘密。任务结束先运行新鲜验证再宣称完成。
