/**
 * Security utilities for Logic-Guard-Layer
 * Provides XSS protection and safe DOM manipulation
 */

const Security = {
    /**
     * Escape HTML entities to prevent XSS attacks
     * @param {string} str - The string to escape
     * @returns {string} - The escaped string
     */
    escapeHtml: function(str) {
        if (str === null || str === undefined) {
            return '';
        }
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    /**
     * Create a text node (always safe)
     * @param {string} text - The text content
     * @returns {Text} - A text node
     */
    createText: function(text) {
        return document.createTextNode(String(text || ''));
    },

    /**
     * Safely set text content of an element
     * @param {HTMLElement} element - The target element
     * @param {string} text - The text to set
     */
    setText: function(element, text) {
        if (element) {
            element.textContent = String(text || '');
        }
    },

    /**
     * Create an element with safe text content
     * @param {string} tagName - The element tag name
     * @param {string} text - The text content
     * @param {string} className - Optional class name
     * @returns {HTMLElement} - The created element
     */
    createElement: function(tagName, text, className) {
        const el = document.createElement(tagName);
        if (text !== undefined && text !== null) {
            el.textContent = String(text);
        }
        if (className) {
            el.className = className;
        }
        return el;
    },

    /**
     * Create a violation card element safely
     * @param {Object} violation - The violation object
     * @param {boolean} isFixed - Whether the violation was fixed
     * @returns {HTMLElement} - The violation card element
     */
    createViolationCard: function(violation, isFixed) {
        const card = document.createElement('div');
        card.className = 'violation-card' + (isFixed ? ' fixed' : '');

        const typeEl = this.createElement('div', '[' + this.escapeHtml(violation.type) + ']', 'violation-type');
        const messageEl = this.createElement('div', violation.message, 'violation-message');

        const detailsEl = document.createElement('div');
        detailsEl.className = 'violation-details';

        const constraintSpan = this.createElement('span', 'Constraint: ' + violation.constraint);
        detailsEl.appendChild(constraintSpan);

        if (violation.property_name) {
            const propSpan = this.createElement('span', 'Property: ' + violation.property_name);
            detailsEl.appendChild(propSpan);
        }

        if (violation.actual_value !== null && violation.actual_value !== undefined) {
            const actualSpan = this.createElement('span', 'Actual: ' + violation.actual_value);
            detailsEl.appendChild(actualSpan);
        }

        if (violation.expected_value) {
            const expectedSpan = this.createElement('span', 'Expected: ' + violation.expected_value);
            detailsEl.appendChild(expectedSpan);
        }

        card.appendChild(typeEl);
        card.appendChild(messageEl);
        card.appendChild(detailsEl);

        return card;
    },

    /**
     * Create a status box element safely
     * @param {string} type - Status type: 'success', 'warning', 'error'
     * @param {string} message - The status message
     * @returns {HTMLElement} - The status box element
     */
    createStatusBox: function(type, message) {
        const div = document.createElement('div');
        div.className = 'status-box ' + type;
        div.textContent = message;
        return div;
    },

    /**
     * Safely display an error message
     * @param {HTMLElement} container - The container element
     * @param {string} message - The error message
     */
    showError: function(container, message) {
        const box = this.createStatusBox('error', '[ERROR] ' + message);
        container.innerHTML = '';
        container.appendChild(box);
    },

    /**
     * Get CSRF token from cookie
     * @returns {string} - The CSRF token or empty string
     */
    getCsrfToken: function() {
        const match = document.cookie.match(/csrf_token=([^;]+)/);
        return match ? match[1] : '';
    },

    /**
     * Add CSRF token to fetch options
     * @param {Object} options - Fetch options object
     * @returns {Object} - Modified options with CSRF header
     */
    addCsrfHeader: function(options) {
        options = options || {};
        options.headers = options.headers || {};
        options.headers['X-CSRF-Token'] = this.getCsrfToken();
        return options;
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.Security = Security;
}
