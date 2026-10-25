# Pashu Yojana Sahayak — Livestock Government Scheme Advisor

Photo → breed → farmer profile → the list of Maharashtra state + Central
government livestock schemes that farmer is eligible for.

## What's in this project

```
livestock-scheme-advisor/
├── colab/
│   └── Livestock_Scheme_Advisor_Training.ipynb   # run this in Google Colab — trains BOTH models
├── backend/
│   ├── app.py             # FastAPI server — serves both trained models
│   ├── requirements.txt
│   └── models/             # <- put the files from the Colab .zip download here
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js               # calls the backend at http://localhost:8000
├── data/
│   ├── stage2_scheme_eligibility.csv        # your full dataset (with explanations_json)
│   ├── stage2_scheme_eligibility_slim.csv   # same, without explanations_json (used for training)
│   └── rules_manifest.json                  # scheme master data (names, basis, sources)
└── README.md               # you are here
```

## The two models

| Stage | Input | Output | Model |
|---|---|---|---|
| **1 — Breed ID** | A photo of the animal | Predicted breed + confidence (cattle/buffalo/sheep only — see note below) | MobileNetV2 transfer-learning CNN, **PyTorch/torchvision** |
| **2 — Eligibility** | Breed + animals owned + social category + land holding + employment status + gender + district | Which of the 16 schemes in `rules_manifest.json` the farmer is eligible for | Random Forest multi-label classifier (+ a single "top recommendation" classifier), **scikit-learn** |

**Why PyTorch, not TensorFlow:** TensorFlow does not currently ship an installable
build for the newest Python releases (e.g. 3.13/3.14) — `pip install tensorflow`
fails outright there. PyTorch does provide wheels for newer Python versions (CPU
builds, which is all inference needs), so the breed classifier runs on PyTorch
specifically so the backend can run on whichever Python you already have,
without needing a second, older Python install just for this project.

**Important limitation:** the four Kaggle datasets you listed
(`indian-bovine-breeds`, `indian-cattle-image-dataset`, `indian-buffalo-dataset`,
`sheep-breed-classification`) only contain **cattle, buffalo and sheep** photos.
Your CSV also includes **goat** breeds (Osmanabadi, Sangamneri, Local goat) and
**poultry** classes (Desi poultry, Kadaknath, Improved layer/broiler) — there's
no public image dataset wired up for those yet. The app handles this by giving
goat/poultry-owning farmers a **manual breed dropdown** instead of a photo
upload. If you find/label a goat or poultry image set later, just add it to
`DATASET_CONFIGS` in the notebook's Section 3 and retrain — no other code needs
to change.

---

## Step-by-step

### A. Get a Kaggle API key
1. Go to https://www.kaggle.com/settings → **API** → **Create New Token**.
2. This downloads `kaggle.json`. Keep it handy — the notebook will ask you to
   upload it.

### B. Run the training notebook in Google Colab
1. Open Google Colab → **File → Upload notebook** → upload
   `colab/Livestock_Scheme_Advisor_Training.ipynb`.
2. **Runtime → Change runtime type → GPU (T4)**.
3. Run the cells **top to bottom**. Along the way it will ask you to upload:
   - `kaggle.json` (Section 2)
   - `stage2_scheme_eligibility_slim.csv` (Section 10 — from this project's `data/` folder)
   - `rules_manifest.json` (Section 11 — from `data/` folder)
4. **Section 4** prints every image-class folder name found in each Kaggle
   dataset. Skim it once — if a breed you care about isn't being picked up
   (i.e. it doesn't show up in the "Final breed classes used for training"
   list at the end of Section 5), add a matching keyword to the
   `BREED_ALIASES` dict in Section 4 and re-run Sections 4–5.
5. Training takes roughly 10–20 minutes on a T4 GPU for Stage 1, and under a
   minute for Stage 2 (it's a Random Forest on ~14k rows).
6. The last cell zips everything into `livestock_models.zip` and downloads it
   to your computer via the browser.

### C. Wire the trained models into the backend
1. **Delete everything currently in `backend/models/` first.** Don't merge old and new files,
   and never rename a file to make it match — `breed_classifier_weights.pt` (a plain PyTorch
   `state_dict`, i.e. just the learned numbers) and an older `breed_classifier.pt`
   (TorchScript, which bundles the numbers *and* the model architecture together) are
   structurally different file formats. Renaming one to the other produces a file that looks
   right in File Explorer but fails to load.
2. Unzip `livestock_models.zip`.
3. Copy every file inside it into `backend/models/`, so you have exactly:
   ```
   backend/models/
     breed_classifier_weights.pt  (PyTorch state_dict — weights only; backend rebuilds the architecture)
     breed_labels.json
      eligibility_model_compact.joblib
      compact_model_metadata.json
     feature_metadata.json
     rules_manifest.json
   ```
4. **Verify it actually loaded correctly** — this matters more than it sounds. Start the
   backend (step D below) and read the startup log line by line:
   - You want to see `[startup] Loaded compact eligibility model` and
     `[startup] Loaded compact model metadata (16 labels)`.
   - When the optional breed-classifier dependencies are installed, you should also see
     `[startup] Loaded breed classifier (N classes)` with **no**
     `FutureWarning` about `torch.jit` above it, and **no**
     `InconsistentVersionWarning` above the `[startup] Loaded compact eligibility model` line.

For the unified KisanSaathi bundle, the supplied multi-gigabyte eligibility artifact is replaced by `backend/models/eligibility_model_compact.joblib`, a small decision-tree model trained from `data/stage2_scheme_eligibility_slim.csv`. Its supported label list and held-out validation metrics are in `backend/models/compact_model_metadata.json`. Only labels present in that supplied dataset are scored; other catalogue schemes remain unscored.
   - A model that loads *with* a version warning is not confirmed safe — scikit-learn's own
     documentation is explicit that behavior across versions isn't guaranteed even when
     unpickling technically succeeds; predictions could be silently wrong. Treat any such
     warning as a real problem to fix (retrain with matching versions), not something to
     shrug off because the server didn't crash.
   - The most common cause of a version-warning is training Stage 1 and Stage 2 at different
     times, in different Colab sessions, with different scikit-learn versions silently
     installed. The safest habit: whenever you retrain anything, re-run the **entire**
     notebook top to bottom in one sitting (Runtime → Run all) rather than re-running
     individual sections — that guarantees every file in the resulting zip was produced by
     the exact same package versions.

### D. Run the backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended (macOS/Linux)
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```
On Windows, `python -m pip ...` / `python -m uvicorn ...` (rather than bare `pip`/`uvicorn`)
avoids "not recognized as a command" errors when Python's `Scripts` folder isn't on PATH —
this is the more reliable form to use either way.

Visit http://localhost:8000 in a browser — you should see a JSON status
response confirming both models loaded, plus the dropdown option lists. You can also check
http://localhost:8000/health for a compact loaded/not-loaded summary with error details.

### E. Open the frontend
The frontend is plain HTML/CSS/JS — no build step. Two ways to open it:
- **Simplest:** double-click `frontend/index.html` to open it directly in a browser.
- **Recommended** (avoids browser file:// quirks): serve it locally, e.g.
  ```bash
  cd frontend
  python -m http.server 5500
  ```
  then visit http://localhost:5500.

The frontend calls the backend at `http://localhost:8000` by default. To point
it elsewhere (e.g. a deployed backend), set `window.API_BASE = "https://your-api.example.com"`
in a `<script>` tag before `app.js` loads in `index.html`.

### F. Use it
1. Upload a cattle/buffalo/sheep photo → click **Identify breed from photo**
   (or use the manual breed dropdown for goats/poultry, or if you'd rather not
   upload a photo).
2. Fill in animals owned, social category, land holding, employment status,
   gender, and district.
3. Click **Find my schemes** → see the eligible schemes, the top recommendation,
   and each scheme's level (state/central) and kind (asset/service/credit/insurance).

---

## Retraining / improving later
- **More breeds:** add datasets to `DATASET_CONFIGS` (Section 3 of the notebook),
  extend `BREED_ALIASES` (Section 4), re-run the whole notebook, and drop the
  new `.zip` contents into `backend/models/` again.
- **Better eligibility accuracy:** since the CSV is itself rule-generated
  (see `explanations_json` in the full CSV), the Random Forest should already
  get close to 100% — if it doesn't, check that `feature_metadata.json`'s
  `label_cols` matches the `elig_*` columns in your CSV, and that categorical
  values in the frontend dropdowns exactly match the CSV's spelling
  (e.g. `semi_medium_plus`, not `Semi Medium Plus`).
- **Deploying for real farmers:** put the backend behind HTTPS (e.g. on
  Render/Railway/a small VM with `uvicorn` behind nginx), update `API_BASE` in
  the frontend, and host the static frontend files anywhere (Netlify, GitHub
  Pages, S3).

## Data provenance
All rupee figures, subsidy percentages, and category rules come from
`data/rules_manifest.json`, sourced from Maharashtra GRs (2021–2023) as
republished at `dahd.maharashtra.gov.in` and `ah.mahabms.com`, plus a
user-supplied document for central schemes (RGM, NLM, PKCC, DEDS, DIDF, LIS,
NADCP, AHIDF). Several demographic priors (social-category shares, land-holding
shares) are **configurable assumptions, not verified Maharashtra statistics** —
see the `assumptions` array in `rules_manifest.json` before quoting any
distributional claim publicly.
