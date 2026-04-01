# Dev Charter

> **This is the reference (English) version.**
> For the canonical (Japanese) version, see [README-jp.md](README-jp.md).

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)

Shared development charter for AI-assisted software projects.

This repository defines common philosophy, architecture principles,
and development rules used across projects.

## Documents

| File | Description |
|---|---|
| [PRINCIPLES.md](PRINCIPLES.md) | Development philosophy, design and architecture principles |
| [CODE_STYLE.md](CODE_STYLE.md) | Code style guide |
| [AI_COLLABORATION_RULES.md](AI_COLLABORATION_RULES.md) | AI collaboration rules and role assignments |
| [AI_CONTEXT_HIERARCHY.md](AI_CONTEXT_HIERARCHY.md) | AI context priority hierarchy |
| [AI_TOOL_SETUP.md](AI_TOOL_SETUP.md) | AI context file structure spec (AI_CONTEXT.md and agent config files) |
| [LANGUAGE_POLICY.md](LANGUAGE_POLICY.md) | Language policy (canonical = Japanese) |
| [LOCALIZATION_POLICY.md](LOCALIZATION_POLICY.md) | Localization and supported languages |
| [PROJECT_LIFECYCLE.md](PROJECT_LIFECYCLE.md) | Project lifecycle and team structure |
| [UI_GUIDELINES.md](UI_GUIDELINES.md) | UI guidelines, color palette, iconography |
| [MONETIZATION_POLICY.md](MONETIZATION_POLICY.md) | Monetization policy and platform-specific guidelines |
| [SECURITY_POLICY.md](SECURITY_POLICY.md) | Security policy and hook configuration reference |
| [LEGAL_POLICY.md](LEGAL_POLICY.md) | License selection criteria and templates (Closed / MIT / AGPL·GPL·LGPL) |
| [topics/CI_POLICY.md](topics/CI_POLICY.md) | CI job design and Branch Protection Ruleset |
| [topics/GITHUB_SETTINGS.md](topics/GITHUB_SETTINGS.md) | GitHub repository settings review (Ruleset, Sponsors) |
| [topics/GITHUB_CONTRIBUTING.md](topics/GITHUB_CONTRIBUTING.md) | Issue, PR, CONTRIBUTING.md, PR template, and Quasi-CLA (for OSS) |
| [topics/TEMPLATE_README_GUIDELINES.md](topics/TEMPLATE_README_GUIDELINES.md) | GitHub template repository README guidelines (environment, language, LICENSE, required sections) |
| [topics/PROJECT_README_GUIDELINES.md](topics/PROJECT_README_GUIDELINES.md) | README setup guide for projects created from a template |

## How to Use

1. Pull dev-charter into `docs/dev-charter/` via `git subtree`
2. Have the AI read the charter and generate `AI_CONTEXT.md` and agent config files at the project root
3. After charter updates, run `git subtree pull` and have the AI sync the context files

See [AI_TOOL_SETUP.md](AI_TOOL_SETUP.md) for the structure spec.

## Install (git subtree)

```
git remote add dev-charter https://github.com/y-marui/dev-charter
git fetch dev-charter
git subtree add --prefix=docs/dev-charter dev-charter main --squash
```

After installing, paste the following prompt into your AI tool:

```
Read all files in docs/dev-charter/, explore this project, then do the following:

1. Set up AI context files following the spec in docs/dev-charter/AI_TOOL_SETUP.md
2. Compare the project against charter requirements and fix any gaps
   (e.g., missing CI jobs, security hooks not configured, missing CONTRIBUTING.md)
   For large-scope changes, confirm with the user before proceeding

- If you have questions or ambiguities, ask all of them at once before starting
- If the charter conflicts with existing conventions, list the conflicts and confirm priority with the user before proceeding
- Do not commit after completing (let the user review first)
```

## Update

If the `dev-charter` remote is not set up (e.g., after cloning the project), add it first:

```
git remote add dev-charter https://github.com/y-marui/dev-charter
```

```
git subtree pull --prefix=docs/dev-charter dev-charter main --squash
```

After updating, paste the following prompt into your AI tool:

```
Read all files in docs/dev-charter/ and update only what is affected by charter changes:

1. Update AI context files following the spec in docs/dev-charter/AI_TOOL_SETUP.md
2. If charter changes affect project files (CI config, security hooks, etc.), fix them too

- No need to re-explore the entire project
- If AI_CONTEXT.md does not exist, use the install prompt instead
- If a charter change conflicts with a project-specific rule, list the conflicts and confirm priority with the user
- Do not commit after completing (let the user review first)
```

## Makefile helper

```
update-charter:
	git subtree pull --prefix=docs/dev-charter dev-charter main --squash
```

---

*This document has a Japanese canonical version [README-jp.md](README-jp.md). Update both in the same commit when editing.*
