import React from 'react'
import { useTranslation } from 'react-i18next'

export default function LanguageToggle() {
  const { i18n } = useTranslation()

  const currentLanguage = i18n.language

  const changeLanguage = (language) => {
    i18n.changeLanguage(language)
    localStorage.setItem('smartfarm-language', language)
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        background: 'rgba(255,255,255,0.18)',
        borderRadius: 20,
        padding: 4,
        border: '1px solid rgba(255,255,255,0.3)',
      }}
    >
      <button
        onClick={() => changeLanguage('en')}
        style={{
          border: 'none',
          borderRadius: 16,
          padding: '6px 12px',
          background:
            currentLanguage === 'en'
              ? '#fff'
              : 'transparent',
          color:
            currentLanguage === 'en'
              ? '#2e7d32'
              : '#fff',
          fontWeight: 700,
          cursor: 'pointer',
          fontSize: '0.78rem',
        }}
      >
        EN
      </button>

      <button
        onClick={() => changeLanguage('mr')}
        style={{
          border: 'none',
          borderRadius: 16,
          padding: '6px 12px',
          background:
            currentLanguage === 'mr'
              ? '#fff'
              : 'transparent',
          color:
            currentLanguage === 'mr'
              ? '#2e7d32'
              : '#fff',
          fontWeight: 700,
          cursor: 'pointer',
          fontSize: '0.78rem',
        }}
      >
        मराठी
      </button>
    </div>
  )
}