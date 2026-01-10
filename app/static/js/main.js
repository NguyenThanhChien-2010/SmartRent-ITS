// Main JavaScript for SmartRent ITS

// Utility functions
const Utils = {
    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    },
    
    // Format date
    formatDate(date) {
        return new Date(date).toLocaleDateString('vi-VN');
    },
    
    // Show notification
    showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    },
    
    // Get user location
    getUserLocation() {
        return new Promise((resolve, reject) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    }),
                    error => reject(error)
                );
            } else {
                reject(new Error('Geolocation not supported'));
            }
        });
    },
    
    // Calculate distance between two points (Haversine)
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth radius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon/2) * Math.sin(dLon/2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
};

// API calls
const API = {
    // Get nearby vehicles
    async getNearbyVehicles(lat, lng, radius = 5, type = 'all') {
        const response = await fetch(
            `/vehicles/api/nearby?lat=${lat}&lng=${lng}&radius=${radius}&type=${type}`
        );
        return response.json();
    },
    
    // Book vehicle
    async bookVehicle(vehicleId) {
        const response = await fetch(`/vehicles/${vehicleId}/book`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return response.json();
    },
    
    // Unlock vehicle
    async unlockVehicle(vehicleId) {
        const response = await fetch(`/vehicles/${vehicleId}/unlock`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return response.json();
    },
    
    // Lock vehicle
    async lockVehicle(vehicleId) {
        const response = await fetch(`/vehicles/${vehicleId}/lock`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return response.json();
    },
    
    // End trip
    async endTrip(tripId, data) {
        const response = await fetch(`/trips/${tripId}/end`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    // Report emergency
    async reportEmergency(data) {
        const response = await fetch('/emergency/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Export utilities
window.SmartRent = {
    Utils,
    API
};
