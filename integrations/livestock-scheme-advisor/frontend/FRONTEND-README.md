# Livestock scheme advisor: coverage and limitations

## What the UI shows

- `schemes.json` contains 66 scheme catalogue entries, each with English and Marathi names and short descriptions.
- The compact eligibility artifact has outputs for only 16 of those entries. The API returns all 66, marks the 16 as model estimates, and marks the remaining 50 as **not evaluated**. They are not presented as ineligible.
- The model receives the seven profile fields listed in `backend/models/feature_metadata.json`: breed, animal count, social category, land holding, employment status, gender, and district.
- The original `top1_model.joblib` and `top1_label_encoder.joblib` ranking artifacts are not included. If the ranking model is unavailable, the API reports its fallback method and orders only model-estimated eligible entries by eligibility-model confidence. If there are no estimated-eligible entries, it returns no recommendation.
- The UI's English and Marathi messages distinguish model estimates from verified eligibility. The Marathi language switch applies immediately. See `i18n.json` and the bundled page in `index.html`.

## Do not interpret the model as an eligibility decision

The bundled eligibility training data is generated from rule-pattern assumptions, not a verified collection of real farmer outcomes. Its 2,965-row validation figures measure agreement with that generated data only; they do not demonstrate real-world accuracy. The manifest also marks entries requiring verification. Eligibility criteria, availability, official links, and application windows can change; check them with the relevant department or official portal before applying.

The 66-entry catalogue also includes entries beyond direct livestock subsidies (for example, broader agriculture, institutional programs, surveys, and awards). Catalogue presence does not mean that a farmer qualifies or that the scheme is a direct cash benefit. Review each scheme's scope before making an application recommendation.

The scheme names/short descriptions have English and Marathi text, but source URLs and scheme rules were not independently reverified during this repair. Some manifest entries explicitly call out missing or unverified eligibility details. Preserve those warnings rather than filling gaps with assumptions.

## Photo and veterinary features

The ZIP does not contain a 2.18 GB eligibility artifact. It contains the compact eligibility model and separate breed/animal-health weights. The breed-photo prediction and animal-health image inference require PyTorch and were not exercised in the verification environment.

The veterinary locator's interface labels, canonical district names, and facility categories are available in Marathi. Facility names, addresses, and taluka values remain in their source text because the archive does not include a vetted bilingual location dictionary.

## Development and production files

The production veterinary app serves `frontend/dist/`. Source changes should be followed by a rebuild from `integrations/vet-app/frontend`:

```bash
npm ci --no-audit --no-fund
npm run build
```

The updated ZIP already includes the rebuilt bundle.
