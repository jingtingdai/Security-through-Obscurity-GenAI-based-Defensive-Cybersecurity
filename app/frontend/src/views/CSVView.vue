<template>
  <div class="csv-view">
    <div class="container-fluid">
      <div class="row">
        <div class="col-12">
          <h1 class="mb-4">Security through Obscurity: GenAI-based Defensive Cybersecurity</h1>
          <p class="lead text-muted mb-4">
            Upload CSV files and retrieve data from database with advanced filtering and sorting capabilities.
          </p>
        </div>
      </div>
      
      <div class="row">
        <div class="col-lg-6 mb-4">
          <CSVUpload @upload-success="handleUploadSuccess" />
        </div>
        <div class="col-lg-6 mb-4">
          <div class="card">
            <div class="card-header">
              <h5>Instructions</h5>
            </div>
            <div class="card-body">
              <ol class="mb-0">
                <li>Select a CSV file from your computer</li>
                <li>Click "Upload CSV" to process the file</li>
                <li>View the processed data in the table below</li>
                <li>Use search to navigate through large datasets</li>
                <li>Click column headers to sort data</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row">
        <div class="col-12">
          <DataDisplay ref="dataDisplay" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CSVUpload from '@/components/CSVUpload.vue'
import DataDisplay from '@/components/DataDisplay.vue'

export default {
  name: 'CSVView',
  components: {
    CSVUpload,
    DataDisplay
  },
  methods: {
    handleUploadSuccess() {
      // Refresh the data display when upload is successful
      this.$refs.dataDisplay.loadData()
    }
  }
}
</script>

<style scoped>
.csv-view {
  padding: 20px 0;
}

.card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: none;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  font-weight: 600;
}

.lead {
  font-size: 1.1rem;
  font-weight: 300;
}

ol li {
  margin-bottom: 0.5rem;
}
</style>
