import { authService } from '@/services/authService'

export const authGuard = {
  // Check if route requires authentication
  requiresAuth(to, from, next) {
    const token = authService.getToken()
    const isAuthenticated = authService.isAuthenticated()
    
    console.log('Auth guard check:', { 
      path: to.path,
      from: from.path,
      isAuthenticated, 
      hasToken: !!token,
      tokenPreview: token ? token.substring(0, 30) + '...' : 'none'
    })
    
    // Only check if token exists - let the server validate expiration
    // The server will return 401 if token is invalid, and axios interceptor will handle it
    if (!isAuthenticated) {
      console.warn('Auth guard: Access denied, redirecting to login - no token found')
      // Redirect to login
      next('/login')
    } else {
      console.log('Auth guard: Access granted to', to.path, '- token exists, server will validate')
      next()
    }
  },
  
  // Check if user is already authenticated (for login page)
  alreadyAuthenticated(to, from, next) {
    const isAuthenticated = authService.isAuthenticated()
    
    // Only check if token exists - let the server validate expiration
    if (isAuthenticated) {
      // User has a token, redirect to main page
      // Server will validate if token is still valid
      console.log('Auth guard: User already has token, redirecting to /csv')
      next('/csv')
    } else {
      next()
    }
  }
}
