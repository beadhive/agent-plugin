# beadhive/agent-plugin

Public generated distribution targeting the [Agent Plugins standard](https://agent-plugins.org/).
This initial repository contains documentation only; generated distribution
artifacts will arrive through the subsequent validated migration.

## Migration boundary

`beadhive/skills` will become the canonical authoring source.
`beadhive/agent-plugin` will contain generated public artifacts.
`beadhive/claude-plugin` remains public with hive prefix `bh-cp`; preserve its
existing content and installation coordinates (marketplace `beadhive`, plugin
`bh`). It becomes another generated output target only after migration
validation.

Private source content may be published only through an explicit, reviewed
artifact allowlist. Publication is deny-by-default: never mirror the private
repository or publish unlisted source files, hive data, or supporting resources.
No publication pipeline or allowlist is implemented by this initial scaffold.

Skills migration, agent-hitch implementation, and release automation are
subsequent work.
