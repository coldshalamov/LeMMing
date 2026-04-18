import json
import os
import tempfile
import time
from pathlib import Path

from lemming.models import ModelRegistry, reset_models_cache


def test_model_registry_cache():
    reset_models_cache()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        models_file = config_dir / "models.json"

        test_data = {"test_model": {"provider": "dummy", "model_name": "test-dummy", "provider_config": {}}}

        with open(models_file, "w") as f:
            json.dump(test_data, f)

        r1 = ModelRegistry(config_dir)
        keys1 = r1.list_keys()
        assert keys1 == ["test_model"]

        # Test 2: modify file but keep mtime
        original_mtime = models_file.stat().st_mtime
        original_atime = models_file.stat().st_atime

        test_data2 = {"test_model2": {"provider": "dummy2", "model_name": "test-dummy2", "provider_config": {}}}

        with open(models_file, "w") as f:
            json.dump(test_data2, f)

        os.utime(models_file, (original_atime, original_mtime))

        # Should be cached
        r2 = ModelRegistry(config_dir)
        keys2 = r2.list_keys()
        assert keys2 == ["test_model"]

        # Test 3: update mtime, should load new
        time.sleep(0.01)  # ensure new mtime is different enough

        with open(models_file, "w") as f:
            json.dump(test_data2, f)

        r3 = ModelRegistry(config_dir)
        keys3 = r3.list_keys()
        assert keys3 == ["test_model2"]
