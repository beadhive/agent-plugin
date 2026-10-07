#!/usr/bin/env python3
"""Local scaffold QA is explicitly distinct from required public CI acceptance."""
from pathlib import Path
import json
import subprocess
import sys
from check_artifact import ROOT, HOST_PARTS, PRIVATE_PARTS, require


def main():
    manifest=ROOT/'plugin.json'; receipt=ROOT/'release-receipt.json'
    if manifest.exists() or receipt.exists():
        # Reuse the public CLI's sanitized schema/YAML/JSON diagnostics. Never
        # let exception formatting echo malformed payload data in local checks.
        result=subprocess.run([sys.executable,str(ROOT/'qa/check_artifact.py'),'--artifact',str(ROOT),'--receipt',str(receipt),'--destination','--require-artifact'])
        raise SystemExit(result.returncode)
    else:
        owned=set(json.loads((ROOT/'qa/destination-owned.json').read_text())['files'])
        allowed=owned|{'README.md','CONTRIBUTING.md','.gitignore'}
        files={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and not any(part in HOST_PARTS for part in p.relative_to(ROOT).parts)}
        tracked=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z'],text=True).split('\0')
        require(not any(any(part in PRIVATE_PARTS for part in Path(name).parts) for name in tracked if name and name not in owned),'Tracked private residue in preparation stage')
        require(files<=allowed,'Unexpected unreceipted files in preparation stage: '+str(sorted(files-allowed)))
        print('PREPARATION QA ONLY: no generated artifact or release receipt; public acceptance pending')


if __name__=='__main__': main()
