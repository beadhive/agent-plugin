#!/usr/bin/env python3
"""Isolated public skills installation and native Codex plugin acceptance.

Staged mode deliberately cannot produce a public acceptance verdict.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time

from check_artifact import EXPECTED_SKILLS, ROOT, require, validate

PUBLIC = 'https://github.com/beadhive/agent-plugin'
CLI = ['npm', 'exec', '--yes', '--package=skills@1.7.0', '--', 'skills']
SET_REQUESTS = {
    'planning': (['plan'], {}),
    'dispatch': (['dispatcher'], {}),
    'control-intake': (['control'], {'control': ['intake']}),
    'refactor-request': (['refactor'], {'refactor': ['request'], 'planner': ['refactor']}),
    'refactor-execution': (['refactor'], {'refactor': ['execution'], 'developer': ['refactor']}),
    'modularize-request': (['modularize'], {'refactor': ['request'], 'planner': ['modularize']}),
    'modularize-execution': (['modularize'], {'refactor': ['execution'], 'developer': ['modularize']}),
    'onboarding': (['setup'], {}),
    'spike-replan': (['plan'], {'plan': ['spike-verdict'], 'planner': ['spike-verdict']}),
}


def run(args, cwd, env, timeout=180):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, 'Consumer command failed: ' + args[0])
    return result.stdout


def isolated_env(base):
    home = base / 'home'
    home.mkdir()
    return {'PATH': os.environ['PATH'], 'HOME': str(home),
            'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(base / 'cache'),
            'CODEX_HOME': str(base / 'codex-home'), 'npm_config_cache': str(base / 'npm-cache'),
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_TERMINAL_PROMPT': '0', 'DISABLE_TELEMETRY': '1', 'DO_NOT_TRACK': '1',
            'CI': '1', 'NO_COLOR': '1'}


def companions(artifact):
    """Read only generated public companion docs; never private source metadata."""
    records = {}
    for name in sorted(EXPECTED_SKILLS):
        text = (artifact / 'skills' / name / 'COMPANIONS.md').read_text()
        required = re.findall(r'\]\(\.\./([a-z-]+)/SKILL\.md\)', text)
        modes = {}
        for mode, names in re.findall(r'^- ([a-z-]+): install (.+?) when ', text, re.M):
            modes[mode] = re.findall(r'`([a-z-]+)`', names)
        require(set(required) <= EXPECTED_SKILLS, 'Unknown public companion')
        require(all(set(names) <= EXPECTED_SKILLS for names in modes.values()), 'Unknown mode companion')
        records[name] = (required, modes)
    return records


def closure(records, roots, active=None):
    selected, pending = set(), list(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        required, modes = records[name]
        pending.extend(required)
        for mode in (active or {}).get(name, []):
            require(mode in modes, 'Unknown documented mode')
            pending.extend(modes[mode])
    return sorted(selected)


def check_copy(source, installed, selected):
    require({p.name for p in installed.iterdir() if p.is_dir()} == set(selected), 'Installed skill roster drift')
    for name in selected:
        original, copied = source / 'skills' / name, installed / name
        expected = {p.relative_to(original).as_posix(): p for p in original.rglob('*') if p.is_file()}
        actual = {p.relative_to(copied).as_posix(): p for p in copied.rglob('*') if p.is_file()}
        require(expected.keys() == actual.keys(), 'Installed support inventory drift')
        require(not any(p.is_symlink() for p in copied.rglob('*')), 'Installed support symlink')
        for path in expected:
            require(expected[path].read_bytes() == actual[path].read_bytes(), 'Installed support bytes drift')
            require(expected[path].stat().st_mode & 0o777 == actual[path].stat().st_mode & 0o777,
                    'Installed support mode drift')
        require((copied / 'LICENSE').read_bytes() == (source / 'LICENSE').read_bytes(), 'Installed license drift')


def public_skills(artifact, commit, base, env):
    source = PUBLIC + '/tree/' + commit
    require(run(CLI + ['--version'], base, env).strip() == '1.7.0', 'skills CLI version drift')
    listing = run(CLI + ['add', source, '--list'], base, env)
    found = set(re.findall(r'^│    ([a-z][a-z-]+)\s*$', listing, re.M))
    require(found == EXPECTED_SKILLS, 'Public skill discovery drift')
    records = companions(artifact)
    requests = [('single-' + name, [name]) for name in sorted(EXPECTED_SKILLS)]
    requests += [(name + '-required', closure(records, [name])) for name in sorted(EXPECTED_SKILLS)
                 if len(closure(records, [name])) > 1]
    requests += [(label, closure(records, roots, modes)) for label, (roots, modes) in SET_REQUESTS.items()]
    requests += [('complete-corpus', sorted(EXPECTED_SKILLS))]
    results, tested = [], {}
    for label, selected in requests:
        key = tuple(selected)
        if key not in tested:
            project = base / ('install-' + label)
            project.mkdir()
            run(CLI + ['add', source, '--skill', *selected, '--agent', 'claude-code', '--copy', '-y'], project, env)
            check_copy(artifact, project / '.claude/skills', selected)
            tested[key] = label
        results.append({'set': label, 'selected': selected, 'bytesModesLicensesSupport': 'pass',
                        'missingCompanions': sorted(set().union(*(set(closure(records, [n])) for n in selected)) - set(selected)),
                        'installationSharedWith': tested[key]})
    return {'version': '1.7.0', 'source': source, 'discovered': sorted(found), 'installations': results,
            'uniqueInstallations': len(tested), 'installerResolvesDependencies': False,
            'skillsOnlyOmits': ['MCP registration', 'hooks', 'agents', 'styles', 'extension resources']}


class Protocol:
    def __init__(self, project, env):
        self.process = subprocess.Popen(['codex', '--disable', 'apps', 'app-server', '--stdio'],
                                        cwd=project, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.messages, self.identifier = queue.Queue(), 0
        def reader():
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
        threading.Thread(target=reader, daemon=True).start()

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()

    def call(self, method, params, timeout=120):
        self.identifier += 1
        self.send({'id': self.identifier, 'method': method, 'params': params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                message = self.messages.get(timeout=max(.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if message.get('id') == self.identifier:
                require('error' not in message, 'Native protocol failed: ' + method)
                return message['result']
        raise TimeoutError('Native protocol timeout: ' + method)

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()


def native(artifact, base, env):
    home, project = Path(env['CODEX_HOME']), base / 'native-project'
    home.mkdir(); project.mkdir()
    # Reference existing authorized authentication without copying or logging it.
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if auth.is_file():
        (home / 'auth.json').symlink_to(auth)
    plugin = project / 'plugins/beadhive'
    plugin.mkdir(parents=True)
    receipt = json.loads((artifact / 'release-receipt.json').read_text())
    for name in receipt['files']:
        target = plugin / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact / name, target)
    marketplace = project / '.agents/plugins/marketplace.json'
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(json.dumps({'name': 'consumer-acceptance', 'interface': {'displayName': 'Consumer Acceptance'},
        'plugins': [{'name': 'beadhive', 'source': {'source': 'local', 'path': './plugins/beadhive'},
                     'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, 'category': 'Productivity'}]}))
    version = run(['codex', '--version'], project, env).strip()
    run(['codex', 'plugin', 'marketplace', 'add', str(project), '--json'], project, env)
    run(['codex', 'plugin', 'add', 'beadhive@consumer-acceptance', '--json'], project, env)
    protocol = Protocol(project, env)
    try:
        protocol.call('initialize', {'clientInfo': {'name': 'beadhive-consumer-acceptance', 'version': '1'},
                                     'capabilities': {'experimentalApi': True}})
        protocol.send({'method': 'initialized', 'params': {}})
        listing = protocol.call('plugin/list', {'cwds': [str(project)], 'marketplaceKinds': ['local'], 'forceRefetch': False})
        detail = protocol.call('plugin/read', {'marketplacePath': str(marketplace), 'pluginName': 'beadhive'})['plugin']
        skills = protocol.call('skills/list', {'cwds': [str(project)], 'forceReload': True})
        require(not listing['marketplaceLoadErrors'], 'Native marketplace errors')
        require(detail['summary']['installed'] and detail['summary']['enabled'], 'Native plugin not enabled')
        found = {row['name'].removeprefix('beadhive:') for data in skills['data'] for row in data['skills']
                 if row['name'].startswith('beadhive:')}
        require(found == EXPECTED_SKILLS, 'Native skill discovery drift')
        require('default' in detail['mcpServers'], 'Native MCP declaration missing')
        thread = protocol.call('thread/start', {'cwd': str(project), 'ephemeral': True,
                                               'sandbox': 'read-only', 'approvalPolicy': 'never'})
        servers = protocol.call('mcpServerStatus/list', {'threadId': thread['thread']['id'],
                                                        'detail': 'toolsAndAuthOnly', 'limit': 100})
        server = next(row for row in servers['data'] if row['name'] == 'default')
        require(server['pluginId'] == detail['summary']['id'], 'Native MCP plugin identity mismatch')
        require(not server.get('toolsError'), 'Native MCP tool listing failed')
        tools = sorted(server['tools'])
        require({'hive_list', 'hive_status', 'plan_check'} <= set(tools), 'Native bh-mcp tools missing')
        return {'clientVersion': version, 'pluginSkills': sorted(found), 'installation': 'pass',
                'mcpStartupAndToolListing': 'pass', 'mcpCommand': 'bh-mcp', 'mcpTools': tools,
                'modelTurns': 0, 'toolsCalled': 0, 'temporaryConfiguration': True,
                'extensions': 'agents/instructions/permissions/personas embedded inert; not executed or enforced',
                'limits': 'Native discovery and MCP startup only; no skill task execution or universal client claim'}
    finally:
        protocol.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True, help='Exact reviewed destination Git SHA')
    parser.add_argument('--candidate-digest', required=True, help='Independent paired-gate payload candidate pin')
    parser.add_argument('--staged', type=Path, help='Local generated destination; native preparation ONLY')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}', args.commit), 'Full destination commit required')
    require(re.fullmatch('[0-9a-f]{64}', args.candidate_digest), 'Full payload candidate digest required')
    with tempfile.TemporaryDirectory(prefix='bh-ap-consumers-') as temporary:
        base = Path(temporary)
        env = isolated_env(base)
        artifact = base / 'artifact'
        if args.staged:
            artifact = args.staged.resolve()
        else:
            run(['git', 'clone', '--no-checkout', PUBLIC + '.git', str(artifact)], base, env)
            run(['git', 'checkout', '--detach', args.commit], artifact, env)
        require(run(['git', 'rev-parse', 'HEAD'], artifact, env).strip() == args.commit, 'Destination commit mismatch')
        # Never trust the destination's copy of the validator or QA ownership list.
        validate(artifact, artifact / 'release-receipt.json', True, args.candidate_digest)
        receipt = json.loads((artifact / 'release-receipt.json').read_text())
        evidence = {'schemaVersion': 1, 'publicRepository': PUBLIC, 'destinationCommit': args.commit,
                    'publicAcceptance': 'pending' if args.staged else 'pass',
                    'source': 'local staged destination' if args.staged else 'anonymous public clone and pinned remote skills CLI',
                    'releaseVersion': receipt['releaseVersion'], 'packVersion': receipt['authoredVersion'],
                    'sourceCommit': receipt['sourceCommit'], 'hitchRevision': receipt['hitchRevision'],
                    'candidateDigest': receipt['digest'], 'payloadDigest': receipt['payloadDigest'],
                    'platform': os.uname().sysname, 'ownershipSwitchAuthorized': False}
        if not args.staged:
            evidence['skillsCli'] = public_skills(artifact, args.commit, base, env)
        evidence['native'] = native(artifact, base, env)
        args.output.write_text(json.dumps(evidence, indent=2) + '\n')
        print('Staged native preparation passed; public acceptance PENDING' if args.staged else 'Public consumers passed')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, StopIteration, subprocess.TimeoutExpired, TimeoutError) as error:
        print('Consumer verification failed: ' + (str(error).split(':', 1)[0] if isinstance(error, ValueError)
                                                 else type(error).__name__), file=__import__('sys').stderr)
        raise SystemExit(1)
