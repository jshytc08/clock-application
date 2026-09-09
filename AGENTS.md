## Verified local commits

After completing an authorized implementation task, commit the verified changes locally without asking again. The user handles pushing to origin.

1. Inspect `git status` and the diff before editing. Preserve unrelated edits and record any pre-existing failures.
2. Add regression coverage for changed behavior. Run `python scripts/check.py` with the project's virtual environment; this is the required implementation release gate. For UI changes, also review the generated desktop/mobile screenshots and affected error states. Documentation-only changes need a content review and whitespace check.
3. Fix failures before committing. If a required check cannot run, report the blocker and leave the implementation uncommitted; never bypass checks or claim missing tests passed.
   When changing dependencies, also run `python -m pip_audit -r requirements.txt` and `npm audit`; resolve reported vulnerabilities before committing.
4. After code changes, refresh graphify as described below. Review the final diff and stage explicit task-related paths or hunks, including relevant tests and documentation. Keep secrets, local environments, and unrelated user changes out of the commit.
5. Create a descriptive local commit for the completed task. Check the resulting commit and working tree; report the hash, checks run, and any remaining changes. If a hook modifies files, review its output and commit relevant generated changes as needed.

Do not push, amend existing commits, rewrite history, or disable hooks unless the user explicitly requests it. An instruction to leave changes uncommitted overrides this workflow.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
