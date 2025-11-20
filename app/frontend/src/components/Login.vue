<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>Login</h2>
        <p class="text-muted">Sign in to access the system</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input 
            type="text" 
            class="form-control" 
            id="username"
            v-model="form.username"
            :class="{ 'is-invalid': errors.username }"
            placeholder="Enter your username"
            required
          >
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username }}
          </div>
        </div>
        
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input 
            type="password" 
            class="form-control" 
            id="password"
            v-model="form.password"
            :class="{ 'is-invalid': errors.password }"
            placeholder="Enter your password"
            required
          >
          <div v-if="errors.password" class="invalid-feedback">
            {{ errors.password }}
          </div>
        </div>
        
        <div v-if="errorMessage" class="alert alert-danger" role="alert">
          {{ errorMessage }}
        </div>
        
        <div class="d-grid">
          <button 
            type="submit" 
            class="btn btn-primary btn-lg"
            :disabled="isLoading"
            @click.prevent="handleLogin"
          >
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ isLoading ? 'Signing in...' : 'Sign In' }}
          </button>
        </div>
      </form>
      
      <div class="login-footer">
        <p class="text-muted small">
          Contact your administrator for access
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { authService } from '@/services/authService'

export default {
  name: 'LoginPage',
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      errors: {},
      errorMessage: '',
      isLoading: false
    }
  },
  mounted() {
    console.log('=== Login component MOUNTED ===')
    console.log('Component instance:', this)
    console.log('handleLogin method exists:', typeof this.handleLogin === 'function')
  },
  methods: {
    validateForm() {
      this.errors = {}
      
      if (!this.form.username.trim()) {
        this.errors.username = 'Username is required'
      }
      
      if (!this.form.password) {
        this.errors.password = 'Password is required'
      }
      
      return Object.keys(this.errors).length === 0
    },
    
    async handleLogin() {
      console.log('=== handleLogin CALLED ===')
      console.log('Form data:', { username: this.form.username, password: '***' })
      
      if (!this.validateForm()) {
        console.warn('Form validation failed')
        return
      }
      
      console.log('Form validation passed')
      this.isLoading = true
      this.errorMessage = ''
      
      try {
        console.log('=== LOGIN START ===')
        console.log('Attempting login for:', this.form.username)
        
        const response = await authService.login(this.form.username, this.form.password)
        console.log('Login response received:', response)
        console.log('Response type:', typeof response)
        console.log('Response keys:', Object.keys(response || {}))
        
        // Check if response has the required fields
        if (!response || !response.access_token) {
          console.error('ERROR: No access token in response')
          console.error('Full response:', JSON.stringify(response, null, 2))
          throw new Error('No access token received')
        }
        
        console.log('Access token found, length:', response.access_token.length)
        
        // Store token and user info
        console.log('Storing token to localStorage...')
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('token_type', response.token_type || 'Bearer')
        localStorage.setItem('user', JSON.stringify({
          username: this.form.username
        }))
        
        console.log('Token stored successfully')
        console.log('Token preview:', response.access_token.substring(0, 20) + '...')
        
        // Verify token is stored
        console.log('Verifying token was stored...')
        const token = localStorage.getItem('access_token')
        console.log('Retrieved token from localStorage:', token ? 'YES (length: ' + token.length + ')' : 'NO')
        
        if (!token) {
          console.error('ERROR: Token was not stored properly')
          throw new Error('Token was not stored properly')
        }
        
        console.log('Token verified successfully')
        console.log('Current location:', window.location.href)
        
        // Double-check token is still in localStorage before redirect
        const finalTokenCheck = localStorage.getItem('access_token')
        console.log('Final token check before redirect:', finalTokenCheck ? 'YES' : 'NO')
        
        if (!finalTokenCheck) {
          console.error('CRITICAL: Token disappeared from localStorage!')
          throw new Error('Token was lost from localStorage')
        }
        
        // Force a synchronous write to ensure localStorage is persisted
        // Some browsers need a small delay for localStorage to be fully written
        console.log('About to redirect to /csv')
        console.log('=== BEFORE REDIRECT ===')
        
        // Use a small delay to ensure localStorage is fully persisted
        // Then do a hard redirect
        setTimeout(() => {
          // Final verification
          const lastCheck = localStorage.getItem('access_token')
          if (!lastCheck) {
            console.error('Token still not found after delay!')
            alert('Error: Token was not saved. Please try logging in again.')
            return
          }
          
          console.log('Redirecting now with token in localStorage')
          // CRITICAL: Use window.location for hard redirect
          window.location.href = '/csv'
        }, 100)
        
      } catch (error) {
        console.error('=== LOGIN ERROR CAUGHT ===')
        console.error('Error object:', error)
        console.error('Error message:', error.message)
        console.error('Error stack:', error.stack)
        console.error('Error response:', error.response)
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          config: error.config
        })
        
        this.isLoading = false
        
        if (error.response?.status === 401) {
          this.errorMessage = 'Invalid username or password'
          console.error('401 Unauthorized - Invalid credentials')
        } else if (error.response?.status === 422) {
          this.errorMessage = 'Please check your input and try again'
          console.error('422 Validation Error')
        } else if (error.response?.status === 500) {
          this.errorMessage = 'Server error. Please try again later.'
          console.error('500 Server Error')
        } else if (!error.response) {
          this.errorMessage = 'Cannot connect to server. Is the backend running?'
          console.error('No response from server - connection error')
        } else {
          this.errorMessage = `Login failed: ${error.message || 'Unknown error'}`
          console.error('Other error:', error.message)
        }
        console.error('=== END ERROR ===')
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h2 {
  color: #333;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.login-form {
  margin-bottom: 1.5rem;
}

.form-control {
  border-radius: 8px;
  border: 1px solid #ddd;
  padding: 12px 16px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.7;
  transform: none;
}

.login-footer {
  text-align: center;
  border-top: 1px solid #eee;
  padding-top: 1rem;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

.alert {
  border-radius: 8px;
  border: none;
}

.invalid-feedback {
  display: block;
  font-size: 0.875rem;
  color: #dc3545;
}

.is-invalid {
  border-color: #dc3545;
}

@media (max-width: 480px) {
  .login-container {
    padding: 10px;
  }
  
  .login-card {
    padding: 1.5rem;
  }
}
</style>
