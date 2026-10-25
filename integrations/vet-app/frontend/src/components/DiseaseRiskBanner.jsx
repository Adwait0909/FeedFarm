import React from 'react'

/**
 * DiseaseRiskBanner
 *
 * Integrates with your existing livestock disease-risk module.
 * Pass `riskLevel` as "low" | "moderate" | "high" | "critical".
 * Pass `onFindVet` callback to open the vet finder with current location.
 */
export default function DiseaseRiskBanner({ riskLevel, animalName, onFindVet }) {
  if (!riskLevel) return null

  const config = {
    low: {
      bg: '#e8f5e9', border: '#4caf50', icon: '✅',
      color: '#2e7d32',
      title: 'Low Risk',
      message: 'Continue monitoring the animal. No immediate action required.',
      showBtn: false,
    },
    moderate: {
      bg: '#fff3e0', border: '#f57c00', icon: '⚠️',
      color: '#e65100',
      title: 'Moderate Risk',
      message: 'Veterinary consultation is recommended for this animal.',
      showBtn: true,
      btnLabel: '🔍 Find Nearby Vet',
      btnBg: '#f57c00',
    },
    high: {
      bg: '#ffebee', border: '#c62828', icon: '🚨',
      color: '#b71c1c',
      title: 'High Risk',
      message: 'Immediate veterinary assistance is strongly recommended.',
      showBtn: true,
      btnLabel: '🚨 Find Nearby Veterinary Help',
      btnBg: '#c62828',
    },
    critical: {
      bg: '#ffebee', border: '#b71c1c', icon: '🚨',
      color: '#b71c1c',
      title: 'Critical Risk',
      message: 'Seek immediate veterinary assistance without delay.',
      showBtn: true,
      btnLabel: '🚨 Find Emergency Vet Now',
      btnBg: '#b71c1c',
    },
  }

  const c = config[riskLevel.toLowerCase()] || config.low

  return (
    <div style={{
      background: c.bg,
      border: `1.5px solid ${c.border}`,
      borderRadius: 12,
      padding: '16px 20px',
      marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <span style={{ fontSize: 24, flexShrink: 0 }}>{c.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, color: c.color, marginBottom: 4, fontSize: '1rem' }}>
            AI Assessment: {c.title}
            {animalName && <span style={{ fontWeight: 400, color: '#555' }}> — {animalName}</span>}
          </div>
          <p style={{ color: '#444', fontSize: '0.88rem', marginBottom: c.showBtn ? 12 : 0 }}>
            {c.message}
          </p>
          {c.showBtn && (
            <button
              onClick={onFindVet}
              style={{
                background: c.btnBg, color: '#fff',
                border: 'none', borderRadius: 8,
                padding: '9px 18px', fontWeight: 700,
                fontSize: '0.88rem', cursor: 'pointer',
              }}
            >
              {c.btnLabel}
            </button>
          )}
        </div>
      </div>
      <p style={{
        marginTop: 10, fontSize: '0.72rem', color: '#888',
        fontStyle: 'italic',
      }}>
        ⚠️ This AI assessment is for informational purposes only and does not replace professional veterinary advice.
      </p>
    </div>
  )
}
