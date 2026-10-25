"""Check which image preprocessing the bundled animal-health model was TRAINED with.

Needs only numpy + Pillow (no PyTorch), so it runs the same on Windows 10/11 and macOS 12.

Why this works: during training a ResNet's first BatchNorm layer stores running statistics of the
values coming out of the first convolution, i.e. statistics of the training images *after* the
training-time preprocessing.  We push real photos through the first convolution under each candidate
preprocessing and see which one reproduces the stored statistics:

    python scripts/verify_animal_health_preprocessing.py

Result for the bundled best_model.pth: plain Resize(224x224) + ToTensor (pixel values 0..1, NO ImageNet
mean/std normalisation) reproduces the stored statistics; ImageNet normalisation is ~15x off.
services/animal_health.py uses exactly that pipeline when the checkpoint carries no normalisation
metadata.  Re-run this script if you ever replace the weights.
"""
import io
import pickle
import sys
import zipfile
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "animal_health_ai" / "models" / "best_model.pth"
IMAGES = sorted((ROOT / "static" / "images").glob("*.jp*g")) + sorted((ROOT / "static" / "images").glob("*.jfif"))
DTYPES = {"FloatStorage": np.float32, "LongStorage": np.int64, "DoubleStorage": np.float64,
          "HalfStorage": np.float16, "IntStorage": np.int32}


class _Storage:
    def __init__(self, name):
        self.name = name


def load_checkpoint(path):
    """Read a torch zip checkpoint with the standard library only (tensors become numpy arrays)."""
    archive = zipfile.ZipFile(path)
    pkl = next(n for n in archive.namelist() if n.endswith("data.pkl"))
    prefix = pkl[: -len("data.pkl")]
    cache = {}

    class Unpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if name in DTYPES:
                return _Storage(name)
            if name == "_rebuild_tensor_v2":
                def rebuild(storage, offset, size, stride, *_):
                    key, dtype = storage
                    if key not in cache:
                        cache[key] = np.frombuffer(archive.read(prefix + "data/" + key), dtype=dtype)
                    flat = cache[key]
                    view = np.lib.stride_tricks.as_strided(
                        flat[offset:], shape=tuple(size), strides=tuple(s * flat.itemsize for s in stride))
                    return np.array(view)
                return rebuild
            if name == "OrderedDict":
                import collections
                return collections.OrderedDict
            raise pickle.UnpicklingError(f"unexpected object in checkpoint: {module}.{name}")

        def persistent_load(self, pid):
            storage_type = pid[1]
            return pid[2], DTYPES.get(getattr(storage_type, "name", "FloatStorage"), np.float32)

    return Unpickler(io.BytesIO(archive.read(pkl))).load()


def first_layer_statistics(image, conv1, normalise):
    pixels = np.asarray(image.convert("RGB").resize((224, 224), Image.BILINEAR), dtype=np.float32) / 255.0
    if normalise:
        pixels = (pixels - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    padded = np.pad(pixels.transpose(2, 0, 1), ((0, 0), (3, 3), (3, 3)))
    windows = sliding_window_view(padded, (7, 7), axis=(1, 2))[:, ::2, ::2]
    out = np.einsum("chwij,ocij->ohw", windows, conv1).reshape(conv1.shape[0], -1)
    return out.mean(1), out.var(1)


def main():
    checkpoint = load_checkpoint(MODEL)
    state = checkpoint["model_state_dict"]
    classes = checkpoint["classes"]
    print(f"classes (output order): {classes}")
    assert state["fc.weight"].shape == (len(classes), 512), "classifier head does not match the class list"
    print(f"architecture check: {len(state)} tensors, fc {tuple(state['fc.weight'].shape)} -> ResNet18 with {len(classes)} outputs")
    print(f"extra metadata in checkpoint: {sorted(set(checkpoint) - {'model_state_dict', 'classes'}) or 'none'}")
    if not IMAGES:
        sys.exit("No sample images found in static/images")
    conv1, running_mean, running_var = state["conv1.weight"], state["bn1.running_mean"], state["bn1.running_var"]
    live = running_var > 1e-4
    scores = {}
    for normalise in (False, True):
        stats = [first_layer_statistics(Image.open(p), conv1, normalise) for p in IMAGES]
        mean = np.mean([s[0] for s in stats], axis=0)
        var = np.mean([s[1] for s in stats], axis=0)
        log_error = float(np.mean(np.abs(np.log(var[live] + 1e-9) - np.log(running_var[live] + 1e-9))))
        corr = float(np.corrcoef(mean[live], running_mean[live])[0, 1])
        scores[normalise] = log_error
        label = "ImageNet mean/std normalisation" if normalise else "plain 0..1 pixels (no normalisation)"
        print(f"{label:40s} mean |log variance ratio| = {log_error:5.2f}   correlation of channel means = {corr:5.3f}")
    verdict = "no normalisation" if scores[False] < scores[True] else "ImageNet normalisation"
    print(f"\nThe stored statistics match: {verdict}")
    return 0 if verdict == "no normalisation" else 1


if __name__ == "__main__":
    sys.exit(main())
