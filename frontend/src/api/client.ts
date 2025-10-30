import axios from "axios";

// Detect if running on Pi (localhost) or accessing from desktop (use Pi's IP)
const API_BASE_URL =
  window.location.hostname === "localhost"
    ? "http://localhost:8000" // Accessing from Pi itself - NO /api prefix
    : `http://${window.location.hostname}:8000`; // Accessing from desktop using Pi's IP - NO /api prefix

// Base API client pointing to FastAPI backend on port 8000
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

export default apiClient;
