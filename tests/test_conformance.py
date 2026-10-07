"""Deliberate malformed public artifacts must fail even with re-signed inventories."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qa'))
import check_artifact as check


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value)
    path.chmod(0o644)


def fixture(root):
    license_text=(check.ROOT/'qa/MIT-LICENSE.txt').read_text()
    write(root/'LICENSE',license_text)
    write(root/'README.md','# Synthetic validator fixture\n\nNot an allocated release or canonical acceptance.\n')
    extension={'version':1,'resources':{kind:'./'+check.EXTENSION+'/'+kind for kind in check.RESOURCES},'agents':[{'name':name,'tier':'default'} for name in sorted(check.EXPECTED_AGENTS)]}
    write(root/'plugin.json',json.dumps({'$schema':'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json','name':'beadhive','version':'0.0.0-fixture','license':'MIT','extensions':{check.EXTENSION:extension}}))
    write(root/'mcp.json',json.dumps({'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'default':{'type':'stdio','command':'bh-mcp'}}}))
    for name in sorted(check.EXPECTED_SKILLS):
        directory=root/'skills'/name
        write(directory/'SKILL.md',f'---\nname: {name}\ndescription: Synthetic conformance fixture\n---\n\n[Support](references/help.md)\n')
        write(directory/'LICENSE',license_text)
        write(directory/'COMPANIONS.md','# Companions\n\nSynthetic fixture only.\n')
        write(directory/'references/help.md','# Support\n')
    for name in sorted(check.EXPECTED_AGENTS):
        write(root/check.EXTENSION/'agents'/(name+'.md'),'---\ndescription: Synthetic agent\n---\n\nNo runtime authority asserted.\n')
    write(root/check.EXTENSION/'instructions/AGENTS.md','# Inert instructions\n')
    write(root/check.EXTENSION/'permissions/policy.yaml','version: 1\n')
    write(root/check.EXTENSION/'permissions/README.md','# Inert policy\n')
    write(root/check.EXTENSION/'instructions/README.md','# Inert instructions\n')
    write(root/check.EXTENSION/'instructions/OPERATOR-COMMUNICATION.md','# Operator contract fixture\n')
    write(root/check.EXTENSION/'personas/SOUL.md','# Inert planning persona\n')
    write(root/'skills/backfill/scripts/probe.sh','#!/bin/sh\nexit 0\n')
    (root/'skills/backfill/scripts/probe.sh').chmod(0o755)
    return receipt(root)


def receipt(root):
    files=check.inventory(root,excluded=['release-receipt.json'])
    value={'schemaVersion':1,'pack':'beadhive','authoredVersion':'0.0.0','releaseVersion':'0.0.0-fixture','target':'agent-plugins','sourceCommit':'a'*40,'hitchRevision':'b'*40,'files':files,'payloadDigest':digest(files)}
    value['digest']=digest(value)
    write(root/'release-receipt.json',json.dumps(value,indent=2)+'\n')
    return root/'release-receipt.json'


class Conformance(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='public-ap-fixture-')
        self.root=Path(self.temporary.name)
        self.sidecar=fixture(self.root)

    def tearDown(self): self.temporary.cleanup()

    def validate(self): return check.validate(self.root,self.sidecar)

    def resign(self): self.sidecar=receipt(self.root)

    def test_valid_self_contained_fixture(self):
        self.assertEqual(self.validate()['skills'],20)

    def test_local_staged_check_diagnostics_do_not_echo_input(self):
        sentinel='sk-ant-api03-SYNTHETIC_LOCAL_STAGE_DO_NOT_ECHO_1234567890'
        plugin=json.loads((self.root/'plugin.json').read_text());plugin['name']=sentinel
        write(self.root/'plugin.json',json.dumps(plugin));self.resign()
        owned=json.loads((check.ROOT/'qa/destination-owned.json').read_text())['files']
        for name in owned:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(check.ROOT/name,path)
        subprocess.run(['git','init','-q',str(self.root)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True,capture_output=True)
        result=subprocess.run([sys.executable,str(self.root/'qa/check_stage.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('official pinned schema validation',result.stderr)
        self.assertNotIn(sentinel,result.stderr)
        self.assertNotIn(sentinel,result.stdout)
        self.assertNotIn('Traceback',result.stderr)

    def test_cli_metadata_diagnostics_do_not_echo_input(self):
        sentinel='sk-ant-api03-SYNTHETIC_DO_NOT_ECHO_THIS_SENTINEL_1234567890'
        def run_cli():
            result=subprocess.run([sys.executable,str(check.ROOT/'qa/check_artifact.py'),'--artifact',str(self.root),'--receipt',str(self.sidecar)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertNotIn(sentinel,result.stderr)
            self.assertNotIn(sentinel,result.stdout)
            self.assertNotIn('Traceback',result.stderr)
            return result
        plugin=json.loads((self.root/'plugin.json').read_text())
        plugin['name']=sentinel
        write(self.root/'plugin.json',json.dumps(plugin));self.resign()
        self.assertIn('schema validation',run_cli().stderr)
        plugin['name']='beadhive';write(self.root/'plugin.json',json.dumps(plugin))
        (self.root/'skills/plan/SKILL.md').write_text('---\nname: plan\ndescription: ['+sentinel+'\n---\n')
        self.resign()
        self.assertIn('YAML parsing',run_cli().stderr)
        self.sidecar.write_text('{"secret":"'+sentinel+'",invalid}')
        self.assertIn('JSON parsing',run_cli().stderr)

    def test_independent_candidate_pin_rejects_resigned_payload(self):
        pinned=json.loads(self.sidecar.read_text())['digest']
        self.assertEqual(check.validate(self.root,self.sidecar,expected_candidate_digest=pinned)['skills'],20)
        (self.root/'README.md').write_text('Self-consistent replacement payload, not approved candidate')
        self.resign()
        with self.assertRaisesRegex(ValueError,'independently pinned'):check.validate(self.root,self.sidecar,expected_candidate_digest=pinned)

    def test_byte_drift(self):
        (self.root/'README.md').write_text('changed')
        with self.assertRaisesRegex(ValueError,'drift'): self.validate()

    def test_executable_mode_drift(self):
        (self.root/'skills/backfill/scripts/probe.sh').chmod(0o644)
        with self.assertRaisesRegex(ValueError,'drift'): self.validate()

    def test_missing_support(self):
        (self.root/'skills/plan/references/help.md').unlink();self.resign()
        with self.assertRaisesRegex(ValueError,'support/reference'): self.validate()

    def test_containment(self):
        for target in ['../../../../secret','/etc/passwd','references/%2e%2e/%2e%2e/%2e%2e/%2e%2e/secret']:
            with self.subTest(target=target):
                path=self.root/'skills/plan/SKILL.md'
                path.write_text('---\nname: plan\ndescription: valid\n---\n\n[bad]('+target+')\n');self.resign()
                with self.assertRaises(ValueError): self.validate()

    def test_symlink(self):
        (self.root/'skills/plan/link').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'symlink'): self.validate()

    def test_private_residue_paths(self):
        for path in ['.beads/issues.jsonl','hitch.yaml','resources/private.md','skills/plan/.aws/credentials']:
            with self.subTest(path=path):
                write(self.root/path,'private')
                with self.assertRaisesRegex(ValueError,'private source residue'): self.validate()
                (self.root/path).unlink()

    def test_private_residue_text(self):
        (self.root/'README.md').write_text('/data/bees/beadhive/private-source')
        self.resign()
        with self.assertRaisesRegex(ValueError,'private operational residue'): self.validate()

    def test_unexpected_files(self):
        write(self.root/'skills/plan/unlisted.txt','extra')
        with self.assertRaisesRegex(ValueError,'drift'): self.validate()

    def test_receipted_unexpected_root(self):
        write(self.root/'evil.py','pass')
        with self.assertRaisesRegex(ValueError,'unexpected root'): self.validate()

    def test_license_and_companion_metadata(self):
        for leaf in ['LICENSE','COMPANIONS.md']:
            with self.subTest(leaf=leaf):
                path=self.root/'skills/plan'/leaf;content=path.read_bytes();path.unlink();self.resign()
                with self.assertRaises((ValueError,OSError)): self.validate()
                path.write_bytes(content);path.chmod(0o644);self.resign()

    def test_duplicate_frontmatter(self):
        (self.root/'skills/plan/SKILL.md').write_text('---\nname: plan\nname: bad\ndescription: valid\n---\n');self.resign()
        with self.assertRaisesRegex(ValueError,'duplicate'):self.validate()

    def test_unportable_metadata(self):
        (self.root/'skills/plan/SKILL.md').write_text('---\nname: plan\ndescription: valid\nagent: planner\n---\n');self.resign()
        with self.assertRaisesRegex(ValueError,'unportable'):self.validate()

    def test_official_schema(self):
        plugin=json.loads((self.root/'plugin.json').read_text());plugin['name']='BAD NAME';write(self.root/'plugin.json',json.dumps(plugin));self.resign()
        with self.assertRaises(check.jsonschema.ValidationError):self.validate()

    def test_wrong_mcp(self):
        mcp=json.loads((self.root/'mcp.json').read_text());mcp['mcpServers']['default']['command']='other';write(self.root/'mcp.json',json.dumps(mcp));self.resign()
        with self.assertRaisesRegex(ValueError,'descriptor drift'):self.validate()

    def test_false_extension_declaration(self):
        plugin=json.loads((self.root/'plugin.json').read_text());plugin['extensions'][check.EXTENSION]['resources']['personas']='../../personas';write(self.root/'plugin.json',json.dumps(plugin));self.resign()
        with self.assertRaisesRegex(ValueError,'resource declaration'):self.validate()

    def test_receipt_digest_and_immutable_source(self):
        value=json.loads(self.sidecar.read_text());value['sourceCommit']='main';write(self.sidecar,json.dumps(value))
        with self.assertRaisesRegex(ValueError,'immutable'):self.validate()
        self.resign();value=json.loads(self.sidecar.read_text());value['digest']='c'*64;write(self.sidecar,json.dumps(value))
        with self.assertRaisesRegex(ValueError,'digest mismatch'):self.validate()

    def test_destination_owned_separation_and_tracked_residue(self):
        owned=json.loads((check.ROOT/'qa/destination-owned.json').read_text())['files']
        for name in owned:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(check.ROOT/name,path)
        subprocess.run(['git','init','-q',str(self.root)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True,capture_output=True)
        write(self.root/'.venv/cache.md','[unrelated private local cache](/absent/file)')
        write(self.root/'.repowise/wiki.md','[unrelated factory cache](../missing.md)')
        self.assertEqual(check.validate(self.root,self.sidecar,destination=True)['skills'],20)
        write(self.root/'.beads/secret.jsonl','private hive record')
        subprocess.run(['git','-C',str(self.root),'add','-f','.beads/secret.jsonl'],check=True,capture_output=True)
        with self.assertRaisesRegex(ValueError,'tracked private'): check.validate(self.root,self.sidecar,destination=True)

    def test_pinned_schema_drift(self):
        with mock.patch.dict(check.SCHEMA_HASHES,{'plugin.schema.json':'0'*64}):
            with self.assertRaisesRegex(ValueError,'pinned public schema drift'):self.validate()

    def test_guide_support_metadata(self):
        path=self.root/'skills/plan/SKILL.md'
        path.write_text('---\nname: plan\ndescription: valid\nmetadata:\n  guide:\n    entry: missing.md\n---\n')
        self.resign()
        with self.assertRaisesRegex(ValueError,'guide support'):self.validate()

    def test_strict_semver_receipt(self):
        original=json.loads(self.sidecar.read_text())
        for version in ['01.0.0','1.00.0','1.0.00','1.0.0-01','1.0.0-alpha.01','1.0.0-','1.0.0+','1.0.0-alpha..beta']:
            with self.subTest(version=version):
                value=dict(original);value['authoredVersion']=version;value.pop('digest');value['digest']=digest(value)
                write(self.sidecar,json.dumps(value))
                with self.assertRaisesRegex(ValueError,'candidate version'):self.validate()
        write(self.sidecar,json.dumps(original))

    def test_receipt_payload_digest(self):
        value=json.loads(self.sidecar.read_text());value['payloadDigest']='0'*64;value.pop('digest');value['digest']=digest(value)
        write(self.sidecar,json.dumps(value))
        with self.assertRaisesRegex(ValueError,'payload digest mismatch'):self.validate()

    def test_total_payload_and_receipt_deletion_cannot_pass(self):
        shutil.rmtree(self.root);self.root.mkdir()
        with self.assertRaisesRegex(ValueError,'required public'):self.validate()
        result=subprocess.run([sys.executable,str(check.ROOT/'qa/check_artifact.py'),'--artifact',str(self.root),'--receipt',str(self.sidecar),'--require-artifact'],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('required public',result.stderr)


if __name__=='__main__':unittest.main()
