#!/usr/bin/env python3
"""Offline public artifact conformance. No source clone, credentials or code execution."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import subprocess
from urllib.parse import unquote, urlsplit

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = 'io.github.briancripe.agent-hitch'
SCHEMA_HASHES = {'plugin.schema.json':'0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883', 'mcp.schema.json':'6539175bfcdf43085855183e86da40ea94b166547a72b47ae9a0a390516d3acb'}
RESOURCES = {'agents','instructions','permissions','personas'}
HOST_PARTS = {'.git','.venv','__pycache__','.beads','.repowise','.bh'}
PRIVATE_PARTS = {'.git','.beads','.bh','.repowise','.venv','.aws','.codex','.claude','resources','schemas','docs','hitch.yaml','hitch.build.yaml','uv.lock','pyproject.toml','skill-dependencies.json'}
SEMVER = r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
EXPECTED_AGENTS = {'analyst','controller','custodian','developer','director','dispatcher','merger','planner','reviewer','supervisor','warden'}
EXPECTED_SKILLS = {'backfill','control','developer','dispatcher','groom','merger','modularize','operator-communication','overview','plan','planner','plugins','refactor','replan','retro','reviewer','setup','setup-git-workspace','triage','work'}


def require(condition, message):
    if not condition: raise ValueError(message)


def unique_pairs(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key]=value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs)


class UniqueLoader(yaml.SafeLoader): pass


def unique_yaml(loader,node,deep=False):
    loader.flatten_mapping(node)
    return unique_pairs([(loader.construct_object(k,deep=deep),loader.construct_object(v,deep=deep)) for k,v in node.value])


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,unique_yaml)


def frontmatter(path):
    text=path.read_text()
    require(text.startswith('---\n') and '\n---\n' in text[4:], 'missing YAML frontmatter: '+path.name)
    data=yaml.load(text.split('---',2)[1],Loader=UniqueLoader)
    require(isinstance(data,dict),'invalid frontmatter')
    return data


def safe_path(name):
    require(isinstance(name,str) and name and '\\' not in name and '\x00' not in name,'invalid artifact path')
    path=PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix()==name and all(p not in {'.','..'} for p in path.parts),'noncontained artifact path')
    return path


def inventory(artifact, excluded=(), ignored_parts=()):
    files={}
    excluded=set(excluded)
    for path in sorted(artifact.rglob('*')):
        name=path.relative_to(artifact).as_posix()
        if any(part in ignored_parts for part in path.relative_to(artifact).parts): continue
        if name in excluded: continue
        require(not path.is_symlink(),'symlink forbidden: '+name)
        if path.is_file():
            safe_path(name)
            require(not any(part in PRIVATE_PARTS for part in PurePosixPath(name).parts),'private source residue: '+name)
            require(PurePosixPath(name).parts[0] in {'plugin.json','mcp.json','README.md','LICENSE','skills',EXTENSION},'unexpected root artifact path: '+name)
            mode='100'+format(path.stat().st_mode & 0o777,'03o')
            require(mode in {'100644','100755'},'unsupported artifact mode: '+name)
            files[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mode':mode}
    require(files,'empty artifact inventory')
    return files


def validate_schemas(plugin,mcp):
    for name in SCHEMA_HASHES:
        path=ROOT/'qa/schemas'/name
        require(hashlib.sha256(path.read_bytes()).hexdigest()==SCHEMA_HASHES[name],'pinned public schema drift: '+name)
        schema=read_json(path)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(plugin if name.startswith('plugin') else mcp)


def local_references(artifact, files):
    for name in files:
        if not name.endswith('.md'): continue
        path=artifact/name
        text=path.read_text()
        for raw in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"\n]*")?\)',text):
            raw=raw.strip('<>')
            parsed=urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path: continue
            target=path.parent/unquote(parsed.path)
            require(not Path(unquote(parsed.path)).is_absolute(),'absolute reference: '+path.name)
            require(target.resolve().is_relative_to(artifact.resolve()),'escaping reference: '+path.name)
            require(target.exists(),'missing support/reference: '+path.name)


def validate_extensions(plugin,artifact):
    require(set(plugin.get('extensions',{}))=={EXTENSION},'unreviewed extension namespace')
    extension=plugin['extensions'][EXTENSION]
    require(extension.get('version')==1,'unsupported extension version')
    require(set(extension.get('resources',{}))==RESOURCES,'extension capability declarations incomplete')
    for kind,path in extension['resources'].items():
        require(path=='./'+EXTENSION+'/'+kind,'noncontained extension resource declaration')
        require((artifact/path).is_dir(),'missing declared extension resources')
    agents=extension.get('agents',[])
    require({row.get('name') for row in agents}==EXPECTED_AGENTS and len(agents)==len(EXPECTED_AGENTS),'agent capability roster drift')
    require(all(set(row)=={'name','tier'} and row['tier'] in {'default','deep'} for row in agents),'agent tier metadata malformed')
    for name in EXPECTED_AGENTS:
        path=artifact/EXTENSION/'agents'/(name+'.md')
        require(path.is_file(),'missing embedded agent')
        require(isinstance(frontmatter(path).get('description'),str),'agent description missing')
    expected={f'agents/{name}.md' for name in EXPECTED_AGENTS}|{'instructions/AGENTS.md','instructions/README.md','instructions/OPERATOR-COMMUNICATION.md','permissions/policy.yaml','permissions/README.md','personas/SOUL.md'}
    actual={p.relative_to(artifact/EXTENSION).as_posix() for p in (artifact/EXTENSION).rglob('*') if p.is_file()}
    require(actual==expected,'embedded extension artifact roster drift')
    mapping=read_json(ROOT/'qa/capabilities.json')
    require(mapping['native']==['plugin','skills','mcp'],'native capability claims drift')
    require(mapping['embeddedInert']==['agents','instructions','permissions','personas'],'inert capability claims drift')
    require(mapping['runtimeEnforcementClaimed'] is False,'false runtime enforcement claim')


def validate_skills(artifact,plugin):
    root=artifact/'skills'
    require(root.is_dir(),'root skills layout missing')
    names={p.name for p in root.iterdir() if p.is_dir()}
    require(names==EXPECTED_SKILLS,'full approved skill roster drift')
    license_text=(ROOT/'qa/MIT-LICENSE.txt').read_bytes()
    require((artifact/'LICENSE').read_bytes()==license_text,'root MIT license notice drift')
    require(plugin.get('license')=='MIT','manifest license drift')
    for name in names:
        directory=root/name
        require((directory/'LICENSE').read_bytes()==license_text,'leaf MIT notice missing/drift: '+name)
        require((directory/'COMPANIONS.md').is_file(),'copy-preserved companion metadata missing: '+name)
        value=frontmatter(directory/'SKILL.md')
        require(value.get('name')==name and re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',name) and len(name)<=64,'invalid skill name')
        require(isinstance(value.get('description'),str) and 0<len(value['description'])<=1024,'invalid skill description')
        if 'metadata' in value:
            require(isinstance(value['metadata'],dict),'invalid skill metadata')
            guide=value['metadata'].get('guide')
            if guide is not None:
                require(isinstance(guide,dict) and isinstance(guide.get('entry'),str),'invalid guide support metadata')
                entry=directory/guide['entry']
                require(entry.resolve().is_relative_to(directory.resolve()) and entry.is_file(),'missing/escaping guide support entry')
        for native in ['model','tools','agent','skills','context','disable-model-invocation']:
            require(native not in value,'unportable native skill frontmatter')


def validate(artifact,receipt, destination=False, expected_candidate_digest=None):
    require(artifact.is_dir(),'artifact directory missing')
    require(receipt.is_file(),'required public release-receipt.json missing; artifact acceptance pending')
    candidate=read_json(receipt)
    if expected_candidate_digest is not None:
        require(re.fullmatch('[0-9a-f]{64}',expected_candidate_digest),'expected candidate digest must be full SHA-256')
        require(candidate.get('digest')==expected_candidate_digest,'independently pinned candidate digest mismatch')
    require(set(candidate)=={'schemaVersion','pack','authoredVersion','releaseVersion','target','sourceCommit','hitchRevision','files','payloadDigest','digest'},'candidate contract keys mismatch')
    require(type(candidate['schemaVersion']) is int and candidate['schemaVersion']==1,'unsupported candidate schema version')
    require(candidate['pack']=='beadhive','wrong pack receipt')
    require(all(isinstance(candidate[k],str) and re.fullmatch(SEMVER,candidate[k]) for k in ['authoredVersion','releaseVersion']),'invalid sanitized candidate version')
    require(candidate.get('target')=='agent-plugins','wrong target receipt')
    require(re.fullmatch('[0-9a-f]{40}',candidate.get('sourceCommit','')),'source SHA must be immutable')
    require(re.fullmatch('[0-9a-f]{40}',candidate.get('hitchRevision','')),'compiler SHA must be immutable')
    declared=candidate.get('files')
    require(isinstance(declared,dict) and declared,'missing candidate file inventory')
    for name,details in declared.items():
        safe_path(name)
        require(set(details)=={'sha256','mode'} and re.fullmatch('[0-9a-f]{64}',details['sha256']) and details['mode'] in {'100644','100755'},'invalid candidate inventory entry')
    excluded=[]
    if destination:
        excluded=read_json(ROOT/'qa/destination-owned.json')['files']+['release-receipt.json','.git']
        require(not set(declared)&set(excluded),'payload collides with destination-owned QA')
    elif receipt.is_relative_to(artifact):
        require(receipt.relative_to(artifact).as_posix()=='release-receipt.json','unreviewed payload sidecar path')
        excluded=['release-receipt.json']
    ignored_parts=()
    if destination:
        # Build caches and host-local hive state are not public files. Verify the
        # Git index independently so a tracked private path cannot hide here.
        ignored_parts=HOST_PARTS
        tracked=subprocess.check_output(['git','-C',str(artifact),'ls-files','-z'],text=True).split('\0')
        for name in filter(None,tracked):
            if name in excluded: continue
            require(not any(part in PRIVATE_PARTS or part=='__pycache__' for part in PurePosixPath(name).parts),'tracked private source residue')
    actual=inventory(artifact,excluded,ignored_parts)
    require(actual==declared,'payload inventory, bytes or modes drift')
    payload_digest=hashlib.sha256(json.dumps(declared,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()
    require(candidate.get('payloadDigest')==payload_digest,'candidate payload digest mismatch')
    unsigned={key:value for key,value in candidate.items() if key!='digest'}
    digest=hashlib.sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()
    require(candidate.get('digest')==digest,'immutable candidate receipt digest mismatch')
    plugin=read_json(artifact/'plugin.json'); mcp=read_json(artifact/'mcp.json')
    require(plugin.get('version')==candidate.get('releaseVersion'),'release version/manifest mismatch')
    validate_schemas(plugin,mcp)
    require(mcp.get('mcpServers',{}).get('default')=={'type':'stdio','command':'bh-mcp'},'native bh-mcp descriptor drift')
    for file in actual:
        path=artifact/file
        if path.suffix in {'.md','.json','.yaml','.yml','.sh','.py','.txt'}:
            text=path.read_text()
            require(not re.search(r'(?:/data/bees/|/tmp/bh-|/home/bees/|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',text),'private operational residue in payload')
    validate_extensions(plugin,artifact); validate_skills(artifact,plugin)
    local_references(artifact,actual)
    return {'target':'agent-plugins','files':len(actual),'skills':len(EXPECTED_SKILLS),'sourceCommit':candidate['sourceCommit'],'digest':digest,'extensions':'embedded inert; no host enforcement claim'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--destination',action='store_true')
    parser.add_argument('--expected-candidate-digest',help='Independent reviewed SHA-256 pin; no private source access needed')
    parser.add_argument('--require-artifact',action='store_true',help='Acceptance always requires artifact; explicit CI boundary')
    args=parser.parse_args()
    try:
        result=validate(args.artifact.resolve(),args.receipt.resolve(),args.destination,args.expected_candidate_digest)
    except jsonschema.ValidationError:
        print('Artifact conformance failed: official pinned schema validation',file=sys.stderr);raise SystemExit(1)
    except json.JSONDecodeError as error:
        print(f'Artifact conformance failed: JSON parsing at line {error.lineno}, column {error.colno}',file=sys.stderr);raise SystemExit(1)
    except yaml.YAMLError as error:
        mark=getattr(error,'problem_mark',None)
        location=f' at line {mark.line+1}, column {mark.column+1}' if mark is not None else ''
        print('Artifact conformance failed: YAML parsing'+location,file=sys.stderr);raise SystemExit(1)
    except ValueError as error:
        # Our guards use fixed reasons before ':'. Omit all user file/path detail.
        print('Artifact conformance failed: '+str(error).split(':',1)[0],file=sys.stderr);raise SystemExit(1)
    except (KeyError,TypeError,OSError):
        print('Artifact conformance failed: artifact structure or file access',file=sys.stderr);raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__': main()
