# beadhive

Canonical Beadhive full corpus validation candidate.

An [Agent Plugins 1.0.0](https://agent-plugins.org) package, generated from a Hitch pack.

Portable components load in any conformant client: skills from `skills/`, MCP servers from `mcp.json`.

Non-portable resources hitch carries live under `io.github.briancripe.agent-hitch/` and the matching `extensions` key in `plugin.json`. Clients that do not implement that namespace ignore both, by specification.
