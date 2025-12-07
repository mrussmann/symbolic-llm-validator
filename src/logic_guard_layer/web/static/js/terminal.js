/**
 * Logic-Guard-Layer Terminal JavaScript
 * Handles clock updates, font size controls, mobile menu, and other terminal effects
 */

// ============================================================================
// Font Size Control
// ============================================================================

const FontSizeControl = {
    sizes: [14, 16, 18, 20, 22, 24],
    currentIndex: 2, // Default to 18px
    storageKey: 'lgl-font-size',

    init() {
        // Load saved preference
        const saved = localStorage.getItem(this.storageKey);
        if (saved) {
            const savedIndex = this.sizes.indexOf(parseInt(saved));
            if (savedIndex !== -1) {
                this.currentIndex = savedIndex;
            }
        }

        // Apply initial size
        this.apply();

        // Setup event listeners
        const decreaseBtn = document.getElementById('font-decrease');
        const increaseBtn = document.getElementById('font-increase');

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => this.decrease());
        }
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => this.increase());
        }

        // Update label
        this.updateLabel();
    },

    apply() {
        const size = this.sizes[this.currentIndex];
        document.documentElement.style.setProperty('--font-size-base', `${size}px`);
        document.documentElement.style.setProperty('--font-size-lg', `${size + 4}px`);
        document.documentElement.style.setProperty('--font-size-sm', `${size - 2}px`);

        // Dispatch custom event for other components (like visualization)
        window.dispatchEvent(new CustomEvent('fontsizechange', { detail: { size } }));
    },

    increase() {
        if (this.currentIndex < this.sizes.length - 1) {
            this.currentIndex++;
            this.apply();
            this.save();
            this.updateLabel();
            addFlickerEffect();
        }
    },

    decrease() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.apply();
            this.save();
            this.updateLabel();
            addFlickerEffect();
        }
    },

    save() {
        localStorage.setItem(this.storageKey, this.sizes[this.currentIndex]);
    },

    updateLabel() {
        const label = document.getElementById('font-size-label');
        if (label) {
            // Show relative size indicator
            const indicators = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            label.textContent = indicators[this.currentIndex] || 'M';
        }
    },

    getSize() {
        return this.sizes[this.currentIndex];
    }
};

// ============================================================================
// Mobile Menu
// ============================================================================

const MobileMenu = {
    init() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const navLinks = document.querySelector('.nav-links');

        if (toggle && navLinks) {
            toggle.addEventListener('click', () => {
                navLinks.classList.toggle('mobile-open');
                toggle.classList.toggle('active');
            });

            // Close menu when clicking a link
            navLinks.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', () => {
                    navLinks.classList.remove('mobile-open');
                    toggle.classList.remove('active');
                });
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !navLinks.contains(e.target)) {
                    navLinks.classList.remove('mobile-open');
                    toggle.classList.remove('active');
                }
            });
        }
    }
};

// ============================================================================
// Clock
// ============================================================================

function updateClock() {
    const clockEl = document.getElementById('clock');
    if (clockEl) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        const dateStr = now.toLocaleDateString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
        clockEl.textContent = `${dateStr} ${timeStr}`;
    }
}

// Initialize clock
updateClock();
setInterval(updateClock, 1000);

// Add typing effect to elements with .typing-effect class
function typeWriter(element, text, speed = 30) {
    let i = 0;
    element.textContent = '';

    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }

    type();
}

// Initialize all modules on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize font size control
    FontSizeControl.init();

    // Initialize mobile menu
    MobileMenu.init();

    // Initialize typing effects
    const typingElements = document.querySelectorAll('.typing-effect');
    typingElements.forEach(el => {
        const text = el.textContent;
        typeWriter(el, text);
    });
});

// Add CRT flicker on certain actions
function addFlickerEffect() {
    const screen = document.querySelector('.crt-screen');
    if (screen) {
        screen.style.animation = 'none';
        screen.offsetHeight; // Trigger reflow
        screen.style.animation = 'flicker 0.1s';
        setTimeout(() => {
            screen.style.animation = 'flicker 0.15s infinite';
        }, 100);
    }
}

// Add flicker effect on form submissions
document.addEventListener('submit', function(e) {
    addFlickerEffect();
});

// Add flicker effect on button clicks
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('terminal-button')) {
        addFlickerEffect();
    }
});

// Console easter egg
console.log('%c LOGIC-GUARD-LAYER ',
    'background: #0a0a0a; color: #00ff41; font-family: monospace; font-size: 20px; padding: 10px; text-shadow: 0 0 10px #00ff41;');
console.log('%c Neuro-Symbolic Validation System ',
    'background: #0a0a0a; color: #00cc33; font-family: monospace; font-size: 14px; padding: 5px;');
console.log('%c > Ready for validation...',
    'color: #00ff41; font-family: monospace;');
