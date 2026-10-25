// src/crops.js

const crops = [
  {
    name_en: "Cotton",
    name_mr: "कापूस",
    region: "Vidarbha",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [10, 11],
  },
  {
    name_en: "Pigeon Pea",
    name_mr: "तूर",
    region: "Marathwada",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [10, 11],
  },
  {
    name_en: "Sorghum",
    name_mr: "ज्वारी",
    region: "Marathwada",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [9, 10],
  },
  {
    name_en: "Bajra",
    name_mr: "बाजरी",
    region: "Marathwada",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [9, 10],
  },
  {
    name_en: "Gram",
    name_mr: "हरभरा",
    region: "Marathwada",
    season: "Rabi",
    sowing: [10, 11],
    growing: [11, 12, 1, 2],
    harvesting: [3, 4],
  },
  {
    name_en: "Soybean",
    name_mr: "सोयाबीन",
    region: "Vidarbha",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [10, 11],
  },
  {
    name_en: "Groundnut",
    name_mr: "भुईमूग",
    region: "Marathwada",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [10, 11],
  },
  {
    name_en: "Onion",
    name_mr: "कांदा",
    region: "Western Maharashtra",
    season: "Rabi",
    sowing: [10, 11],
    growing: [11, 12, 1, 2],
    harvesting: [3, 4],
  },
  {
    name_en: "Wheat",
    name_mr: "गहू",
    region: "Marathwada",
    season: "Rabi",
    sowing: [10, 11],
    growing: [11, 12, 1, 2],
    harvesting: [3, 4],
  },
  {
    name_en: "Sunflower",
    name_mr: "सूर्यफूल",
    region: "Marathwada",
    season: "Zaid",
    sowing: [2, 3],
    growing: [3, 4, 5],
    harvesting: [5, 6],
  },
  {
    name_en: "Rice",
    name_mr: "तांदूळ",
    region: "Konkan",
    season: "Kharif",
    sowing: [6, 7],
    growing: [7, 8, 9],
    harvesting: [10, 11],
  },
  {
    "name_en": "Mango",
    "name_mr": "आंबा",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10, 11],
    "harvesting": [3, 4, 5, 6]
  },
  {
    "name_en": "Banana",
    "name_mr": "केळी",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Coconut",
    "name_mr": "नारळ",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Cashew",
    "name_mr": "काजू",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Pineapple",
    "name_mr": "अननस",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Jackfruit",
    "name_mr": "फणस",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Kokum",
    "name_mr": "कोकम",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Arecanut",
    "name_mr": "सुपारी",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Nutmeg",
    "name_mr": "जायफळ",
    "region": "Konkan",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Turmeric",
    "name_mr": "हळद",
    "region": "Western Maharashtra",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Sugarcane",
    "name_mr": "ऊस",
    "region": "Western Maharashtra",
    "season": "Annual",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "harvesting": [10, 11, 12]
  },
  {
    "name_en": "Grapes",
    "name_mr": "द्राक्ष",
    "region": "Western Maharashtra",
    "season": "Annual",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },

  {
    "name_en": "Pomegranate",
    "name_mr": "डाळिंब",
    "region": "Western Maharashtra",
    "season": "Annual",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10, 11],
    "harvesting": [12, 1, 2, 3, 4]
  },
  {
    "name_en": "Tomato",
    "name_mr": "टोमॅटो",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Brinjal",
    "name_mr": "वांगी",
    "region": "Western Maharashtra",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [9, 10]
  },
  {
    "name_en": "Cabbage",
    "name_mr": "कोबी",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Cauliflower",
    "name_mr": "फुलकोबी",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Chickpea",
    "name_mr": "हरभरा",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [3, 4]
  },
  {
    "name_en": "Orange",
    "name_mr": "संत्रा",
    "region": "Vidarbha",
    "season": "Annual",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10, 11],
    "harvesting": [12, 1, 2, 3]
  },
  {
    "name_en": "Tur Dal",
    "name_mr": "तूर डाळ",
    "region": "Vidarbha",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Chilli",
    "name_mr": "मिरची",
    "region": "Vidarbha",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Moong",
    "name_mr": "मूग",
    "region": "Vidarbha",
    "season": "Zaid",
    "sowing": [2, 3],
    "growing": [3, 4, 5],
    "harvesting": [5, 6]
  },
  {
    "name_en": "Urad",
    "name_mr": "उडीद",
    "region": "Vidarbha",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Linseed",
    "name_mr": "अळशी",
    "region": "Vidarbha",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [3, 4]
  },
  {
    "name_en": "Sesame",
    "name_mr": "तीळ",
    "region": "Vidarbha",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Mustard",
    "name_mr": "मोहरी",
    "region": "Vidarbha",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [3, 4]
  },
  {
    "name_en": "Apple",
    "name_mr": "सफरचंद",
    "region": "All",
    "season": "Varied",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10],
    "harvesting": [9, 10, 11]
  },
  {
    "name_en": "Guava",
    "name_mr": "पेरू",
    "region": "All",
    "season": "Varied",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5]
  },
  {
    "name_en": "Papaya",
    "name_mr": "पपई",
    "region": "All",
    "season": "Varied",
    "sowing": [2, 3],
    "growing": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "harvesting": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Strawberry",
    "name_mr": "स्ट्रॉबेरी",
    "region": "All",
    "season": "Varied",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3, 4]
  },
  {
    "name_en": "Lemon",
    "name_mr": "लिंबू",
    "region": "All",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10, 11],
    "harvesting": [12, 1, 2, 3]
  },
  {
    "name_en": "Sweet Lime",
    "name_mr": "मोसम्बी",
    "region": "All",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10, 11],
    "harvesting": [12, 1, 2, 3]
  },
  {
    "name_en": "Watermelon",
    "name_mr": "कलिंगड",
    "region": "All",
    "season": "Summer",
    "sowing": [2, 3, 4],
    "growing": [3, 4, 5, 6],
    "harvesting": [5, 6, 7]
  },
  {
    "name_en": "Muskmelon",
    "name_mr": "खरबूज",
    "region": "All",
    "season": "Summer",
    "sowing": [2, 3, 4],
    "growing": [3, 4, 5, 6],
    "harvesting": [5, 6, 7]
  },
  {
    "name_en": "Cucumber",
    "name_mr": "काकडी",
    "region": "All",
    "season": "Summer",
    "sowing": [2, 3, 4],
    "growing": [3, 4, 5, 6],
    "harvesting": [5, 6, 7]
  },
  {
    "name_en": "Pumpkin",
    "name_mr": "भोपळा",
    "region": "All",
    "season": "Summer",
    "sowing": [2, 3, 4],
    "growing": [3, 4, 5, 6],
    "harvesting": [5, 6, 7]
  },
  {
    "name_en": "Ladyfinger",
    "name_mr": "भेंडी",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9],
    "harvesting": [9, 10]
  },
  {
    "name_en": "Spinach",
    "name_mr": "पालक",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Fenugreek",
    "name_mr": "मेथी",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Carrot",
    "name_mr": "गाजर",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Radish",
    "name_mr": "मुळा",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Beetroot",
    "name_mr": "बीट",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Potato",
    "name_mr": "बटाटा",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Garlic",
    "name_mr": "लसूण",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Ginger",
    "name_mr": "आले",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Peas",
    "name_mr": "मटार",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Bottle Gourd",
    "name_mr": "दुधी भोपळा",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Bitter Gourd",
    "name_mr": "कारले",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Ridge Gourd",
    "name_mr": "शेवगा",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Cluster Beans",
    "name_mr": "गवार",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Cowpea",
    "name_mr": "चवळी",
    "region": "All",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },

  {
    "name_en": "Chilli (Green)",
    "name_mr": "हिरवी मिरची",
    "region": "All",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [9, 10, 11]
  },
  {
    "name_en": "Coriander",
    "name_mr": "कोथिंबीर",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Dill",
    "name_mr": "शेपू",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Mint",
    "name_mr": "पुदीना",
    "region": "All",
    "season": "Varied",
    "sowing": [6, 7, 10, 11],
    "growing": [7, 8, 9, 10, 11, 12],
    "harvesting": [9, 10, 11, 12]
  },
  {
    "name_en": "Tulsi",
    "name_mr": "तुळस",
    "region": "All",
    "season": "Varied",
    "sowing": [6, 7, 10, 11],
    "growing": [7, 8, 9, 10, 11, 12],
    "harvesting": [9, 10, 11, 12]
  },
  {
    "name_en": "Safflower",
    "name_mr": "कुसुम",
    "region": "All",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [11, 12, 1, 2],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Castor",
    "name_mr": "अर्गो",
    "region": "Vidarbha",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [7, 8, 9, 10],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Lemon",
    "name_mr": "लिंबू",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Sweet Lime",
    "name_mr": "मोसम्बी",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Watermelon",
    "name_mr": "कलिंगड",
    "region": "Marathwada",
    "season": "Zaid",
    "sowing": [1, 2],
    "growing": [3, 4],
    "harvesting": [5, 6]
  },
  {
    "name_en": "Muskmelon",
    "name_mr": "खरबूज",
    "region": "Western Maharashtra",
    "season": "Zaid",
    "sowing": [1, 2],
    "growing": [3, 4],
    "harvesting": [5, 6]
  },
  {
    "name_en": "Cucumber",
    "name_mr": "काकडी",
    "region": "Vidarbha",
    "season": "Zaid",
    "sowing": [1, 2],
    "growing": [3, 4],
    "harvesting": [5, 6]
  },
  {
    "name_en": "Pumpkin",
    "name_mr": "भोपळा",
    "region": "Marathwada",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Ladyfinger",
    "name_mr": "भेंडी",
    "region": "Vidarbha",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Spinach",
    "name_mr": "पालक",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Fenugreek",
    "name_mr": "मेथी",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Carrot",
    "name_mr": "गाजर",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Radish",
    "name_mr": "मुळा",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Beetroot",
    "name_mr": "बीट",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Potato",
    "name_mr": "बटाटा",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Garlic",
    "name_mr": "लसूण",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Ginger",
    "name_mr": "आले",
    "region": "Konkan",
    "season": "Kharif",
    "sowing": [5, 6],
    "growing": [7, 8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Peas",
    "name_mr": "मटार",
    "region": "Western Maharashtra",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Rose",
    "name_mr": "गुलाब",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11, 12]
  },
  {
    "name_en": "Chrysanthemum",
    "name_mr": "शेवंती",
    "region": "Marathwada",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Marigold",
    "name_mr": "झेंडू",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [5, 6],
    "growing": [7, 8],
    "harvesting": [9, 10, 11]
  },
  {
    "name_en": "Jasmine",
    "name_mr": "चमेली",
    "region": "Konkan",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9, 10],
    "harvesting": [11, 12, 1]
  },
  {
    "name_en": "Tuberose",
    "name_mr": "नागकेशर",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [4, 5],
    "growing": [6, 7, 8],
    "harvesting": [9, 10, 11, 12]
  },
  {
    "name_en": "Zinnia",
    "name_mr": "झिनिया",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  },
  {
    "name_en": "Lily",
    "name_mr": "कमळ",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [7],
    "growing": [8, 9],
    "harvesting": [10, 11, 12]
  },
  {
    "name_en": "Gerbera",
    "name_mr": "जर्बेरा",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [1, 2],
    "growing": [3, 4],
    "harvesting": [5, 6, 7, 8, 9, 10, 11, 12]
  },
  {
    "name_en": "Carnation",
    "name_mr": "कार्नेशन",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11, 12]
  },
  {
    "name_en": "Dolichos Bean",
    "name_mr": "वाल",
    "region": "Konkan",
    "season": "Rabi",
    "sowing": [10, 11],
    "growing": [12, 1],
    "harvesting": [2, 3]
  },
  {
    "name_en": "Snake Gourd",
    "name_mr": "पडवळ",
    "region": "Konkan",
    "season": "Kharif",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10]
  },
  {
    "name_en": "Amaranthus",
    "name_mr": "माठ",
    "region": "Western Maharashtra",
    "season": "Varied",
    "sowing": [6, 7],
    "growing": [8, 9],
    "harvesting": [10, 11]
  }
];

export default crops;
