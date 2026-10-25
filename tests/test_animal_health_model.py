"""Animal-health model: files, label order and preprocessing must stay consistent with the weights."""
import importlib.util
import pathlib
import re

import pytest

import app

SCRIPT = pathlib.Path(app.BASE_DIR) / "scripts" / "verify_animal_health_preprocessing.py"


def _checker():
    spec = importlib.util.spec_from_file_location("verify_animal_health_preprocessing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checkpoint_matches_the_pipeline_used_for_inference(capsys):
    checker = _checker()
    assert checker.main() == 0, "bundled weights were trained WITHOUT ImageNet normalisation; inference must not normalise"
    out = capsys.readouterr().out
    assert "no normalisation" in out


def test_inference_code_uses_the_verified_preprocessing_when_no_metadata():
    source = (pathlib.Path(app.BASE_DIR) / "services" / "animal_health.py").read_text(encoding="utf-8")
    fallback = source.split("else:", 1)[1].split("_model_bundle =", 1)[0]
    fallback = "\n".join(line for line in fallback.splitlines() if not line.strip().startswith("#"))
    assert "Resize((image_size, image_size))" in fallback and "ToTensor()" in fallback and "Normalize" not in fallback


def test_class_labels_match_the_frontend_keys():
    checker = _checker()
    classes = checker.load_checkpoint(checker.MODEL)["classes"]
    js = (pathlib.Path(app.BASE_DIR) / "animal_health_ai" / "static" / "script.js").read_text(encoding="utf-8")
    for label in classes:
        assert re.search(r"['\"]?%s['\"]?\s*:" % re.escape(label), js), f"front-end has no text for class {label!r}"


def test_both_model_files_only_contain_weights_only_safe_objects():
    import pickletools, zipfile
    allowed = {"collections.OrderedDict", "torch.FloatStorage", "torch.LongStorage", "torch._utils._rebuild_tensor_v2"}
    for rel in ("animal_health_ai/models/best_model.pth",
                "integrations/livestock-scheme-advisor/backend/models/breed_classifier_weights.pt"):
        archive = zipfile.ZipFile(pathlib.Path(app.BASE_DIR) / rel)
        data = archive.read(next(n for n in archive.namelist() if n.endswith("data.pkl")))
        found, last = set(), []
        for op, arg, _ in pickletools.genops(data):
            if op.name == "GLOBAL":
                found.add(arg.replace(" ", "."))
            elif op.name == "STACK_GLOBAL" and len(last) >= 2:
                found.add(f"{last[-2]}.{last[-1]}")
            if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE"):
                last.append(arg)
        assert found <= allowed, f"{rel} needs unsafe unpickling: {found - allowed}"


def test_torch_runtime_loads_and_predicts_when_torch_is_installed():
    torch = pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    from services import animal_health
    _, model, classes, transform = animal_health._model()
    from PIL import Image
    tensor = transform(Image.new("RGB", (300, 200), (90, 120, 60))).unsqueeze(0)
    assert tuple(tensor.shape) == (1, 3, 224, 224)
    probabilities = torch.softmax(model(tensor), dim=1)[0]
    assert len(classes) == len(probabilities) and abs(float(probabilities.sum()) - 1.0) < 1e-4
