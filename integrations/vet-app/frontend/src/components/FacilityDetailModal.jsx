import React from 'react'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { displayDistrict, displayFacilityType } from '../utils/locationLabels.js'

export default function FacilityDetailModal({
  facility,
  onClose,
}) {
  const { t, i18n } = useTranslation()

  if (!facility) return null

  const directionsUrl =
    `https://www.google.com/maps/dir/?api=1&destination=` +
    `${facility.latitude},${facility.longitude}`

  const mapsUrl =
    `https://www.google.com/maps?q=` +
    `${facility.latitude},${facility.longitude}`

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        background: 'rgba(0,0,0,.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 16,
          width: '100%',
          maxWidth: 560,
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow:
            '0 8px 40px rgba(0,0,0,.25)',
        }}
      >
        {/* Header */}
        <div
          style={{
            background:
              'linear-gradient(135deg, #2e7d32, #1b5e20)',
            color: '#fff',
            padding: '20px 24px',
            borderRadius:
              '16px 16px 0 0',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent:
              'space-between',
            gap: 12,
          }}
        >
          <div>
            <div
              style={{
                fontSize: '1.25rem',
                fontWeight: 700,
                lineHeight: 1.3,
                marginBottom: 4,
              }}
            >
              🏥 {facility.name}
            </div>

            <span
              style={{
                display: 'inline-block',
                background:
                  'rgba(255,255,255,.2)',
                borderRadius: 20,
                padding: '2px 10px',
                fontSize: '0.78rem',
                fontWeight: 600,
              }}
            >
              {displayFacilityType(facility.facility_type, t)}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label={t('common.close')}
            style={{
              background:
                'rgba(255,255,255,.15)',
              border: 'none',
              borderRadius: '50%',
              width: 36,
              height: 36,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              flexShrink: 0,
              cursor: 'pointer',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div
          style={{
            padding: '20px 24px',
          }}
        >
          {facility.distance_km !==
            undefined && (
            <div
              style={{
                background: '#e8f5e9',
                border:
                  '1px solid #a5d6a7',
                borderRadius: 8,
                padding: '10px 14px',
                marginBottom: 16,
                fontSize: '0.9rem',
                color: '#2e7d32',
                fontWeight: 600,
              }}
            >
              📏 {facility.distance_km}{' '}
              {t(
                'veterinary.modal.fromYourLocation'
              )}
            </div>
          )}

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <DetailRow
              label={t(
                'veterinary.modal.district'
              )}
              value={displayDistrict(facility.district, i18n.language)}
            />

            <DetailRow
              label={t(
                'veterinary.modal.taluka'
              )}
              value={facility.taluka}
            />

            <DetailRow
              label={t(
                'veterinary.modal.address'
              )}
              value={facility.address}
            />

            <DetailRow
              label={t(
                'veterinary.modal.department'
              )}
              value={facility.department}
            />

            <DetailRow
              label={t(
                'veterinary.modal.contact'
              )}
              value={facility.contact}
            />

            <DetailRow
              label={t(
                'veterinary.modal.openingHours'
              )}
              value={
                facility.opening_hours
              }
            />

            <DetailRow
              label={t(
                'veterinary.modal.coordinates'
              )}
              value={`${facility.latitude}° N, ${facility.longitude}° E`}
            />
          </div>

          {/* Action buttons */}
          <div
            style={{
              display: 'flex',
              gap: 10,
              marginTop: 20,
              flexWrap: 'wrap',
            }}
          >
            <a
              href={directionsUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1,
                minWidth: 140,
                display: 'flex',
                alignItems: 'center',
                justifyContent:
                  'center',
                gap: 8,
                padding: '11px 16px',
                background: '#1565c0',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontWeight: 600,
                fontSize: '0.9rem',
                textDecoration: 'none',
              }}
            >
              🗺{' '}
              {t(
                'veterinary.modal.getDirections'
              )}
            </a>

            <a
              href={mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1,
                minWidth: 140,
                display: 'flex',
                alignItems: 'center',
                justifyContent:
                  'center',
                gap: 8,
                padding: '11px 16px',
                background: '#e8f5e9',
                color: '#2e7d32',
                border:
                  '1.5px solid #a5d6a7',
                borderRadius: 8,
                fontWeight: 600,
                fontSize: '0.9rem',
                textDecoration: 'none',
              }}
            >
              📍{' '}
              {t(
                'veterinary.modal.viewOnMap'
              )}
            </a>
          </div>

          <p
            style={{
              marginTop: 16,
              fontSize: '0.75rem',
              color: '#999',
              textAlign: 'center',
              lineHeight: 1.4,
            }}
          >
            {t(
              'veterinary.modal.dataSource'
            )}
            <br />
            {t(
              'veterinary.modal.verifyDetails'
            )}
          </p>
        </div>
      </div>
    </div>
  )
}

function DetailRow({ label, value }) {
  const { t, i18n } = useTranslation()

  const isNA =
    !value ||
    value === 'Not available' ||
    value ===
      'Contact number not available' ||
    value ===
      'Opening hours not available'

  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '8px 0',
        borderBottom:
          '1px solid #f0f0f0',
        alignItems: 'flex-start',
      }}
    >
      <span
        style={{
          fontSize: '0.78rem',
          color: '#888',
          fontWeight: 600,
          width: 110,
          flexShrink: 0,
          paddingTop: 1,
        }}
      >
        {label}
      </span>

      <span
        style={{
          fontSize: '0.88rem',
          color: isNA ? '#bbb' : '#222',
          lineHeight: 1.4,
          flex: 1,
        }}
      >
        {value || t(
          'veterinary.modal.notAvailable'
        )}
      </span>
    </div>
  )
}