export const getApiBaseUrl = () => {
    // If we are on localhost, use the standard local backend
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return "http://127.0.0.1:8000/api";
    }
    // Otherwise, use the same hostname but on port 8000 (standard for our deployment)
    return `${window.location.protocol}//${window.location.hostname}:8000/api`;
};

export const API_BASE_URL = getApiBaseUrl();
