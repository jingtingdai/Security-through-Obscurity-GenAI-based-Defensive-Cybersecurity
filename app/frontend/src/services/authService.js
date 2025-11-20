import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Helper function to clear auth data
function clearAuthData() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
  localStorage.removeItem('user')
}

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only clear auth data on 401, but NOT if we're on the login page
    // (to avoid clearing token during login process)
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      console.log('Axios interceptor: 401 error, clearing auth data')
      // Token expired or invalid, clear auth data
      clearAuthData()
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const authService = {
  // Login user
  async login(username, password) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    
    const response = await api.post('/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    
    return response.data
  },
  
  // Get current user info
  async getCurrentUser() {
    const response = await api.get('/')
    return response.data
  },
  
  // Check if user is authenticated
  isAuthenticated() {
    const token = localStorage.getItem('access_token')
    return !!token
  },
  
  // Get stored token
  getToken() {
    return localStorage.getItem('access_token')
  },
  
  // Get stored user info
  getUser() {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  },
  
  // Logout user
  logout() {
    clearAuthData()
  },
  
  // Check if token is expired (basic check)
  isTokenExpired() {
    const token = this.getToken()
    if (!token) {
      console.log('isTokenExpired: No token found')
      return true
    }
    
    try {
      // Decode JWT token (basic decode, not verification)
      const parts = token.split('.')
      if (parts.length !== 3) {
        console.warn('isTokenExpired: Token does not have 3 parts, assuming valid (let server validate)')
        return false // Don't treat malformed tokens as expired, let the server handle it
      }
      
      const payload = JSON.parse(atob(parts[1]))
      const currentTime = Date.now() / 1000
      
      console.log('isTokenExpired: Decoded payload', { 
        hasExp: 'exp' in payload, 
        exp: payload.exp,
        expDate: payload.exp ? new Date(payload.exp * 1000).toISOString() : 'N/A',
        iat: payload.iat,
        iatDate: payload.iat ? new Date(payload.iat * 1000).toISOString() : 'N/A',
        currentTime: currentTime,
        currentDate: new Date(currentTime * 1000).toISOString(),
        payloadKeys: Object.keys(payload)
      })
      
      // If token doesn't have exp field, assume it's valid (let server handle it)
      if (!payload.exp) {
        console.warn('isTokenExpired: Token has no exp field, assuming valid (let server validate)')
        return false
      }
      
      // Check if token is expired
      const isExpired = payload.exp < currentTime
      const timeDiff = currentTime - payload.exp
      
      if (isExpired) {
        console.warn('isTokenExpired: Token appears expired', { 
          exp: payload.exp, 
          expDate: new Date(payload.exp * 1000).toISOString(),
          current: currentTime,
          currentDate: new Date(currentTime * 1000).toISOString(),
          diffSeconds: timeDiff,
          diffMinutes: Math.round(timeDiff / 60),
          diffHours: Math.round(timeDiff / 3600)
        })
        
        // If token expired less than 5 minutes ago, assume it's a clock sync issue
        // and let the server validate it (don't block access)
        if (timeDiff < 300) { // 5 minutes
          console.warn('isTokenExpired: Token expired recently (< 5 min), assuming clock sync issue - letting server validate')
          return false
        }
      } else {
        console.log('isTokenExpired: Token is valid', {
          exp: payload.exp,
          expDate: new Date(payload.exp * 1000).toISOString(),
          current: currentTime,
          currentDate: new Date(currentTime * 1000).toISOString(),
          remainingSeconds: payload.exp - currentTime,
          remainingMinutes: Math.round((payload.exp - currentTime) / 60)
        })
      }
      
      return isExpired
    } catch (error) {
      console.warn('isTokenExpired: Error decoding token, assuming valid (let server validate)', error)
      return false // Don't treat decode errors as expired, let the server handle it
    }
  }
}

export default api
