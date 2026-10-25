# KisanSaathi frontend

This React source is part of the Farm2Feed project. The production build is served by the root Flask app at `/kisaath/`, with all APIs on the same host and port.

From the project root, follow `README.md` to run the app. To rebuild this frontend, run `npm ci --legacy-peer-deps` and `npm run build` in this folder; Flask serves the generated `build/` folder. Do not use the standalone React development server as the app's run command.

Weather requests use the Flask server and Open-Meteo's public geocoding and forecast APIs; no API key is needed.
