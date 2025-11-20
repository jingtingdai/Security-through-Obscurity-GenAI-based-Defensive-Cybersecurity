<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <h4>Security through Obscurity</h4>
        </div>
        <div class="nav-links">
          <router-link to="/csv" class="nav-link">Data Management</router-link>
          <button @click="handleLogout" class="btn btn-outline-danger btn-sm">
            Logout
          </button>
        </div>
      </div>
    </nav>
    <router-view/>
  </div>
</template>

<script>
import { authService } from '@/services/authService'

export default {
  name: 'App',
  data() {
    return {
      isAuthenticated: false
    }
  },
  mounted() {
    this.checkAuthStatus()
  },
  methods: {
    checkAuthStatus() {
      // Only check if token exists - let the server validate expiration
      this.isAuthenticated = authService.isAuthenticated()
    },
    
    handleLogout() {
      authService.logout()
      this.isAuthenticated = false
      this.$router.push('/login')
    }
  },
  
  // Watch for route changes to update auth status
  watch: {
    $route() {
      this.checkAuthStatus()
    }
  },
  
  // Listen for login success events and storage changes
  created() {
    // Listen for storage changes (when localStorage is updated from other tabs)
    window.addEventListener('storage', (e) => {
      if (e.key === 'access_token') {
        this.checkAuthStatus()
      }
    })
    
    // Listen for custom login event (fired when login succeeds in same window)
    window.addEventListener('user-logged-in', () => {
      this.checkAuthStatus()
    })
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}

.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 1rem 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand h4 {
  color: white;
  margin: 0;
  font-weight: 600;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.router-link-exact-active {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-outline-danger {
  border-color: rgba(255, 255, 255, 0.5);
  color: white;
}

.btn-outline-danger:hover {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .nav-links {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
