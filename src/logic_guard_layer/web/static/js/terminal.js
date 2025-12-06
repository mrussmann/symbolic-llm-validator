/**
 * Logic-Guard-Layer Terminal JavaScript
 * Handles clock updates and other terminal effects
 */

// Update clock in footer
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

// Initialize typing effects on page load
document.addEventListener('DOMContentLoaded', function() {
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
