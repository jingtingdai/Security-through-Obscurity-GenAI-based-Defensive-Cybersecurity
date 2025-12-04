import { authService } from '@/services/authService'

export const authGuard = {
  // Check if route requires authentication
  requiresAuth(to, from, next) {
    const token = authService.getToken()
    const isAuthenticated = authService.isAuthenticated()
    const isExpired = authService.isTokenExpired()
    
    console.log('Auth guard check:', { 
      path: to.path,
      from: from.path,
      isAuthenticated, 
      hasToken: !!token,
      isExpired,
      tokenPreview: token ? token.substring(0, 30) + '...' : 'none'
    })
    
    // Check if token exists and is not expired
    if (!isAuthenticated || isExpired) {
      if (isExpired) {
        console.warn('Auth guard: Token expired, redirecting to login')
        authService.logout()
      } else {
        console.warn('Auth guard: Access denied, redirecting to login - no token found')
      }
      // Redirect to login
      next('/login')
    } else {
      console.log('Auth guard: Access granted to', to.path, '- token exists and is valid')
      next()
    }
  },
  
  // Check if user is already authenticated (for login page)
  alreadyAuthenticated(to, from, next) {
    const isAuthenticated = authService.isAuthenticated()
    const isExpired = authService.isTokenExpired()
    
    // Check if token exists and is not expired
    if (isAuthenticated && !isExpired) {
      // User has a valid token, redirect to main page
      console.log('Auth guard: User already has valid token, redirecting to /csv')
      next('/csv')
    } else {
      if (isExpired) {
        console.log('Auth guard: Token expired, clearing and staying on login page')
        authService.logout()
      }
      next()
    }
  }
}
