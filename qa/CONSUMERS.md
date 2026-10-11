# Consumer verification and AGF main delivery

`CONSUMER-EVIDENCE.json` preserves the historical Linux native preparation result
from Codex 0.160.0. It establishes no public consumer acceptance. The current
0.6.0 delivery uses independently reviewed AGF main integration: local checks,
submission, approval, molecule finish, then origin-main push. No release branch
or pull request is required. Public installation acceptance remains separately
tracked by **Verify public skills installation and native Agent Plugins loading
(`bh-ap-exc`)** after the reviewed main is publicly reachable.

## Best-effort local preparation

From this QA tree, supply the complete committed generated destination and exact
commit. The independently reviewed immutable payload candidate digest is
`9e49c0951d0f06b25dcff7d736f7a8632514a9a98dcc5a07ce1e4fd71d8d700e`.

```sh
uv run --locked python qa/check_consumers.py \
  --staged /path/to/committed-destination --commit EXACT_COMMITTED_SHA \
  --candidate-digest 9e49c0951d0f06b25dcff7d736f7a8632514a9a98dcc5a07ce1e4fd71d8d700e \
  --output /tmp/local-consumers.json
```

Both modes run real `skills@1.7.0` discovery, all twenty single installs,
transitive required/reference sets, nine documented mode sets and the complete
corpus. Identical sets share installations while preserving every request in
evidence. Local mode passes the validated checkout path to the CLI; public mode
passes the GitHub URL at the exact SHA. Every installed support file, metadata,
script, document, license and executable mode must match the verified payload.
Single installs record missing companions; the installer does not resolve them.
Project-only `--agent claude-code --copy -y` installs use temporary HOME, XDG,
npm cache and CODEX_HOME roots, no global Git configuration or source credentials.
No real client configuration is modified.

Native Codex loading uses an isolated local marketplace adapter containing only
receipt-listed bytes from the verified destination. The harness measures actual
client version, all twenty skill names, plugin enablement, declared stdio
`bh-mcp` startup and tool listing. Existing authorized Codex authentication is
referenced only when available. No model turns or MCP tool calls run. Agents,
instructions, permissions and planning persona are embedded inert: no execution,
persona behavior or permission enforcement is established. Darwin execution is
deferred. Neither adapter loading nor schema conformance establishes direct native
public catalog installation or universal client compatibility. Skills-only installs
omit native MCP registration, hooks, agents/styles and extension resources.

## Public acceptance after main push

Run without `--staged` only after the owning merger finishes AGF delivery and the
coordinator verifies origin main. Substitute the actual publicly fetched main SHA:

```sh
uv run --locked python qa/check_consumers.py --commit PUBLIC_MAIN_SHA \
  --candidate-digest 9e49c0951d0f06b25dcff7d736f7a8632514a9a98dcc5a07ce1e4fd71d8d700e \
  --output /tmp/public-consumers.json
```

The harness anonymously clones the fixed public repository, checks out that exact
SHA and validates the complete immutable inventory/receipt before invoking the
remote-source CLI matrix and native adapter. Failure exits nonzero without a
success report. Local preparation always records `publicAcceptance: pending`.
Public reports pin actual destination SHA, source/compiler identity, release/pack
0.6.0, candidate digest and payload digest; they authorize no ownership change.
The coordinator records actual AGF review gate, approved reviewer, merger, closed
molecule and public-main readback separately from immutable payload provenance.
QA revisions require separately reviewed exact path/hash/mode inventories. The
paired release and rollback gate needs both successful public destination reports
before contribution, version or ownership notices can change.
