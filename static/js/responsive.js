// Modern Responsive JavaScript for HR System
document.addEventListener('DOMContentLoaded', function() {
    initResponsiveFeatures();
    createMobileMenuToggle();
    makeTablesResponsive();
    initTouchEnhancements();
    initLoadingStates();
    initSmoothAnimations();
    
    // Handle window resize
    window.addEventListener('resize', debounce(handleResize, 250));
});

// Initialize all responsive features
function initResponsiveFeatures() {
    // Add responsive classes based on screen size
    updateResponsiveClasses();
    
    // Initialize mobile-specific features
    if (window.innerWidth <= 768) {
        initMobileFeatures();
    }
    
    // Initialize tablet-specific features
    if (window.innerWidth > 768 && window.innerWidth <= 1024) {
        initTabletFeatures();
    }
}

// Create mobile menu toggle
function createMobileMenuToggle() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // Create mobile menu button
    const mobileMenuButton = document.createElement('button');
    mobileMenuButton.innerHTML = '<i class="fas fa-bars"></i>';
    mobileMenuButton.className = 'mobile-menu-toggle';
    mobileMenuButton.setAttribute('aria-label', 'Toggle Menu');
    
    // Style the button
    Object.assign(mobileMenuButton.style, {
        position: 'fixed',
        top: '20px',
        left: '20px',
        zIndex: '1001',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: 'none',
        borderRadius: '12px',
        width: '50px',
        height: '50px',
        display: 'none',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        fontSize: '18px'
    });

    document.body.appendChild(mobileMenuButton);

    // Toggle sidebar functionality
    mobileMenuButton.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMobileMenu();
    });

    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768 &&
            !sidebar.contains(event.target) &&
            !mobileMenuButton.contains(event.target) &&
            sidebar.classList.contains('mobile-open')) {
            closeMobileMenu();
        }
    });

    // Handle escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('mobile-open')) {
            closeMobileMenu();
        }
    });

    // Add mobile styles
    addMobileStyles();
}

// Toggle mobile menu
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay') || createMobileOverlay();
    
    if (sidebar.classList.contains('mobile-open')) {
        closeMobileMenu();
    } else {
        openMobileMenu();
    }
}

// Open mobile menu
function openMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay') || createMobileOverlay();
    
    sidebar.classList.add('mobile-open');
    overlay.classList.add('active');
    document.body.classList.add('menu-open');
    
    // Animate menu items
    const menuItems = sidebar.querySelectorAll('.nav-item');
    menuItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('slide-in');
    });
}

// Close mobile menu
function closeMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    
    sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    document.body.classList.remove('menu-open');
    
    // Remove animation classes
    const menuItems = sidebar.querySelectorAll('.nav-item');
    menuItems.forEach(item => {
        item.classList.remove('slide-in');
    });
}

// Create mobile overlay
function createMobileOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    
    Object.assign(overlay.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%',
        background: 'rgba(0, 0, 0, 0.5)',
        zIndex: '999',
        opacity: '0',
        visibility: 'hidden',
        transition: 'all 0.3s ease',
        backdropFilter: 'blur(5px)'
    });
    
    overlay.addEventListener('click', closeMobileMenu);
    document.body.appendChild(overlay);
    
    return overlay;
}

// Add mobile-specific styles
function addMobileStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 1000;
            }
            
            .sidebar.mobile-open {
                transform: translateX(0);
            }
            
            .mobile-menu-toggle {
                display: flex !important;
            }
            
            .mobile-overlay.active {
                opacity: 1 !important;
                visibility: visible !important;
            }
            
            body.menu-open {
                overflow: hidden;
            }
            
            .main-content {
                margin-left: 0 !important;
                padding: 80px 15px 20px 15px;
            }
            
            .nav-item.slide-in {
                animation: slideInLeft 0.3s ease-out forwards;
            }
            
            @keyframes slideInLeft {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        }
        
        @media (max-width: 480px) {
            .content-area {
                padding: 15px !important;
            }
            
            .card {
                margin-bottom: 15px;
            }
            
            .card-body {
                padding: 15px !important;
            }
            
            .btn {
                padding: 10px 20px;
                font-size: 14px;
            }
        }
    `;
    document.head.appendChild(style);
}

// Make tables responsive
function makeTablesResponsive() {
    const tables = document.querySelectorAll('table:not(.responsive-processed)');
    
    tables.forEach(table => {
        table.classList.add('responsive-processed');
        
        // Wrap table in responsive container
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            wrapper.style.cssText = `
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            `;
            
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
        
        // Add mobile-friendly table features
        if (window.innerWidth <= 768) {
            makeMobileTable(table);
        }
    });
}

// Convert table to mobile-friendly format
function makeMobileTable(table) {
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, index) => {
            if (headers[index]) {
                cell.setAttribute('data-label', headers[index]);
            }
        });
    });
    
    // Add mobile table styles
    if (!document.querySelector('#mobile-table-styles')) {
        const style = document.createElement('style');
        style.id = 'mobile-table-styles';
        style.textContent = `
            @media (max-width: 768px) {
                .table-responsive table,
                .table-responsive thead,
                .table-responsive tbody,
                .table-responsive th,
                .table-responsive td,
                .table-responsive tr {
                    display: block;
                }
                
                .table-responsive thead tr {
                    position: absolute;
                    top: -9999px;
                    left: -9999px;
                }
                
                .table-responsive tr {
                    border: 1px solid rgba(0,0,0,0.1);
                    border-radius: 12px;
                    margin-bottom: 15px;
                    padding: 15px;
                    background: white;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                }
                
                .table-responsive td {
                    border: none;
                    position: relative;
                    padding: 8px 0 8px 50% !important;
                    text-align: right;
                }
                
                .table-responsive td:before {
                    content: attr(data-label) ": ";
                    position: absolute;
                    left: 0;
                    width: 45%;
                    padding-right: 10px;
                    white-space: nowrap;
                    font-weight: 600;
                    color: #2d3436;
                    text-align: left;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Handle window resize
function handleResize() {
    updateResponsiveClasses();
    
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (window.innerWidth > 768) {
        // Desktop view
        if (sidebar) sidebar.classList.remove('mobile-open');
        if (mobileMenuToggle) mobileMenuToggle.style.display = 'none';
        document.body.classList.remove('menu-open');
        
        // Remove mobile overlay
        const overlay = document.querySelector('.mobile-overlay');
        if (overlay) overlay.classList.remove('active');
        
    } else {
        // Mobile view
        if (mobileMenuToggle) mobileMenuToggle.style.display = 'flex';
    }
    
    // Re-process tables for new screen size
    makeTablesResponsive();
}

// Update responsive classes
function updateResponsiveClasses() {
    const body = document.body;
    const width = window.innerWidth;
    
    // Remove existing responsive classes
    body.classList.remove('mobile', 'tablet', 'desktop');
    
    // Add appropriate class
    if (width <= 768) {
        body.classList.add('mobile');
    } else if (width <= 1024) {
        body.classList.add('tablet');
    } else {
        body.classList.add('desktop');
    }
}

// Initialize mobile-specific features
function initMobileFeatures() {
    // Add touch-friendly button sizes
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.style.minHeight = '44px';
        btn.style.minWidth = '44px';
    });
    
    // Improve form inputs for mobile
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.style.fontSize = '16px'; // Prevents zoom on iOS
    });
}

// Initialize tablet-specific features
function initTabletFeatures() {
    // Tablet-specific optimizations
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.marginBottom = '20px';
    });
}

// Initialize touch enhancements
function initTouchEnhancements() {
    if (!isTouchDevice()) return;
    
    document.body.classList.add('touch-device');
    
    // Add touch feedback to interactive elements
    const interactiveElements = document.querySelectorAll('button, .btn, .nav-link, .card');
    
    interactiveElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        
        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-active');
            }, 150);
        });
    });
    
    // Add touch styles
    const style = document.createElement('style');
    style.textContent = `
        .touch-device .touch-active {
            transform: scale(0.98);
            opacity: 0.8;
        }
        
        .touch-device button,
        .touch-device .btn {
            min-height: 44px;
            min-width: 44px;
        }
        
        .touch-device .nav-link {
            min-height: 44px;
            padding: 12px 20px;
        }
    `;
    document.head.appendChild(style);
}

// Initialize loading states
function initLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                addLoadingState(submitBtn);
            }
        });
    });
}

// Add loading state to button
function addLoadingState(button) {
    const originalText = button.innerHTML;
    const loadingHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    button.innerHTML = loadingHTML;
    button.disabled = true;
    
    // Reset after 5 seconds (fallback)
    setTimeout(() => {
        if (button.disabled) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }, 5000);
}

// Initialize smooth animations
function initSmoothAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe cards and other elements
    const animateElements = document.querySelectorAll('.card, .stat-card, .alert');
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Add animation styles
    const style = document.createElement('style');
    style.textContent = `
        .card, .stat-card, .alert {
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}

// Utility functions
function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global use
window.ResponsiveUtils = {
    toggleMobileMenu,
    closeMobileMenu,
    makeTablesResponsive,
    addLoadingState,
    isTouchDevice
};