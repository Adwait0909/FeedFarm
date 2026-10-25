function csrfHeaders() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? { "X-CSRF-Token": meta.content } : {};
}

// --------------------------------------------------
// Translations
// --------------------------------------------------

const TEXT = {
  en: {
    navTitle: "Cattle Disease Detector",
    subtitle: "Upload a photo of a cow to check for signs of Foot-and-Mouth Disease, Lumpy Skin Disease, or a healthy animal.",
    uploadText: "Choose a cow image",
    analyzeButton: "Analyze Image",
    resultHeading: "Result",
    confidenceLabel: "Confidence breakdown:",
    infoHeading: "What this means",
    severityHeading: "Severity",
    severityDisclaimer: "Severity is an approximate indicator based on the model's prediction confidence — not a clinical severity assessment. Always consult a veterinarian for an accurate diagnosis.",
    footerText: "This is an AI prediction from a student project model — not a substitute for veterinary diagnosis. When in doubt, consult a vet.",
    footerLine2: "Cattle Disease Detector — built with PyTorch & Flask",
    promptUpload: "👆 Upload an image, then press \u201cAnalyze Image\u201d to get a prediction.",
    promptAnalyze: "Image uploaded. Press \u201cAnalyze Image\u201d below to run the model.",
    analyzing: "Analyzing...",
    errorGeneric: "Something went wrong. Please check the server terminal and try again.",
    downloadReportButton: "📄 Download PDF Report",
    generatingReport: "Generating report...",
    generatedLabel: "Generated on",
    reportError: "Couldn't generate the report. Please check the server terminal and try again.",
    classNames: {
      "healthy": "Healthy",
      "lumpy": "Lumpy Skin Disease",
      "foot-and-mouth": "Foot-and-Mouth Disease",
    },
    severityLabels: { low: "Low", medium: "Medium", high: "High" },
  },
  mr: {
    navTitle: "गाई आजार ओळख प्रणाली",
    subtitle: "पाय व तोंड रोग (FMD), लम्पी त्वचा रोग किंवा निरोगी गाय ओळखण्यासाठी गायीचा फोटो अपलोड करा.",
    uploadText: "गायीचा फोटो निवडा",
    analyzeButton: "फोटो तपासा",
    resultHeading: "निकाल",
    confidenceLabel: "विश्वासार्हता तपशील:",
    infoHeading: "याचा अर्थ काय",
    severityHeading: "तीव्रता",
    severityDisclaimer: "येथील तीव्रता ही मॉडेलच्या अंदाजाच्या विश्वासार्हतेवर आधारित अंदाजे माहिती आहे — हे वैद्यकीय तीव्रता मूल्यांकन नाही. अचूक निदानासाठी नेहमी पशुवैद्यकाचा सल्ला घ्या.",
    footerText: "ही एक विद्यार्थी प्रकल्पाच्या एआय मॉडेलद्वारे केलेली अंदाजित माहिती आहे — पशुवैद्यकीय निदानाला पर्याय नाही. शंका असल्यास पशुवैद्यकाचा सल्ला घ्या.",
    footerLine2: "गाई आजार ओळख प्रणाली — PyTorch आणि Flask वापरून तयार",
    promptUpload: "👆 फोटो अपलोड करा, नंतर अंदाज मिळवण्यासाठी \u201cफोटो तपासा\u201d दाबा.",
    promptAnalyze: "फोटो अपलोड झाला. मॉडेल चालवण्यासाठी खालील \u201cफोटो तपासा\u201d बटण दाबा.",
    analyzing: "तपासणी सुरू आहे...",
    errorGeneric: "काहीतरी चूक झाली. कृपया सर्व्हर टर्मिनल तपासा आणि पुन्हा प्रयत्न करा.",
    downloadReportButton: "📄 PDF अहवाल डाउनलोड करा",
    generatingReport: "अहवाल तयार होत आहे...",
    generatedLabel: "तयार केले",
    reportError: "अहवाल तयार करता आला नाही. कृपया सर्व्हर टर्मिनल तपासा आणि पुन्हा प्रयत्न करा.",
    classNames: {
      "healthy": "निरोगी",
      "lumpy": "लम्पी त्वचा रोग",
      "foot-and-mouth": "पाय व तोंड रोग",
    },
    severityLabels: { low: "कमी", medium: "मध्यम", high: "उच्च" },
  },
};

const DISEASE_INFO = {
  en: {
    "healthy": {
      summary: "No visible signs of Lumpy Skin Disease or Foot-and-Mouth Disease detected.",
      points: [
        "Keep up routine care: clean water, balanced feed, and regular deworming.",
        "Still worth a periodic vet check-up, especially during disease outbreak seasons.",
        "Re-check with a fresh photo if the animal starts showing symptoms later.",
      ],
    },
    "lumpy": {
      summary: "Signs consistent with Lumpy Skin Disease (LSD), a viral disease spread by biting insects (mosquitoes, ticks, flies).",
      points: [
        "Isolate the animal from the rest of the herd immediately to limit spread.",
        "Contact a veterinarian promptly for confirmation and treatment.",
        "Control biting insects around the shed (nets, insecticide spray).",
        "Avoid moving the animal to markets or other farms until cleared by a vet.",
      ],
    },
    "foot-and-mouth": {
      summary: "Signs consistent with Foot-and-Mouth Disease (FMD), a highly contagious viral disease affecting the mouth, tongue, and feet.",
      points: [
        "Isolate the animal immediately — FMD spreads very easily between animals.",
        "Contact a veterinarian or local animal husbandry department right away.",
        "Disinfect footwear, equipment, and vehicles moving between animals.",
        "Restrict animal movement in/out of the farm until the outbreak is controlled.",
      ],
    },
  },
  mr: {
    "healthy": {
      summary: "लम्पी त्वचा रोग किंवा पाय व तोंड रोगाची कोणतीही स्पष्ट लक्षणे आढळली नाहीत.",
      points: [
        "नियमित काळजी सुरू ठेवा: स्वच्छ पाणी, संतुलित आहार आणि वेळोवेळी जंतनाशक औषध द्या.",
        "साथीच्या हंगामात वेळोवेळी पशुवैद्यकाकडून तपासणी करून घेणे योग्य.",
        "नंतर लक्षणे दिसल्यास नवीन फोटोसह पुन्हा तपासा.",
      ],
    },
    "lumpy": {
      summary: "लम्पी त्वचा रोग (LSD) ची लक्षणे दिसत आहेत — हा एक विषाणूजन्य आजार आहे जो डास, गोचिड, माश्या यांसारख्या चावणाऱ्या कीटकांमार्फत पसरतो.",
      points: [
        "जनावराला ताबडतोब कळपापासून वेगळे करा जेणेकरून रोग पसरणार नाही.",
        "पुष्टीकरण व उपचारासाठी लवकरात लवकर पशुवैद्यकाशी संपर्क साधा.",
        "गोठ्याभोवती कीटक नियंत्रण करा (जाळी, कीटकनाशक फवारणी).",
        "पशुवैद्यकाची परवानगी मिळेपर्यंत जनावराला बाजारात किंवा इतर फार्मवर नेऊ नका.",
      ],
    },
    "foot-and-mouth": {
      summary: "पाय व तोंड रोग (FMD) ची लक्षणे दिसत आहेत — हा एक अत्यंत संसर्गजन्य विषाणूजन्य आजार आहे जो तोंड, जीभ आणि पायांवर परिणाम करतो.",
      points: [
        "जनावराला त्वरित वेगळे करा — FMD जनावरांमध्ये फार वेगाने पसरतो.",
        "त्वरित पशुवैद्यक किंवा स्थानिक पशुसंवर्धन विभागाशी संपर्क साधा.",
        "जनावरांच्या दरम्यान वापरले जाणारे बूट, उपकरणे आणि वाहने निर्जंतुक करा.",
        "साथ नियंत्रित होईपर्यंत फार्ममध्ये जनावरांची ने-आण थांबवा.",
      ],
    },
  },
};

const SEVERITY_MESSAGES = {
  en: {
    low: "Signs are unclear or mild. Re-check with a clearer, well-lit photo, and monitor the animal over the next day or two.",
    medium: "Noticeable signs detected. Isolate the animal and contact a veterinarian within the next day or two.",
    high: "Strong, clear signs detected. Isolate the animal immediately and contact a veterinarian as soon as possible.",
  },
  mr: {
    low: "लक्षणे अस्पष्ट किंवा सौम्य आहेत. स्पष्ट व चांगल्या प्रकाशातील फोटोने पुन्हा तपासा आणि पुढील एक-दोन दिवस जनावरावर लक्ष ठेवा.",
    medium: "लक्षणीय चिन्हे आढळली आहेत. जनावराला वेगळे करा आणि पुढील एक-दोन दिवसांत पशुवैद्यकाशी संपर्क साधा.",
    high: "स्पष्ट व तीव्र लक्षणे आढळली आहेत. जनावराला ताबडतोब वेगळे करा आणि शक्य तितक्या लवकर पशुवैद्यकाशी संपर्क साधा.",
  },
};

const SEVERITY_COLOR = { low: "#fbc02d", medium: "#f57c00", high: "#c62828" };
const SEVERITY_EMOJI = { low: "🟡", medium: "🟠", high: "🔴" };

function getSeverity(confidence) {
  if (confidence < 0.65) return "low";
  if (confidence < 0.85) return "medium";
  return "high";
}

// --------------------------------------------------
// State
// --------------------------------------------------

let currentLang = "en";
let lastResult = null; // { predicted_class, confidence, all_scores }
let selectedFile = null;

// --------------------------------------------------
// DOM references
// --------------------------------------------------

const navTitle = document.getElementById("navTitle");
const subtitle = document.getElementById("subtitle");
const uploadText = document.getElementById("uploadText");
const fileInput = document.getElementById("fileInput");
const previewWrap = document.getElementById("previewWrap");
const previewImg = document.getElementById("previewImg");
const analyzeBtn = document.getElementById("analyzeBtn");
const promptMsg = document.getElementById("promptMsg");

const resultCard = document.getElementById("resultCard");
const resultHeading = document.getElementById("resultHeading");
const predictionBadge = document.getElementById("predictionBadge");
const confidenceLabel = document.getElementById("confidenceLabel");
const confidenceBars = document.getElementById("confidenceBars");
const severityBlock = document.getElementById("severityBlock");
const severityTitle = document.getElementById("severityTitle");
const severityMsg = document.getElementById("severityMsg");
const severityDisclaimer = document.getElementById("severityDisclaimer");
const downloadReportBtn = document.getElementById("downloadReportBtn");

const infoCard = document.getElementById("infoCard");
const infoHeading = document.getElementById("infoHeading");
const infoSummary = document.getElementById("infoSummary");
const infoPoints = document.getElementById("infoPoints");

const footerText = document.getElementById("footerText");
const footerLine2 = document.getElementById("footerLine2");

const langEnBtn = document.getElementById("langEnBtn");
const langMrBtn = document.getElementById("langMrBtn");

// --------------------------------------------------
// Render (re)draws all text for the current language + current state
// --------------------------------------------------

function render() {
  const T = TEXT[currentLang];

  navTitle.textContent = T.navTitle;
  subtitle.textContent = T.subtitle;
  uploadText.textContent = T.uploadText;
  analyzeBtn.textContent = T.analyzeButton;

  langEnBtn.classList.toggle("active", currentLang === "en");
  langMrBtn.classList.toggle("active", currentLang === "mr");

  footerText.textContent = T.footerText;
  footerLine2.textContent = T.footerLine2;

  if (!selectedFile) {
    promptMsg.style.display = "block";
    promptMsg.textContent = T.promptUpload;
    resultCard.style.display = "none";
    infoCard.style.display = "none";
    downloadReportBtn.style.display = "none";
    return;
  }

  if (!lastResult) {
    promptMsg.style.display = "block";
    promptMsg.textContent = T.promptAnalyze;
    resultCard.style.display = "none";
    infoCard.style.display = "none";
    downloadReportBtn.style.display = "none";
    return;
  }

  promptMsg.style.display = "none";
  renderResult();
}

function renderResult() {
  const T = TEXT[currentLang];
  const INFO = DISEASE_INFO[currentLang];
  const SEV_MSG = SEVERITY_MESSAGES[currentLang];

  const { predicted_class, confidence, all_scores } = lastResult;
  const displayName = T.classNames[predicted_class];

  resultCard.style.display = "block";
  resultHeading.textContent = T.resultHeading;

  predictionBadge.textContent = `${predicted_class === "healthy" ? "✅" : "⚠️"} ${displayName} — ${(confidence * 100).toFixed(1)}%`;
  predictionBadge.className = "badge " + (predicted_class === "healthy" ? "healthy" : "disease");

  confidenceLabel.textContent = T.confidenceLabel;

  confidenceBars.innerHTML = "";
  const sortedScores = Object.entries(all_scores).sort((a, b) => b[1] - a[1]);
  for (const [className, score] of sortedScores) {
    const row = document.createElement("div");
    row.className = "bar-row";

    const label = document.createElement("div");
    label.className = "bar-label";
    label.textContent = `${T.classNames[className]} — ${(score * 100).toFixed(1)}%`;

    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${(score * 100).toFixed(1)}%`;
    track.appendChild(fill);

    row.appendChild(label);
    row.appendChild(track);
    confidenceBars.appendChild(row);
  }

  if (predicted_class !== "healthy") {
    const severity = getSeverity(confidence);
    severityBlock.style.display = "block";
    severityBlock.style.borderLeftColor = SEVERITY_COLOR[severity];
    severityTitle.textContent = `${T.severityHeading}: ${SEVERITY_EMOJI[severity]} ${T.severityLabels[severity]}`;
    severityMsg.textContent = SEV_MSG[severity];
    severityDisclaimer.textContent = T.severityDisclaimer;
  } else {
    severityBlock.style.display = "none";
  }

  const info = INFO[predicted_class];
  if (info) {
    infoCard.style.display = "block";
    infoHeading.textContent = T.infoHeading;
    infoSummary.textContent = info.summary;
    infoPoints.innerHTML = "";
    for (const point of info.points) {
      const li = document.createElement("li");
      li.textContent = point;
      infoPoints.appendChild(li);
    }
  } else {
    infoCard.style.display = "none";
  }

  downloadReportBtn.style.display = "block";
  downloadReportBtn.textContent = T.downloadReportButton;
}

// --------------------------------------------------
// Events
// --------------------------------------------------

langEnBtn.addEventListener("click", () => {
  currentLang = "en";
  render();
});

langMrBtn.addEventListener("click", () => {
  currentLang = "mr";
  render();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;

  selectedFile = file;
  lastResult = null;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewWrap.style.display = "block";
    analyzeBtn.style.display = "block";
    render();
  };
  reader.readAsDataURL(file);
});

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  const T = TEXT[currentLang];
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = T.analyzing;

  const formData = new FormData();
  formData.append("image", selectedFile);

  try {
    const response = await fetch("/animal-health/predict", { method: "POST", headers: csrfHeaders(), body: formData });
    if (!response.ok) throw new Error("Request failed");
    const data = await response.json();
    lastResult = data;
  } catch (err) {
    alert(T.errorGeneric);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = T.analyzeButton;
    render();
  }
});

downloadReportBtn.addEventListener("click", async () => {
  if (!selectedFile || !lastResult) return;

  const T = TEXT[currentLang];
  const INFO = DISEASE_INFO[currentLang];
  const SEV_MSG = SEVERITY_MESSAGES[currentLang];
  const { predicted_class, confidence, all_scores } = lastResult;
  const isHealthy = predicted_class === "healthy";
  const severity = isHealthy ? "" : getSeverity(confidence);
  const info = INFO[predicted_class];

  downloadReportBtn.disabled = true;
  downloadReportBtn.textContent = T.generatingReport;

  const scoresArr = Object.entries(all_scores)
    .sort((a, b) => b[1] - a[1])
    .map(([className, score]) => [T.classNames[className], `${(score * 100).toFixed(1)}%`]);

  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("report_title", T.navTitle);
  formData.append("generated_label", T.generatedLabel);
  formData.append("result_heading", T.resultHeading);
  formData.append("display_name", T.classNames[predicted_class]);
  formData.append("confidence_text", `${(confidence * 100).toFixed(1)}%`);
  formData.append("is_healthy", isHealthy ? "true" : "false");
  formData.append("confidence_label", T.confidenceLabel);
  formData.append("all_scores", JSON.stringify(scoresArr));
  formData.append("severity_heading", isHealthy ? "" : T.severityHeading);
  formData.append("severity_label", isHealthy ? "" : T.severityLabels[severity]);
  formData.append("severity_message", isHealthy ? "" : SEV_MSG[severity]);
  formData.append("info_heading", T.infoHeading);
  formData.append("info_summary", info ? info.summary : "");
  formData.append("info_points", JSON.stringify(info ? info.points : []));
  formData.append("disclaimer", T.footerText);

  try {
    const response = await fetch("/animal-health/generate_report", { method: "POST", headers: csrfHeaders(), body: formData });
    if (!response.ok) throw new Error("Request failed");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cattle_disease_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert(T.reportError);
  } finally {
    downloadReportBtn.disabled = false;
    downloadReportBtn.textContent = T.downloadReportButton;
  }
});

// Initial render
render();
