import React from 'react'
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
} from 'react-leaflet'
import L from 'leaflet'
import { useTranslation } from 'react-i18next'
import { displayDistrict, displayFacilityType } from '../utils/locationLabels.js'

// Fix Leaflet default icon issue with Vite
delete L.Icon.Default.prototype._getIconUrl

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const userIcon = new L.Icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const dispensaryIcon = new L.Icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const clinicIcon = new L.Icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function VetMap({
  facilities,
  userLocation,
  radius,
  onMarkerClick,
}) {
  const { t, i18n } = useTranslation()

  const centre = userLocation
    ? [userLocation.lat, userLocation.lon]
    : [19.7515, 75.7139]

  return (
    <div
      style={{
        borderRadius: 12,
        overflow: 'hidden',
        border: '1.5px solid #e0e0e0',
      }}
    >
      <MapContainer
        center={centre}
        zoom={userLocation ? 11 : 7}
        style={{ height: 420, width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* User location */}
        {userLocation && (
          <>
            <Marker
              position={[userLocation.lat, userLocation.lon]}
              icon={userIcon}
            >
              <Popup>
                <strong>
                  📍 {t('veterinary.map.yourLocation')}
                </strong>
              </Popup>
            </Marker>

            <Circle
              center={[userLocation.lat, userLocation.lon]}
              radius={radius * 1000}
              pathOptions={{
                color: '#1565c0',
                fillColor: '#90caf9',
                fillOpacity: 0.1,
                weight: 1.5,
              }}
            />
          </>
        )}

        {/* Facility markers */}
        {facilities.map((f) => {
          const icon =
            f.facility_type === 'Veterinary Dispensary'
              ? dispensaryIcon
              : clinicIcon

          const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}`

          return (
            <Marker
              key={f.id}
              position={[f.latitude, f.longitude]}
              icon={icon}
              eventHandlers={{
                click: () =>
                  onMarkerClick &&
                  onMarkerClick(f),
              }}
            >
              <Popup maxWidth={240}>
                <strong
                  style={{
                    fontSize: '0.88rem',
                  }}
                >
                  {f.name}
                </strong>

                <br />

                <span
                  style={{
                    fontSize: '0.75rem',
                    color: '#555',
                  }}
                >
                  {displayFacilityType(f.facility_type, t)}
                </span>

                <br />

                {f.district !== 'Not available' && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                    }}
                  >
                      📍 {displayDistrict(f.district, i18n.language)}
                  </span>
                )}

                {f.distance_km !== undefined && (
                  <>
                    <br />

                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: '#2e7d32',
                        fontWeight: 600,
                      }}
                    >
                      📏 {f.distance_km} km{' '}
                      {t('veterinary.map.away')}
                    </span>
                  </>
                )}

                <br />

                <a
                  href={directionsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: '0.75rem',
                    color: '#1565c0',
                    fontWeight: 600,
                  }}
                >
                  🗺 {t('veterinary.map.getDirections')}
                </a>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>

      {/* Legend */}
      <div
        style={{
          padding: '10px 16px',
          background: '#f9f9f9',
          borderTop: '1px solid #e0e0e0',
          display: 'flex',
          gap: 20,
          flexWrap: 'wrap',
          fontSize: '0.78rem',
        }}
      >
        <LegendItem
          color="#1565c0"
          label={t('veterinary.map.yourLocation')}
        />

        <LegendItem
          color="#4caf50"
          label={t(
            'veterinary.map.veterinaryDispensary'
          )}
        />

        <LegendItem
          color="#f57c00"
          label={t(
            'veterinary.map.districtTalukaClinic'
          )}
        />
      </div>
    </div>
  )
}

function LegendItem({ color, label }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
      }}
    >
      <div
        style={{
          width: 12,
          height: 12,
          borderRadius: '50%',
          background: color,
        }}
      />

      <span style={{ color: '#555' }}>
        {label}
      </span>
    </div>
  )
}