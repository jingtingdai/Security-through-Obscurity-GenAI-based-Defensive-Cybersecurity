<template>
  <div class="data-display-container">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h3>Data Display</h3>
        <button 
          class="btn btn-outline-primary btn-sm" 
          @click="loadData"
          :disabled="isLoading"
        >
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status"></span>
          {{ isLoading ? 'Loading...' : 'Refresh Data' }}
        </button>
      </div>
      <div class="card-body">
        
        <div v-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>
        
        <div v-if="!isLoading && data.length === 0 && !error" class="text-center text-muted py-4">
          <i class="bi bi-inbox" style="font-size: 3rem;"></i>
          <p class="mt-2">No data available. Upload a CSV file to see data here.</p>
        </div>
        
        <div v-if="data.length > 0">
          <div class="mb-3">
            <div class="row">
              <div class="col-md-6">
                <div class="input-group">
                  <span class="input-group-text">
                    <i class="bi bi-search"></i>
                  </span>
                  <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Search data..." 
                    v-model="searchTerm"
                  >
                </div>
              </div>
              <div class="col-md-6">
                <div class="input-group">
                  <span class="input-group-text">Show</span>
                  <select class="form-select" v-model="itemsPerPage">
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                  <span class="input-group-text">entries</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-dark">
                <tr>
                  <th v-for="column in columns" :key="column" @click="sortBy(column)" 
                      class="sortable" :class="{ 'sorted': sortColumn === column }">
                    {{ column }}
                    <i v-if="sortColumn === column" 
                       :class="sortDirection === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down'"
                       class="ms-1"></i>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in paginatedData" :key="index">
                  <td v-for="column in columns" :key="column">
                    {{ item[column] }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="d-flex justify-content-between align-items-center mt-3">
            <div class="text-muted">
              Showing {{ startIndex + 1 }} to {{ endIndex }} of {{ filteredData.length }} entries
            </div>
            <nav>
              <ul class="pagination pagination-sm mb-0">
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <button class="page-link" @click="currentPage = 1" :disabled="currentPage === 1">
                    First
                  </button>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <button class="page-link" @click="currentPage--" :disabled="currentPage === 1">
                    Previous
                  </button>
                </li>
                <li class="page-item" v-for="page in visiblePages" :key="page" 
                    :class="{ active: page === currentPage }">
                  <button class="page-link" @click="currentPage = page">
                    {{ page }}
                  </button>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <button class="page-link" @click="currentPage++" :disabled="currentPage === totalPages">
                    Next
                  </button>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <button class="page-link" @click="currentPage = totalPages" :disabled="currentPage === totalPages">
                    Last
                  </button>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/authService'

export default {
  name: 'DataDisplay',
  data() {
    return {
      data: [],
      isLoading: false,
      error: null,
      searchTerm: '',
      sortColumn: '',
      sortDirection: 'asc',
      currentPage: 1,
      itemsPerPage: 25
    }
  },
  computed: {
    columns() {
      if (this.data.length === 0) return []
      return Object.keys(this.data[0])
    },
    filteredData() {
      if (!this.searchTerm) return this.data
      
      const term = this.searchTerm.toLowerCase()
      return this.data.filter(item => 
        Object.values(item).some(value => 
          String(value).toLowerCase().includes(term)
        )
      )
    },
    sortedData() {
      if (!this.sortColumn) return this.filteredData
      
      return [...this.filteredData].sort((a, b) => {
        const aVal = a[this.sortColumn]
        const bVal = b[this.sortColumn]
        
        if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1
        return 0
      })
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.sortedData.slice(start, end)
    },
    totalPages() {
      return Math.ceil(this.filteredData.length / this.itemsPerPage)
    },
    startIndex() {
      return (this.currentPage - 1) * this.itemsPerPage
    },
    endIndex() {
      return Math.min(this.startIndex + this.itemsPerPage, this.filteredData.length)
    },
    visiblePages() {
      const pages = []
      const start = Math.max(1, this.currentPage - 2)
      const end = Math.min(this.totalPages, this.currentPage + 2)
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    }
  },
  methods: {
    async loadData() {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await api.get('/real-data/')
        this.data = response.data
        this.currentPage = 1 // Reset to first page when loading new data
      } catch (error) {
        console.error('Error loading data:', error)
        this.error = error.response?.data?.detail || 'Failed to load data. Please try again.'
      } finally {
        this.isLoading = false
      }
    },
    sortBy(column) {
      if (this.sortColumn === column) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortColumn = column
        this.sortDirection = 'asc'
      }
      this.currentPage = 1 // Reset to first page when sorting
    }
  },
  mounted() {
    this.loadData()
  }
}
</script>

<style scoped>
.data-display-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: none;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background-color: rgba(54, 73, 196, 0.66);
}

.sorted {
  background-color: rgba(12, 61, 208, 0.81);
}

.table th {
  border-top: none;
  font-weight: 600;
}

.table-responsive {
  max-height: 600px;
  overflow-y: auto;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

.pagination .page-link {
  color: #0d6efd;
  border-color: #dee2e6;
}

.pagination .page-item.active .page-link {
  background-color:rgba(145, 146, 150, 0.81);
  border-color:rgb(76, 77, 79);
}

.pagination .page-item.disabled .page-link {
  color: #6c757d;
  background-color: #fff;
  border-color: #dee2e6;
}
</style>
