/// <reference types="vite/client" />
import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail
    if (detail) {
      err.message = Array.isArray(detail)
        ? detail.map((d: { msg: string }) => d.msg).join(', ')
        : String(detail)
    }
    return Promise.reject(err)
  }
)

export default apiClient
