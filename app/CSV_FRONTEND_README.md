# CSV Frontend Functionality

This document describes the newly added CSV upload and data display functionality in the Vue.js frontend.

## Features

### 1. CSV Upload Component (`CSVUpload.vue`)
- **File Selection**: Users can select CSV files from their computer
- **File Validation**: Only CSV files are accepted
- **Upload Progress**: Shows loading spinner during upload
- **Status Feedback**: Displays success/error messages
- **File Information**: Shows selected file name and size

### 2. Data Display Component (`DataDisplay.vue`)
- **Data Table**: Displays uploaded CSV data in a responsive table
- **Search Functionality**: Real-time search across all columns
- **Sorting**: Click column headers to sort data (ascending/descending)
- **Pagination**: Navigate through large datasets with configurable page sizes
- **Auto-refresh**: Automatically loads data when component mounts
- **Error Handling**: Displays user-friendly error messages

### 3. CSV View (`CSVView.vue`)
- **Integrated Interface**: Combines upload and display components
- **Instructions**: Provides user guidance
- **Responsive Layout**: Works on desktop and mobile devices
- **Real-time Updates**: Data display refreshes automatically after successful upload

## Navigation

The CSV functionality is accessible via:
- **URL**: `http://localhost:8080/csv`
- **Navigation Menu**: "CSV Data" link in the main navigation

## Backend Integration

The frontend integrates with existing backend endpoints:
- **Upload**: `POST /upload-csv/` - Uploads and processes CSV files
- **Data Retrieval**: `GET /real data/` - Retrieves processed data

## Technical Details

### Dependencies
- Vue 3 with Composition API
- Bootstrap 5 for styling
- Bootstrap Icons for UI elements
- Axios for HTTP requests

### File Structure
```
frontend/src/
├── components/
│   ├── CSVUpload.vue      # CSV upload component
│   └── DataDisplay.vue    # Data display component
├── views/
│   └── CSVView.vue        # Main CSV page
└── router/
    └── index.js           # Updated with CSV route
```

## Usage Instructions

1. **Start the Backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run serve
   ```

3. **Access the Application**:
   - Open `http://localhost:3000` in your browser
   - Click "CSV Data" in the navigation menu

4. **Upload CSV**:
   - Click "Select CSV File" and choose a CSV file
   - Click "Upload CSV" to process the file
   - Wait for success confirmation

5. **View Data**:
   - Data will automatically appear in the table below
   - Use search box to filter data
   - Click column headers to sort
   - Use pagination controls to navigate through data

## Features in Detail

### Upload Component Features
- File type validation (CSV only)
- File size display
- Upload progress indication
- Success/error status messages
- Clear file selection option

### Data Display Features
- Responsive table design
- Real-time search filtering
- Multi-column sorting
- Configurable pagination (10, 25, 50, 100 items per page)
- Page navigation (First, Previous, Next, Last)
- Entry count display
- Loading states and error handling

### Responsive Design
- Mobile-friendly layout
- Bootstrap grid system
- Collapsible navigation
- Touch-friendly controls

## Error Handling

The application handles various error scenarios:
- Invalid file types
- Empty CSV files
- Network errors
- Backend processing errors
- Large file uploads

All errors are displayed with user-friendly messages and appropriate styling.
