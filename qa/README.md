# Public destination QA and receipt contract

This repository owns only `qa/destination-owned.json`'s exact QA paths. Canonical
promotion owns the generated root `plugin.json`, `mcp.json`, `skills/`, MIT notices,
README and namespaced embedded resources. Do not hand-edit generated payloads.
`release-receipt.json` is a public, sanitized immutable Hitch candidate sidecar staged
by the canonical adapter. It is excluded from its own payload inventory; QA ownership
is excluded separately. No private source checkout or credentials are used here.

The candidate contract from Hitch ah-qr7z is integer `schemaVersion: 1`, pack,
authoredVersion, releaseVersion, target, full immutable sourceCommit/hitchRevision,
files, payloadDigest, digest. File values are `{sha256, mode}`, with Git modes
`100644`/`100755`. Both digests use SHA-256 over UTF-8 encoded
`json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)`:
payloadDigest hashes files; digest hashes the whole candidate excluding digest.
No URLs, local paths, operational settings or secrets belong in the sidecar.
The public sidecar uses the **payload candidate** that excludes itself. To stage
that sidecar, the canonical adapter creates a separate **publisher candidate**
whose approved files include the sidecar. Their digests intentionally differ.
`--expected-candidate-digest` pins the payload candidate sidecar, not the publisher
candidate or orchestration promotion receipt; the paired release gate verifies
both independently. Hitch does not inject or rewrite the sidecar.

```sh
just check
just accept
uv run --locked python qa/check_artifact.py --artifact /path/to/generated/package \
  --receipt /path/to/public/candidate.json --require-artifact
```

`just check` tests synthetic malformed-artifact controls and can report **preparation
only, acceptance pending** while this documentation scaffold lacks generated output.
Public CI and `just accept` always require actual output and its sidecar; deleting both
cannot downgrade acceptance to a passing preparation check. The preparation branch
therefore awaits full canonical staging before public CI can pass. No candidate release
has been allocated by this QA bead.

Validation freezes the official Agent Plugins 1.0.0 schemas offline, checks exact
inventory hashes/modes, contained root/resources/Markdown/guide references, the complete
20-skill/11-agent roster, copy-preserved companions/support, exact root/leaf MIT notices,
native `bh-mcp`, and explicit extension capability mapping. Unexpected paths, symlinks,
private source/cache paths, operational local path/key residue, duplicate metadata and
unreviewed native skill frontmatter fail. Existing standard `allowed-tools`/guide metadata
is preserved as declared information; this gate does not establish host enforcement.

The native surfaces are plugin, skills and MCP. The namespaced agents, instructions,
permissions and planning persona are **embedded inert**. Schema validity and contained
bundling do not establish live model behavior or permission enforcement. Authenticated
public-client acceptance is separately gated (`bh-ap-exc`). Receipts establish byte/mode
agreement with an approved canonical candidate; they are not cryptographic proof of
source regeneration. A recomputed self-consistent receipt is not immutable provenance.
The paired release gate independently pins candidate digest and source/compiler/version
identity; callers can pass `--expected-candidate-digest <reviewed-sha256>` to reject a
replacement payload with a re-signed receipt, without accessing private source. Public
default drift checks compare the committed receipt and do not claim cryptographic source
authenticity. The private canonical pipeline retains that regeneration guarantee
and review must authorize the candidate/receipt together. Linux proof fixtures do not
establish Darwin support.

CI installs only locked public Python dependencies. The workflow has read-only contents
permission and never reads canonical source, GitHub source tokens or private clone secrets.
Git-tracked files cannot hide behind local cache/hive exclusions. Fixture generation never
executes bundled runtime scripts. Reviewed upgrades are needed to change corpus/layout,
schemas or extension mapping.

Consumer preparation, pinned public installation commands and the pending public
staging boundary are recorded in [CONSUMERS.md](CONSUMERS.md).
