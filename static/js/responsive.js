// Responsive functionality
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    createMobileMenuToggle();

    // Handle responsive tables
    makeTablesResponsive();

    // Handle window resize
    window.addEventListener('resize', handleResize);

    // Initialize responsive features
    initResponsiveFeatures();
});

function createMobileMenuToggle() {
    // Create mobile menu button
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const mobileMenuButton = document.createElement('button');
    mobileMenuButton.innerHTML = '<span class="material-icons">menu</span>';
    mobileMenuButton.className = 'mobile-menu-toggle';
    mobileMenuButton.style.cssText = `
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 1001;
        background: #1e40af;
        color: white;
        border: none;
        border-radius: 6px;
        width: 40px;
        height: 40px;
        display: none;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;

    document.body.appendChild(mobileMenuButton);

    // Toggle sidebar on mobile
    mobileMenuButton.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-open');
        document.body.classList.toggle('menu-open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768 &&
            !sidebar.contains(event.target) &&
            !mobileMenuButton.contains(event.target) &&
            sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
            document.body.classList.remove('menu-open');
        }
    });

    // Add CSS for mobile menu
    const style = document.createElement('style');
    style.textContent = `
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            .sidebar.mobile-open {
                transform: translateX(0);
            }
            .mobile-menu-toggle {
                display: flex !important;
            }
            body.menu-open {
                overflow: hidden;
            }
        }
    `;
    document.head.appendChild(style);
}

function makeTablesResponsive() {
    const tables = document.querySelectorAll('table');

    tables.forEach(table => {
        if (table.offsetWidth > document.documentElement.clientWidth) {
            table.parentElement.style.overflowX = 'auto';
            table.parentElement.style.webkitOverflowScrolling = 'touch';
        }
    });
}

function handleResize() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (window.innerWidth > 768) {
        if (sidebar) sidebar.classList.remove('mobile-open');
        if (mobileMenuToggle) mobileMenuToggle.style.display = 'none';
    } else {
        if (mobileMenuToggle) mobileMenuToggle.style.display = 'flex';
    }

    makeTablesResponsive();
}

function initResponsiveFeatures() {
    // Add loading states for better mobile experience
    const buttons = document.querySelectorAll('button, .action-button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                // Add loading feedback for mobile
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="material-icons" style="animation: spin 1s linear infinite;">refresh</span> Loading...';
                this.disabled = true;

                // Restore after 2 seconds if still disabled (fallback)
                setTimeout(() => {
                    if (this.disabled) {
                        this.innerHTML = originalText;
                        this.disabled = false;
                    }
                }, 2000);
            }
        });
    });

    // Add CSS for loading animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Touch device detection and enhancements
function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

if (isTouchDevice()) {
    document.body.classList.add('touch-device');

    // Add touch-specific improvements
    const style = document.createElement('style');
    style.textContent = `
        .touch-device .action-button {
            min-height: 44px;
            min-width: 44px;
            padding: 12px 16px;
        }
        .touch-device .sidebar a {
            min-height: 44px;
            padding: 12px 25px;
        }
        .touch-device .employee-name-cell {
            min-height: 44px;
        }
    `;
    document.head.appendChild(style);
}