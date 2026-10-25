// Marathi display labels for district names. API values remain canonical English
// identifiers so search requests continue to match the source records.
const MARATHI_DISTRICTS = {
  ahilyanagar: 'अहिल्यानगर', akola: 'अकोला', amravati: 'अमरावती', beed: 'बीड',
  ahmednagar: 'अहिल्यानगर', aurangabad: 'छत्रपती संभाजीनगर',
  bhandara: 'भंडारा', buldhana: 'बुलढाणा', chandrapur: 'चंद्रपूर',
  'chhatrapati sambhajinagar': 'छत्रपती संभाजीनगर', dharashiv: 'धाराशिव',
  'ch. sambhajinagar': 'छत्रपती संभाजीनगर',
  'ch.sambhajinagar': 'छत्रपती संभाजीनगर',
  'chh. sambhajinagar': 'छत्रपती संभाजीनगर',
  'chh.sambhajinagar': 'छत्रपती संभाजीनगर',
  dhule: 'धुळे', gadchiroli: 'गडचिरोली', gondia: 'गोंदिया', hingoli: 'हिंगोली',
  jalgaon: 'जळगाव', jalna: 'जालना', kolhapur: 'कोल्हापूर', latur: 'लातूर',
  nagpur: 'नागपूर', nanded: 'नांदेड', nandurbar: 'नंदुरबार', nashik: 'नाशिक',
  palghar: 'पालघर', parbhani: 'परभणी', pune: 'पुणे', raigad: 'रायगड',
  ratnagiri: 'रत्नागिरी', sangli: 'सांगली', satara: 'सातारा', sindhudurg: 'सिंधुदुर्ग',
  solapur: 'सोलापूर', thane: 'ठाणे', wardha: 'वर्धा', washim: 'वाशिम', yavatmal: 'यवतमाळ',
  'mumbai city': 'मुंबई शहर', 'mumbai suburban': 'मुंबई उपनगर',
};

const FACILITY_TYPE_KEYS = {
  'veterinary dispensary': 'veterinary.facilityType.dispensary',
  'district veterinary polyclinic': 'veterinary.facilityType.districtClinic',
  'taluka veterinary clinic': 'veterinary.facilityType.talukaClinic',
  'district/taluka veterinary clinic': 'veterinary.facilityType.generalClinic',
};

export function displayDistrict(value, language) {
  if (!value) return value;
  return language === 'mr' ? (MARATHI_DISTRICTS[String(value).trim().toLowerCase()] || value) : value;
}

export function displayFacilityType(value, translate) {
  if (!value) return value;
  const key = FACILITY_TYPE_KEYS[String(value).trim().toLowerCase()];
  return key && translate ? translate(key) : value;
}
