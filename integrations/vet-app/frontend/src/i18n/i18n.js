import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './en.json'
import mr from './mr.json'

const savedLanguage = localStorage.getItem('smartfarm-language') || 'en'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: en,
      },
      mr: {
        translation: mr,
      },
    },

    lng: savedLanguage,
    fallbackLng: 'en',

    interpolation: {
      escapeValue: false,
    },
  })

export default i18n