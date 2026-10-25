import { useState, useCallback } from 'react'

export function useGeolocation() {
  const [location, setLocation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const getLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError(
        'Your browser does not support location access. Please search by district instead.'
      )
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude)
        const lon = Number(pos.coords.longitude)

        console.log('GPS coordinates:', {
          latitude: lat,
          longitude: lon,
        })

        // Basic coordinate validation
        if (
          !Number.isFinite(lat) ||
          !Number.isFinite(lon)
        ) {
          setLoading(false)
          setError(
            'Invalid location coordinates received. Please search by district/taluka instead.'
          )
          return
        }

        setLocation({
          lat,
          lon,
        })

        setLoading(false)
      },

      (err) => {
        setLoading(false)

        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError(
              'Location permission was denied. Please search by district/taluka below.'
            )
            break

          case err.POSITION_UNAVAILABLE:
            setError(
              'Your location could not be determined. Please search by district/taluka below.'
            )
            break

          case err.TIMEOUT:
            setError(
              'Location request timed out. Please try again or search by district.'
            )
            break

          default:
            setError(
              'Could not get your location. Please search by district/taluka below.'
            )
        }
      },

      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 60000,
      }
    )
  }, [])

  const clearLocation = useCallback(() => {
    setLocation(null)
    setError(null)
  }, [])

  return {
    location,
    loading,
    error,
    getLocation,
    clearLocation,
  }
}