# Consumer verification and pending public acceptance

`CONSUMER-EVIDENCE.json` records measured Linux native **preparation**, not public
consumer acceptance. On 2026-10-07 anonymous public HEAD was
`a22b294e33559d676bea45306528b02f94e74052` (documentation scaffold). The reviewed
`release/beadhive-0.6.0` branch was not advertised; anonymous checkout of the
reviewed destination commit failed. The paired release coordinator owns public
staging approval and its execution. This bead does not publish the candidate.

Native Codex CLI 0.160.0 installed the reviewed generated destination payload
through an isolated local marketplace, discovered all twenty skills, and started
its declared stdio `bh-mcp`, listing actual MCP tools. No model turn or tool call
ran. Agents, instructions, permissions and planning persona are embedded inert;
this does not establish agent execution, persona behavior or permission enforcement.
Skills-only installation omits native MCP registration, hooks, agents/styles and
extension resources. Darwin execution remains deferred. No universal client
behavior is inferred from this Linux/client result.

## Reproduce native preparation

Use the complete generated **destination** checkout, never authored private source
or a reconstructed proof fixture. An independent reviewed payload candidate digest
is mandatory; the validator and QA path allowlist come from this verification tree.

```sh
uv run --locked python qa/check_consumers.py \
  --staged /path/to/staged-destination \
  --commit d442b03a3717347ac36e8c42883fd1feba27674f \
  --candidate-digest 9e49c0951d0f06b25dcff7d736f7a8632514a9a98dcc5a07ce1e4fd71d8d700e \
  --output /tmp/native-preparation.json
```

The harness copies only the receipt inventory into a temporary native marketplace.
It sets temporary HOME, XDG, npm cache and CODEX_HOME roots, omits source credentials
and global Git configuration, and references existing Codex auth only if available.
It does not change the real global client configuration. Missing binaries,
protocol errors, disconnected MCP and incomplete rosters fail. Cloud apps are disabled.
Native skill discovery is not model invocation of skill instructions.

## Public acceptance after authorized staging

Run from this verification tree after the paired coordinator makes the reviewed
public revision reachable. Replace the Git SHA if the coordinator stages a revised
transport; retain the externally approved payload candidate digest only if the
payload is unchanged. Use a new evidence output path for each attempt: failures
exit nonzero and do not produce a success report.

```sh
uv run --locked python qa/check_consumers.py \
  --commit d442b03a3717347ac36e8c42883fd1feba27674f \
  --candidate-digest 9e49c0951d0f06b25dcff7d736f7a8632514a9a98dcc5a07ce1e4fd71d8d700e \
  --output /tmp/public-consumers.json
```

Without `--staged`, the harness anonymously clones the fixed public repository,
checks out the exact SHA, validates its full inventory/receipt, then calls real
`skills@1.7.0` against the **remote URL at that SHA** for discovery, all twenty
singles, transitive required/reference sets, the nine documented mode sets and the
complete corpus. Identical sets share an installation while preserving every
request in evidence. It compares every installed support file, metadata, script,
document, license and executable mode with the verified public payload. Each run
uses project-only `--agent claude-code --copy -y` installs; no `--global` is used.
Single installs record missing companions; CLI success does not imply closure.
The public-generated COMPANIONS.md files supply the dependency/mode graph; the
harness does not clone or require canonical private metadata.

Representative manual consumer commands (substitute the reviewed public SHA):

```sh
npm exec --yes --package=skills@1.7.0 -- skills --version
npm exec --yes --package=skills@1.7.0 -- skills add \
  https://github.com/beadhive/agent-plugin/tree/REVIEWED_SHA --list
npm exec --yes --package=skills@1.7.0 -- skills add \
  https://github.com/beadhive/agent-plugin/tree/REVIEWED_SHA \
  --skill developer work --agent claude-code --copy -y
```

Run manual commands in a disposable project with isolated home/config/cache roots
as the harness does. The CLI does not resolve companions, install external
providers/runtimes, configure MCP or grant role authority.

## Paired gate handoff

The evidence pins destination Git SHA, release/pack 0.6.0, canonical source SHA,
Hitch revision, payload candidate digest and payload digest. The bundle digest and
QA base commit accompany the measured staged result. Public acceptance, public
release commit and both destinations' ownership approval remain pending.
The coordinator must collect the successful **public** report and the paired
Claude outcome before completing release acceptance or switching contribution,
version or ownership notices. This report authorizes no notice changes.
Adding these destination QA files changes the reviewed QA snapshot; the coordinator
must separately review and repin any promotion plan that includes them. Existing
staged candidates and promotion state are not edited by this bead.

Packaging references: [Agent Plugins 1.0.0](https://agent-plugins.org/),
[skills CLI](https://github.com/vercel-labs/skills), and
[official OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins).
These documents explain formats; measured versions/results above establish this
probe's limited runtime claims.
