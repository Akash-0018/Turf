// Debug logging system for slots management
const DEBUG = {
    ENABLED: true,
    LEVELS: {
        INFO: 'info',
        WARN: 'warn',
        ERROR: 'error',
        DEBUG: 'debug'
    },

    log: function(level, message, data = null) {
        if (!this.ENABLED) return;

        const timestamp = new Date().toISOString();
        const prefix = `[SLOTS ${level.toUpperCase()}] [${timestamp}]`;

        switch (level) {
            case this.LEVELS.INFO:
                console.info(prefix, message, data || '');
                break;
            case this.LEVELS.WARN:
                console.warn(prefix, message, data || '');
                break;
            case this.LEVELS.ERROR:
                console.error(prefix, message, data || '');
                break;
            case this.LEVELS.DEBUG:
                console.debug(prefix, message, data || '');
                break;
        }
    },

    info: function(message, data = null) {
        this.log(this.LEVELS.INFO, message, data);
    },

    warn: function(message, data = null) {
        this.log(this.LEVELS.WARN, message, data);
    },

    error: function(message, data = null) {
        this.log(this.LEVELS.ERROR, message, data);
    },

    debug: function(message, data = null) {
        this.log(this.LEVELS.DEBUG, message, data);
    }
};

// Function to track API calls
function trackApiCall(url, method, data = null) {
    DEBUG.info(`API Call: ${method} ${url}`, data);
    return {
        start: new Date(),
        end: function() {
            const duration = new Date() - this.start;
            DEBUG.info(`API Call Complete: ${method} ${url}`, {
                duration: `${duration}ms`,
                data: data
            });
        }
    };
}

// Function to track slot operations
function trackSlotOperation(operation, slotData) {
    DEBUG.debug(`Slot Operation: ${operation}`, slotData);
}

// Function to track UI updates
function trackUiUpdate(element, action) {
    DEBUG.debug(`UI Update: ${action}`, {
        element: element.id || element.className || 'unknown',
        timestamp: new Date().toISOString()
    });
}

// Function to track errors
function trackError(context, error) {
    DEBUG.error(`Error in ${context}`, {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
    });
}

// Facility tracking functions
function trackFacilities() {
    const facilities = document.querySelectorAll('.facility-card');
    DEBUG.info('Facilities Found:', {
        count: facilities.length,
        visible: Array.from(facilities).filter(f => f.style.display !== 'none').length
    });

    facilities.forEach((facility, index) => {
        DEBUG.debug(`Facility ${index + 1}:`, {
            name: facility.dataset.name,
            sports: facility.dataset.sports,
            displayed: facility.style.display !== 'none',
            hasImage: facility.querySelector('.facility-image')?.src || 'No image'
        });
    });
}

// Initialize debug tracking
document.addEventListener('DOMContentLoaded', function() {
    DEBUG.info('Page loaded, initializing debug tracking');
    trackFacilities();

    // Track facility filtering
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            DEBUG.info('Filter applied');
            trackFacilities();
        });
    }

    // Track slot loading
    const viewSlotButtons = document.querySelectorAll('.view-slots');
    viewSlotButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const facilityId = btn.dataset.facilityId;
            DEBUG.info('View slots clicked for facility:', { facilityId });
        });
    });
});

// Export functions if using modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DEBUG,
        trackApiCall,
        trackSlotOperation,
        trackUiUpdate,
        trackError,
        trackFacilities
    };
}
