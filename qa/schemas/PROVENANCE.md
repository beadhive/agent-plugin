# Frozen public Agent Plugins 1.0.0 schemas

Copied verbatim from the official versioned identifiers, retrieved 2026-08-09:

- https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
- https://agent-plugins.org/schemas/1.0.0/mcp.schema.json

`check_artifact.py` pins both SHA-256 values and validates offline. The authoritative
specification is https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md.
Clients must not fetch schemas while loading plugins. Update to a new schema/spec version
through review; never edit upstream schemas to accommodate generated output.
