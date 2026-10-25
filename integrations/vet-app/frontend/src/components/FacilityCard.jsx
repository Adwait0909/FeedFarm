import React from 'react'
import { useTranslation } from 'react-i18next'
import { displayDistrict, displayFacilityType } from '../utils/locationLabels.js'

function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const aLat = Number(lat1)
  const aLon = Number(lon1)
  const bLat = Number(lat2)
  const bLon = Number(lon2)

  if (
    !Number.isFinite(aLat) ||
    !Number.isFinite(aLon) ||
    !Number.isFinite(bLat) ||
    !Number.isFinite(bLon)
  ) {
    return null
  }

  const R = 6371

  const dLat = ((bLat - aLat) * Math.PI) / 180
  const dLon = ((bLon - aLon) * Math.PI) / 180

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((aLat * Math.PI) / 180) *
      Math.cos((bLat * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2

  const c =
    2 * Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    )

  return R * c
}

function formatDistance(distanceKm, t) {
  if (!Number.isFinite(distanceKm)) return null

  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)} ${t('veterinary.meter')}`
  }

  return `${distanceKm.toFixed(1)} ${t('veterinary.km')}`
}

export default function FacilityCard({
  facility,
  userLocation,
  onViewDetails,
}) {
  const { t, i18n } = useTranslation()

  if (!facility) return null

  let distanceKm = Number(facility.distance_km)

  // Calculate distance on frontend when required.
  const calculatedDistance =
    userLocation &&
    facility.latitude != null &&
    facility.longitude != null
      ? calculateDistanceKm(
          userLocation.lat,
          userLocation.lon,
          facility.latitude,
          facility.longitude
        )
      : null

  // If backend doesn't provide a distance,
  // or incorrectly returns 0 for different coordinates,
  // use the frontend Haversine calculation.
  if (
    !Number.isFinite(distanceKm) ||
    (
      distanceKm === 0 &&
      calculatedDistance != null &&
      calculatedDistance > 0.001
    )
  ) {
    distanceKm = calculatedDistance
  }

  const distanceLabel = formatDistance(distanceKm, t)

  const directionsUrl =
    `https://www.google.com/maps/dir/?api=1&destination=` +
    `${facility.latitude},${facility.longitude}`

  return (
    <article
      style={{
        background: '#fff',
        border: '1px solid #e0e0e0',
        borderRadius: 14,
        padding: 18,
        boxShadow: '0 2px 8px rgba(0,0,0,.06)',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ flex: 1 }}>
          <h3
            style={{
              margin: 0,
              color: '#1b5e20',
              fontSize: '1rem',
              lineHeight: 1.35,
            }}
          >
            🏥 {facility.name}
          </h3>

          <span
            style={{
              display: 'inline-block',
              marginTop: 7,
              padding: '4px 9px',
              borderRadius: 14,
              background: '#e8f5e9',
              color: '#2e7d32',
              fontSize: '0.72rem',
              fontWeight: 700,
            }}
          >
            {displayFacilityType(facility.facility_type, t) ||
              t('veterinary.modal.notAvailable')}
          </span>
        </div>

        {distanceLabel && (
          <span
            style={{
              flexShrink: 0,
              padding: '5px 9px',
              borderRadius: 14,
              background: '#e3f2fd',
              color: '#1565c0',
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            📍 {distanceLabel} {t('veterinary.card.away')}
          </span>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gap: 7,
          color: '#555',
          fontSize: '0.84rem',
        }}
      >
        <div>
          <strong>
            {t('veterinary.card.district')}:
          </strong>{' '}
          {displayDistrict(facility.district, i18n.language) ||
            t('veterinary.modal.notAvailable')}
        </div>

        {facility.taluka &&
          facility.taluka !== 'Not available' && (
            <div>
              <strong>
                {t('veterinary.modal.taluka')}:
              </strong>{' '}
              {facility.taluka}
            </div>
          )}

        <div>
          <strong>
            {t('veterinary.card.address')}:
          </strong>{' '}
          {facility.address ||
            t('veterinary.modal.notAvailable')}
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginTop: 'auto',
        }}
      >
        <button
          type="button"
          onClick={() => onViewDetails?.(facility)}
          style={{
            flex: 1,
            minWidth: 130,
            padding: '9px 12px',
            borderRadius: 8,
            border: 'none',
            background: '#2e7d32',
            color: '#fff',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {t('veterinary.card.viewDetails')}
        </button>

        <a
          href={directionsUrl}
          target="_blank"
          rel="noreferrer"
          style={{
            flex: 1,
            minWidth: 130,
            padding: '9px 12px',
            borderRadius: 8,
            border: '1px solid #2e7d32',
            color: '#2e7d32',
            fontWeight: 700,
            textAlign: 'center',
            background: '#fff',
          }}
        >
          {t('veterinary.card.getDirections')}
        </a>
      </div>
    </article>
  )
}