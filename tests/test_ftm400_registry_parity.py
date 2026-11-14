"""Keep the new remote preview's supported models aligned with canonical registry."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'experimental' / 'ftm400_remote' / 'server.py'
spec = importlib.util.spec_from_file_location('ftm400_remote_parity', MODULE_PATH)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
REGISTRY = ROOT / 'data' / 'device_manuals.json'


class CanonicalRegistryParityTests(unittest.TestCase):
    def test_every_known_model_is_supported_once(self):
        data = json.loads(REGISTRY.read_text(encoding='utf-8'))
        models = [model for family in data['model_families'] for model in family['models']]
        self.assertEqual(len(models), len(set(models)), 'ambiguous duplicate manufacturer model')
        self.assertEqual(set(models), set(remote.MODELS), 'preview model list drifted from registry')

    def test_compatibility_families_match_registry(self):
        data = json.loads(REGISTRY.read_text(encoding='utf-8'))
        expected = {
            'YAESU.FTM400.DR-DE': 'DR/DE',
            'YAESU.FTM400.XDR-XDE': 'XDR/XDE',
        }
        self.assertEqual({x['id'] for x in data['model_families']}, set(expected))
        for family in data['model_families']:
            for model in family['models']:
                with self.subTest(model=model):
                    self.assertEqual(remote.MODELS[model], expected[family['id']])
                    self.assertFalse(remote.PreviewRadio(model).snapshot()['rf_transmit_enabled'])


if __name__ == '__main__':
    unittest.main()
