<template>
  <div class="csv-upload-container">
    <div class="card">
      <div class="card-header">
        <h3>Upload CSV File</h3>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <label for="csvFile" class="form-label">Select CSV File</label>
          <input 
            type="file" 
            class="form-control" 
            id="csvFile" 
            accept=".csv"
            @change="handleFileSelect"
            ref="fileInput"
          >
        </div>
        
        <div v-if="selectedFile" class="mb-3">
          <div class="alert alert-info">
            <strong>Selected file:</strong> {{ selectedFile.name }}
            <br>
            <strong>Size:</strong> {{ formatFileSize(selectedFile.size) }}
          </div>
        </div>

        <div v-if="uploadStatus" class="mb-3">
          <div :class="uploadStatusClass" role="alert">
            {{ uploadMessage }}
          </div>
        </div>

        <div class="d-grid gap-2 d-md-flex justify-content-md-end">
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="uploadFile"
            :disabled="!selectedFile || isUploading"
          >
            <span v-if="isUploading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ isUploading ? 'Uploading...' : 'Upload CSV' }}
          </button>
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="clearFile"
            :disabled="isUploading"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/authService'

export default {
  name: 'CSVUpload',
  data() {
    return {
      selectedFile: null,
      isUploading: false,
      uploadStatus: false,
      uploadMessage: '',
      uploadStatusClass: '',
      dataPerTrue: 100
    }
  },
  async mounted() {
    try {
      const res = await api.get('/config')
      if (typeof res.data?.dataPerTrue === 'number') {
        this.dataPerTrue = res.data.dataPerTrue
      }
    } catch (e) {
      // fallback to default 100
    }
  },
  methods: {
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
          this.showStatus('Please select a CSV file', 'alert-danger')
          return
        }
        this.selectedFile = file
        this.clearStatus()
      }
    },
    
    async uploadFile() {
      if (!this.selectedFile) return
      
      this.isUploading = true
      this.clearStatus()
      
      try {
        const formData = new FormData()
        formData.append('file', this.selectedFile)
        
        const response = await api.post('/upload-csv/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        const trueRows = this.dataPerTrue ? Math.round(response.data.rows / this.dataPerTrue) : response.data.rows
        this.showStatus(`Successfully uploaded! Processed ${trueRows} rows.`, 'alert-success')
        this.$emit('upload-success', response.data)
        
      } catch (error) {
        console.error('Upload error:', error)
        const errorMessage = error.response?.data?.detail || 'Upload failed. Please try again.'
        this.showStatus(errorMessage, 'alert-danger')
      } finally {
        this.isUploading = false
      }
    },
    
    clearFile() {
      this.selectedFile = null
      this.$refs.fileInput.value = ''
      this.clearStatus()
    },
    
    showStatus(message, className) {
      this.uploadMessage = message
      this.uploadStatusClass = className
      this.uploadStatus = true
    },
    
    clearStatus() {
      this.uploadStatus = false
      this.uploadMessage = ''
      this.uploadStatusClass = ''
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
  }
}
</script>

<style scoped>
.csv-upload-container {
  max-width: 600px;
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

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}
</style>
