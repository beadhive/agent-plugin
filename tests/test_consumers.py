"""Consumer proof must detect lost support bytes/modes and incomplete companions."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

QA = Path(__file__).resolve().parents[1] / 'qa'
sys.path.insert(0, str(QA))
from check_consumers import check_copy, closure, isolated_env, main


class ConsumerControls(unittest.TestCase):
    def test_support_loss_and_nonexecutability_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, installed = root / 'source', root / 'installed'
            original, copied = source / 'skills/example', installed / 'example'
            original.mkdir(parents=True); copied.mkdir(parents=True)
            (source / 'LICENSE').write_text('MIT test notice\n')
            for name, text in [('SKILL.md', 'example\n'), ('LICENSE', 'MIT test notice\n'), ('helper.sh', '#!/bin/sh\n')]:
                (original / name).write_text(text); (copied / name).write_text(text)
            (original / 'helper.sh').chmod(0o755); (copied / 'helper.sh').chmod(0o755)
            check_copy(source, installed, ['example'])
            (copied / 'helper.sh').chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'mode drift'):
                check_copy(source, installed, ['example'])
            (copied / 'helper.sh').unlink()
            with self.assertRaisesRegex(ValueError, 'inventory drift'):
                check_copy(source, installed, ['example'])

    def test_transitive_mode_companions_with_cycle(self):
        records = {'developer': (['work'], {'refactor': ['refactor']}),
                   'work': ([], {}), 'refactor': (['developer'], {})}
        self.assertEqual(closure(records, ['developer']), ['developer', 'work'])
        self.assertEqual(closure(records, ['developer'], {'developer': ['refactor']}),
                         ['developer', 'refactor', 'work'])
        with self.assertRaisesRegex(ValueError, 'Unknown documented mode'):
            closure(records, ['developer'], {'developer': ['undeclared']})

    def test_environment_has_no_source_credentials_or_global_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict('os.environ', {'GITHUB_TOKEN': 'sentinel', 'CODEX_HOME': '/real/config'}):
                env = isolated_env(Path(temporary))
            self.assertNotIn('GITHUB_TOKEN', env)
            self.assertNotEqual(env['CODEX_HOME'], '/real/config')
            self.assertTrue(Path(env['HOME']).is_relative_to(temporary))
            self.assertEqual(env['GIT_TERMINAL_PROMPT'], '0')

    def test_moving_ref_rejected_before_network_or_client_startup(self):
        with patch.object(sys, 'argv', ['check_consumers.py', '--commit', 'main',
                                      '--candidate-digest', 'a' * 64, '--output', '/tmp/unused-consumer-test.json']):
            with patch('check_consumers.run') as command:
                with self.assertRaisesRegex(ValueError, 'Full destination commit required'):
                    main()
                command.assert_not_called()
