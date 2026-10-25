import React, {
  useState,
  useEffect,
  useCallback,
} from 'react'

import { useTranslation } from 'react-i18next'
import { displayDistrict } from '../utils/locationLabels.js'
import { vetApi } from '../services/veterinaryApi.js'
import { useGeolocation } from '../hooks/useGeolocation.js'
import LanguageToggle from './LanguageToggle.jsx'
import FacilityCard from './FacilityCard.jsx'
import FacilityDetailModal from './FacilityDetailModal.jsx'
import VetMap from './VetMap.jsx'
import DiseaseRiskBanner from './DiseaseRiskBanner.jsx'


// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const RADIUS_OPTIONS = [5, 10, 25, 50]


// ─────────────────────────────────────────────────────────────────────────────
// Distance Calculation
// ─────────────────────────────────────────────────────────────────────────────

const calculateDistanceKm = (
  lat1,
  lon1,
  lat2,
  lon2
) => {
  const R = 6371

  const dLat =
    ((lat2 - lat1) * Math.PI) / 180

  const dLon =
    ((lon2 - lon1) * Math.PI) / 180

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2

  const c =
    2 *
    Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    )

  return R * c
}


// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function VeterinaryLocator({
  riskLevel = null,
  animalName = null,
}) {

  const { t, i18n } = useTranslation()

  const TYPE_FILTERS = [
    {
      label: t('veterinary.filters.all'),
      value: null,
    },
    {
      label: t(
        'veterinary.filters.dispensaries'
      ),
      value: 'Veterinary Dispensary',
    },
    {
      label: t(
        'veterinary.filters.districtClinics'
      ),
      value: 'District Veterinary Polyclinic',
    },
    {
      label: t(
        'veterinary.filters.talukaClinics'
      ),
      value: 'Taluka Veterinary Clinic',
    },
  ]


  // ───────────────────────────────────────────────────────────────────────────
  // Geolocation
  // ───────────────────────────────────────────────────────────────────────────

  const {
    location,
    loading: geoLoading,
    error: geoError,
    getLocation,
  } = useGeolocation()


  // ───────────────────────────────────────────────────────────────────────────
  // Search state
  // ───────────────────────────────────────────────────────────────────────────

  const [radius, setRadius] =
    useState(25)

  const [typeFilter, setTypeFilter] =
    useState(null)

  const [facilities, setFacilities] =
    useState([])

  const [searching, setSearching] =
    useState(false)

  const [searchError, setSearchError] =
    useState(null)

  const [hasSearched, setHasSearched] =
    useState(false)

  const [searchMode, setSearchMode] =
    useState('nearby')


  // ───────────────────────────────────────────────────────────────────────────
  // District / Taluka state
  // ───────────────────────────────────────────────────────────────────────────

  const [useDistrict, setUseDistrict] =
    useState(false)

  const [districts, setDistricts] =
    useState([])

  const [talukas, setTalukas] =
    useState([])

  const [selDistrict, setSelDistrict] =
    useState('')

  const [selTaluka, setSelTaluka] =
    useState('')

  const [distLoading, setDistLoading] =
    useState(false)


  // ───────────────────────────────────────────────────────────────────────────
  // UI state
  // ───────────────────────────────────────────────────────────────────────────

  const [selectedFacility, setSelectedFacility] =
    useState(null)

  const [showMap, setShowMap] =
    useState(true)

  const [stats, setStats] =
    useState(null)


  // ───────────────────────────────────────────────────────────────────────────
  // Load districts + statistics
  // ───────────────────────────────────────────────────────────────────────────

  useEffect(() => {

    vetApi
      .getDistricts()
      .then((data) => {
        setDistricts(
          Array.isArray(data)
            ? data
            : []
        )
      })
      .catch(() => {
        setDistricts([])
      })


    vetApi
      .getStats()
      .then((data) => {
        setStats(data)
      })
      .catch(() => {
        setStats(null)
      })

  }, [])


  // ───────────────────────────────────────────────────────────────────────────
  // Load talukas when district changes
  // ───────────────────────────────────────────────────────────────────────────

  useEffect(() => {

    if (!selDistrict) {
      setTalukas([])
      setSelTaluka('')
      return
    }

    setDistLoading(true)

    vetApi
      .getTalukas(selDistrict)
      .then((data) => {
        setTalukas(
          Array.isArray(data)
            ? data
            : []
        )
        setSelTaluka('')
      })
      .catch(() => {
        setTalukas([])
      })
      .finally(() => {
        setDistLoading(false)
      })

  }, [selDistrict])


  // ───────────────────────────────────────────────────────────────────────────
  // Nearby search
  // ───────────────────────────────────────────────────────────────────────────

const doNearbySearch = useCallback(
  async (loc, rad, type) => {
    if (!loc) return

    const latitude = Number(loc.lat)
    const longitude = Number(loc.lon)

    // Validate coordinates before calling backend
    if (
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude)
    ) {
      setSearchError(
        'Invalid location coordinates. Please search by district/taluka instead.'
      )
      setFacilities([])
      return
    }

    // Maharashtra approximate bounds
    const isInMaharashtra =
      latitude >= 15 &&
      latitude <= 23 &&
      longitude >= 72 &&
      longitude <= 81

    if (!isInMaharashtra) {
      console.warn(
        'GPS location is outside Maharashtra:',
        {
          latitude,
          longitude,
        }
      )

      setSearchError(
        'Your current location appears to be outside Maharashtra. Please search by district/taluka instead.'
      )

      setFacilities([])
      setHasSearched(true)
      setSearching(false)

      return
    }

    setSearchMode('nearby')
    setUseDistrict(false)
    setSearching(true)
    setSearchError(null)
    setHasSearched(true)

    try {
      const res = await vetApi.getNearby({
        latitude,
        longitude,
        radius: Number(rad),
        limit: 50,
        facility_type: type || undefined,
      })

      setFacilities(
        Array.isArray(res?.facilities)
          ? res.facilities
          : []
      )

    } catch (err) {
      console.error(
        'Nearby search error:',
        err
      )

      setSearchError(
        err?.message ||
        'Unable to find nearby veterinary facilities.'
      )

      setFacilities([])

    } finally {
      setSearching(false)
    }
  },
  []
)


  // ───────────────────────────────────────────────────────────────────────────
  // Search when location changes
  // ───────────────────────────────────────────────────────────────────────────

  useEffect(() => {

    if (location) {
      doNearbySearch(
        location,
        radius,
        typeFilter
      )
    }

  }, [
    location,
    doNearbySearch,
  ])


  // ───────────────────────────────────────────────────────────────────────────
  // High-risk animal → request location
  // ───────────────────────────────────────────────────────────────────────────

  useEffect(() => {

    if (
      riskLevel &&
      (
        riskLevel === 'high' ||
        riskLevel === 'critical'
      )
    ) {

      if (
        !location &&
        !geoLoading
      ) {
        getLocation()
      }

    }

  }, [
    riskLevel,
    location,
    geoLoading,
    getLocation,
  ])


  // ───────────────────────────────────────────────────────────────────────────
  // District search
  // ───────────────────────────────────────────────────────────────────────────

  const doDistrictSearch = useCallback(
  async () => {
    if (!selDistrict) return

    setSearching(true)
    setSearchError(null)
    setHasSearched(true)

    try {
      const res = await vetApi.searchByDistrict({
        district: selDistrict,
        taluka: selTaluka || undefined,
        facility_type: typeFilter,
        limit: 100,
      })

      setFacilities(res?.facilities || [])

    } catch (err) {
      console.error(
        'District search error:',
        err
      )

      setSearchError(
        err?.message ||
          'Unable to search veterinary facilities.'
      )

      setFacilities([])

    } finally {
      setSearching(false)
    }
  },
  [selDistrict, selTaluka, typeFilter]
)

  // ───────────────────────────────────────────────────────────────────────────
  // Handle GPS button
  // ───────────────────────────────────────────────────────────────────────────

  const handleFindNearby = () => {

    setUseDistrict(false)
    setSearchMode('nearby')

    getLocation()

  }


  // ───────────────────────────────────────────────────────────────────────────
  // Handle radius change
  // ───────────────────────────────────────────────────────────────────────────

  const handleRadiusChange =
    (newRadius) => {

      setRadius(newRadius)

      if (location) {

        doNearbySearch(
          location,
          newRadius,
          typeFilter
        )

      }

    }


  // ───────────────────────────────────────────────────────────────────────────
  // Handle filter change
  // ───────────────────────────────────────────────────────────────────────────

  const handleTypeFilterChange =
    (newType) => {

      setTypeFilter(newType)

      if (
        searchMode === 'nearby' &&
        location
      ) {

        doNearbySearch(
          location,
          radius,
          newType
        )

      } else if (
        searchMode === 'district' &&
        selDistrict
      ) {

        setTimeout(() => {
          doDistrictSearch()
        }, 0)

      }

    }


  // ───────────────────────────────────────────────────────────────────────────
  // Filter facilities
  // ───────────────────────────────────────────────────────────────────────────

  const filteredFacilities =
    facilities.filter(
      (facility) => {

        if (!typeFilter) {
          return true
        }

        const facilityType =
          String(
            facility.facility_type ||
            ''
          ).toLowerCase()

        return facilityType ===
          typeFilter.toLowerCase()

      }
    )


  // ───────────────────────────────────────────────────────────────────────────
  // Map location
  // ───────────────────────────────────────────────────────────────────────────

  const mapUserLocation =
    location
      ? {
          lat: location.lat,
          lon: location.lon,
        }
      : null


  // ───────────────────────────────────────────────────────────────────────────
  // Results title
  // ───────────────────────────────────────────────────────────────────────────

  let resultsTitle =
    t(
      'veterinary.results.nearby',
      { radius }
    )

  if (searchMode === 'district') {

    if (selTaluka) {

      resultsTitle =
        t(
          'veterinary.results.districtTaluka',
          {
            district: selDistrict,
            taluka: selTaluka,
          }
        )

    } else {

      resultsTitle =
        t(
          'veterinary.results.district',
          {
            district: selDistrict,
          }
        )

    }

  }


  // ───────────────────────────────────────────────────────────────────────────
  // Render
  // ───────────────────────────────────────────────────────────────────────────

  return (

    <div
      style={{
        minHeight: '100vh',
        background: '#f1f8e9',
        paddingBottom: 40,
      }}
    >

      {/* Language toggle */}

      <div
  style={{
    display: 'flex',
    justifyContent: 'flex-end',
    marginBottom: 12,
  }}
>
  <LanguageToggle />
</div>


      {/* Header */}

      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '20px 24px 30px',
        }}
      >

        <div
          style={{
            background:
              'linear-gradient(135deg, #2e7d32, #66bb6a)',
            color: '#fff',
            borderRadius: 16,
            padding: '28px 30px',
            marginBottom: 20,
          }}
        >

          <h1
            style={{
              margin: '0 0 10px',
              fontSize: 'clamp(1.6rem, 4vw, 2.3rem)',
              fontWeight: 800,
            }}
          >
            🐄{' '}
            {t(
              'veterinary.title'
            )}
          </h1>

          <p
            style={{
              opacity: 0.88,
              fontSize: '0.95rem',
              maxWidth: 700,
              marginBottom: 20,
            }}
          >
            {t(
              'veterinary.description'
            )}
          </p>


          {/* Statistics */}

          {stats && (

            <div
              style={{
                display: 'flex',
                gap: 10,
                flexWrap: 'wrap',
                marginBottom: 20,
              }}
            >

              <StatChip
                value={stats.total}
                label={t(
                  'veterinary.stats.totalFacilities'
                )}
              />

              {stats.by_type &&
                Object.entries(
                  stats.by_type
                ).map(
                  ([type, count]) => (

                    <StatChip
                      key={type}
                      value={count}
                      label={type}
                    />

                  )
                )}

            </div>

          )}


          {/* Find near me */}

          <button
            onClick={handleFindNearby}
            disabled={geoLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '14px 28px',
              borderRadius: 10,
              background:
                geoLoading
                  ? 'rgba(255,255,255,.3)'
                  : '#fff',
              color:
                geoLoading
                  ? '#fff'
                  : '#2e7d32',
              border: 'none',
              fontWeight: 700,
              fontSize: '1rem',
              cursor:
                geoLoading
                  ? 'not-allowed'
                  : 'pointer',
              boxShadow:
                '0 2px 8px rgba(0,0,0,.2)',
            }}
          >

            {geoLoading
              ? t(
                  'veterinary.gettingLocation'
                )
              : `📍 ${t(
                  'veterinary.findNearMe'
                )}`}

          </button>


          {/* GPS error */}

          {geoError && (

            <div
              style={{
                marginTop: 12,
                background:
                  'rgba(255,255,255,.15)',
                borderRadius: 8,
                padding:
                  '10px 14px',
                fontSize: '0.85rem',
              }}
            >

              ⚠️ {geoError}

              <button
                onClick={() =>
                  setUseDistrict(true)
                }
                style={{
                  marginLeft: 10,
                  background: '#fff',
                  color: '#2e7d32',
                  border: 'none',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {t(
                  'veterinary.locationSearch'
                )}
              </button>

            </div>

          )}


          {/* Location obtained */}

          {location && (

            <div
              style={{
                marginTop: 10,
                fontSize: '0.82rem',
                opacity: 0.85,
              }}
            >
              ✅{' '}
              {t(
                'veterinary.locationObtained'
              )}
            </div>

          )}

        </div>


        {/* ───────────────────────────────────────────────────────────────
            District / Taluka Search
        ─────────────────────────────────────────────────────────────── */}

{true && (
          <div
            style={{
              background: '#fff',
              borderRadius: 12,
              padding: 20,
              border:
                '1.5px solid #e0e0e0',
              marginBottom: 20,
            }}
          >

            <h3
              style={{
                marginTop: 0,
                color: '#333',
              }}
            >
              🔎{' '}
              {t(
                'veterinary.searchByLocation'
              )}
            </h3>


            <div
              style={{
                display: 'grid',
                gridTemplateColumns:
                  'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 14,
              }}
            >

              <div>

                <label
                  style={{
                    display: 'block',
                    marginBottom: 6,
                    fontWeight: 600,
                    color: '#444',
                  }}
                >
                  {t(
                    'veterinary.district'
                  )}
                </label>

                <select
                  value={selDistrict}
                  onChange={(e) =>
                    setSelDistrict(
                      e.target.value
                    )
                  }
                  style={selectStyle}
                >

                  <option value="">
                    {t(
                      'veterinary.selectDistrict'
                    )}
                  </option>

                  {districts.map(
                    (district) => (

                      <option
                        key={district}
                        value={district}
                      >
                        {displayDistrict(district, i18n.language)}
                      </option>

                    )
                  )}

                </select>

              </div>


              <div>

                <label
                  style={{
                    display: 'block',
                    marginBottom: 6,
                    fontWeight: 600,
                    color: '#444',
                  }}
                >
                  {t(
                    'veterinary.taluka'
                  )}
                </label>

                <select
                  value={selTaluka}
                  onChange={(e) =>
                    setSelTaluka(
                      e.target.value
                    )
                  }
                  disabled={
                    !selDistrict ||
                    distLoading
                  }
                  style={selectStyle}
                >

                  <option value="">
                    {distLoading
                      ? t(
                          'veterinary.loadingTalukas'
                        )
                      : t(
                          'veterinary.allTalukas'
                        )}
                  </option>

                  {talukas.map(
                    (taluka) => (

                      <option
                        key={taluka}
                        value={taluka}
                      >
                        {taluka}
                      </option>

                    )
                  )}

                </select>

              </div>

            </div>


            <button
              onClick={doDistrictSearch}
              disabled={
                !selDistrict ||
                searching
              }
              style={{
                marginTop: 14,
                padding:
                  '10px 20px',
                borderRadius: 8,
                border: 'none',
                background:
                  '#2e7d32',
                color: '#fff',
                fontWeight: 700,
                cursor:
                  !selDistrict ||
                  searching
                    ? 'not-allowed'
                    : 'pointer',
              }}
            >
              {searching
                ? t(
                    'veterinary.searching'
                  )
                : t(
                    'veterinary.search'
                  )}
            </button>

          </div>

        )}


        {/* ───────────────────────────────────────────────────────────────
            Filters
        ─────────────────────────────────────────────────────────────── */}

        {hasSearched && (

          <div
            style={{
              background: '#fff',
              borderRadius: 12,
              padding: 16,
              marginBottom: 20,
              border:
                '1px solid #e0e0e0',
            }}
          >

            <div
              style={{
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
                alignItems: 'center',
              }}
            >

              {TYPE_FILTERS.map(
                (filter) => (

                  <button
                    key={
                      filter.value ||
                      'all'
                    }
                    onClick={() =>
                      handleTypeFilterChange(
                        filter.value
                      )
                    }
                    style={{
                      padding:
                        '8px 14px',
                      borderRadius: 20,
                      border:
                        '1.5px solid #ddd',
                      background:
                        typeFilter ===
                        filter.value
                          ? '#2e7d32'
                          : '#fff',
                      color:
                        typeFilter ===
                        filter.value
                          ? '#fff'
                          : '#555',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {filter.label}
                  </button>

                )
              )}


              {/* Radius */}

              {searchMode ===
                'nearby' && (

                <select
                  value={radius}
                  onChange={(e) =>
                    handleRadiusChange(
                      Number(
                        e.target.value
                      )
                    )
                  }
                  style={{
                    ...selectStyle,
                    width: 'auto',
                  }}
                >

                  {RADIUS_OPTIONS.map(
                    (r) => (

                      <option
                        key={r}
                        value={r}
                      >
                        {t(
                          'veterinary.radius'
                        )}{' '}
                        {r}{' '}
                        {t(
                          'veterinary.km'
                        )}
                      </option>

                    )
                  )}

                </select>

              )}

            </div>

          </div>

        )}


        {/* ───────────────────────────────────────────────────────────────
            Disease Risk
        ─────────────────────────────────────────────────────────────── */}

        {riskLevel && (

          <DiseaseRiskBanner
            riskLevel={riskLevel}
            animalName={animalName}
          />

        )}


        {/* Search status */}

        {hasSearched &&
          !searching && (

            <div
              style={{
                display: 'flex',
                justifyContent:
                  'space-between',
                alignItems: 'center',
                marginBottom: 16,
                gap: 10,
              }}
            >

              <div
                style={{
                  padding:
                    '7px 12px',
                  borderRadius: 20,
                  background:
                    searchMode ===
                    'nearby'
                      ? '#e8f5e9'
                      : '#e3f2fd',
                  color:
                    searchMode ===
                    'nearby'
                      ? '#2e7d32'
                      : '#1565c0',
                  fontSize:
                    '0.75rem',
                  fontWeight: 700,
                }}
              >
                {searchMode ===
                'nearby'
                  ? `📍 ${t(
                      'veterinary.nearMe'
                    )}`
                  : `🔎 ${t(
                      'veterinary.locationSearch'
                    )}`}
              </div>


              <button
                onClick={() =>
                  setShowMap(
                    (value) =>
                      !value
                  )
                }
                style={{
                  padding:
                    '7px 14px',
                  borderRadius: 20,
                  border:
                    '1.5px solid #e0e0e0',
                  background:
                    showMap
                      ? '#e3f2fd'
                      : '#fff',
                  color:
                    showMap
                      ? '#1565c0'
                      : '#555',
                  fontSize:
                    '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {showMap
                  ? `🗺 ${t(
                      'veterinary.hideMap'
                    )}`
                  : `🗺 ${t(
                      'veterinary.showMap'
                    )}`}
              </button>

            </div>

          )}


        {/* Loading */}

        {searching && (

          <div
            style={{
              textAlign: 'center',
              padding: 40,
              color: '#2e7d32',
              fontWeight: 600,
            }}
          >
            ⏳{' '}
            {t(
              'veterinary.findingFacilities'
            )}
          </div>

        )}


        {/* Error */}

        {searchError &&
          !searching && (

            <div
              style={{
                background: '#ffebee',
                border:
                  '1.5px solid #ef9a9a',
                borderRadius: 12,
                padding:
                  '18px 20px',
                marginBottom: 20,
              }}
            >

              <div
                style={{
                  fontWeight: 700,
                  color: '#c62828',
                  marginBottom: 8,
                }}
              >
                ⚠️{' '}
                {t(
                  'veterinary.errors.search'
                )}
              </div>

              <p
                style={{
                  color: '#444',
                  fontSize:
                    '0.9rem',
                }}
              >
                {searchError}
              </p>

            </div>

          )}


        {/* Map */}

        {showMap &&
          hasSearched &&
          !searching && (

            <div
              style={{
                marginBottom: 24,
              }}
            >

              <VetMap
                facilities={
                  filteredFacilities
                }
                userLocation={
                  mapUserLocation
                }
                radius={
                  searchMode ===
                  'nearby'
                    ? radius
                    : undefined
                }
                onMarkerClick={
                  setSelectedFacility
                }
              />

            </div>

          )}


        {/* Results */}

        {!searching &&
          hasSearched && (

            <>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent:
                    'space-between',
                  marginBottom: 16,
                }}
              >

                <h2
                  style={{
                    fontSize:
                      '1.1rem',
                    fontWeight: 700,
                    color: '#333',
                  }}
                >
                  {resultsTitle}
                </h2>

                <span
                  style={{
                    background:
                      filteredFacilities.length
                        ? '#e8f5e9'
                        : '#fff3e0',
                    color:
                      filteredFacilities.length
                        ? '#2e7d32'
                        : '#e65100',
                    border:
                      `1px solid ${
                        filteredFacilities.length
                          ? '#a5d6a7'
                          : '#ffcc80'
                      }`,
                    borderRadius: 20,
                    padding:
                      '4px 12px',
                    fontSize:
                      '0.82rem',
                    fontWeight: 700,
                  }}
                >
                  {filteredFacilities.length}{' '}
                  {t(
                    'veterinary.results.found'
                  )}
                </span>

              </div>


              {filteredFacilities.length ===
              0 ? (

                <EmptyState
                  searchMode={
                    searchMode
                  }
                  radius={radius}
                  onChangeRadius={
                    handleRadiusChange
                  }
                  location={!!location}
                />

              ) : (

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      'repeat(auto-fill, minmax(300px, 1fr))',
                    gap: 16,
                  }}
                >

                  {filteredFacilities.map(
                    (facility) => (

                      <FacilityCard
                        key={facility.id}
                        facility={facility}
                        userLocation={
                          mapUserLocation
                        }
                        onViewDetails={
                          setSelectedFacility
                        }
                      />

                    )
                  )}

                </div>

              )}

            </>

          )}


        {/* Modal */}

        {selectedFacility && (

          <FacilityDetailModal
            facility={
              selectedFacility
            }
            onClose={() =>
              setSelectedFacility(
                null
              )
            }
          />

        )}

      </div>

    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// Statistics Chip
// ─────────────────────────────────────────────────────────────────────────────

function StatChip({
  value,
  label,
}) {
  return (
    <div
      style={{
        background:
          'rgba(255,255,255,.2)',
        borderRadius: 20,
        padding: '4px 12px',
        fontSize: '0.8rem',
        color: '#fff',
      }}
    >
      <strong>
        {value?.toLocaleString()}
      </strong>{' '}
      {label}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// Empty State
// ─────────────────────────────────────────────────────────────────────────────

function EmptyState({
  searchMode,
  radius,
  onChangeRadius,
  location,
}) {

  const isNearby =
    searchMode === 'nearby'

  return (
    <div
      style={{
        textAlign: 'center',
        padding: '48px 24px',
        background: '#fff',
        borderRadius: 12,
        border:
          '1.5px dashed #e0e0e0',
      }}
    >

      <div
        style={{
          fontSize: 48,
          marginBottom: 12,
        }}
      >
        🔍
      </div>

      <h3
        style={{
          color: '#333',
          marginBottom: 8,
        }}
      >
        {tStatic(
          isNearby
            ? 'No facilities found'
            : 'No facilities found'
        )}
      </h3>

      <p
        style={{
          color: '#888',
          fontSize: '0.9rem',
          maxWidth: 380,
          margin:
            '0 auto 20px',
        }}
      >
        {isNearby
          ? `No veterinary facilities were found within ${radius} km. Try increasing the search radius.`
          : 'No facilities were found for the selected district or taluka. Try another location.'}
      </p>

      {isNearby &&
        location && (

          <div
            style={{
              display: 'flex',
              gap: 8,
              justifyContent:
                'center',
              flexWrap: 'wrap',
            }}
          >

            {[10, 25, 50]
              .filter(
                (r) => r > radius
              )
              .map((r) => (

                <button
                  key={r}
                  onClick={() =>
                    onChangeRadius(r)
                  }
                  style={{
                    padding:
                      '9px 18px',
                    borderRadius: 8,
                    background:
                      '#2e7d32',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 600,
                    cursor:
                      'pointer',
                  }}
                >
                  Try {r} km
                </button>

              ))}

          </div>

        )}

    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// Select styling
// ─────────────────────────────────────────────────────────────────────────────

const selectStyle = {
  width: '100%',
  padding: '10px 12px',
  border:
    '1.5px solid #ddd',
  borderRadius: 8,
  fontSize: '0.9rem',
  background: '#fff',
  color: '#333',
  outline: 'none',
}


// Small helper used by EmptyState
function tStatic(value) {
  return value
}