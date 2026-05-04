import axios from 'axios'

export const API_BASE_URL = 'https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export const setAuthToken = (token: string | null) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete apiClient.defaults.headers.common['Authorization']
  }
}
