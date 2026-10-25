import axios from 'axios'

const BASE = '/api/veterinary'

const api = axios.create({ baseURL: BASE, timeout: 15000 })

api.interceptors.response.use(
  r => r.data,
  err => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'Network error. Please try again.'
    return Promise.reject(new Error(msg))
  }
)

export const vetApi = {
  /** GET /nearby */
  getNearby: ({ latitude, longitude, radius = 25, limit = 10, facility_type }) =>
    api.get('/nearby', { params: { latitude, longitude, radius, limit, facility_type } }),

  /** GET /search/district */
  searchByDistrict: ({ district, taluka, facility_type, limit = 50 }) =>
    api.get('/search/district', { params: { district, taluka, facility_type, limit } }),

  /** GET /districts */
  getDistricts: () => api.get('/districts'),

  /** GET /talukas?district=X */
  getTalukas: (district) => api.get('/talukas', { params: { district } }),

  /** GET /stats */
  getStats: () => api.get('/stats'),

  /** GET /:id */
  getFacility: (id) => api.get(`/${id}`),

  /** POST /import  (admin) */
  importKml: () => api.post('/import'),
}
