# Permission metadata

Agent-specific `permission_json` preserves declared role intent. [policy.yaml](policy.yaml)
retains the Hitch classification/default-ask policy. Mutating `bh.work-claim` and
`bh.work-submit` decisions are tightened from `allow` to `ask`.

These resources are inert metadata in the Agent Plugins extension. Claude does not
emit the neutral policy; its native tools declarations are target-specific projection.
Bundling neither activates a policy nor grants client permissions. Enforcement and
role authorization require separate host/runtime evidence.
