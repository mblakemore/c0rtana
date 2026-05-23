// Analytics Client — tracks mouse interactions and emits events via WebSocket
// Injected into cortana.html to log operator engagement with interactive particle UI

const ANALYTICS_WS = 'ws://localhost:8767';
let analyticsWs = null;
let interactionSessionId = `sess_${Date.now()}`;

function initAnalytics() {
    // Connect to analytics tracker
    try {
        analyticsWs = new WebSocket(ANALYTICS_WS);
        
        analyticsWs.onopen = () => {
            console.log('[Analytics] Connected to tracker');
        };
        
        analyticsWs.onmessage = (event) => {
            const response = JSON.parse(event.data);
            if (response.status === 'logged') {
                // Silent acknowledgment - no visual feedback needed
            }
        };
        
        analyticsWs.onerror = (err) => {
            console.warn('[Analytics] Connection error:', err.message);
        };
        
        analyticsWs.onclose = () => {
            console.warn('[Analytics] Disconnected, retrying in 5s...');
            setTimeout(initAnalytics, 5000);
        };
    } catch(e) {
        console.error('[Analytics] Failed to initialize:', e);
    }
}

// Track mouse movement interactions
let lastMouseX = null, lastMouseY = null;
let moveCount = 0;

document.addEventListener('mousemove', (e) => {
    if (!analyticsWs || analyticsWs.readyState !== WebSocket.OPEN) return;
    
    moveCount++;
    
    // Throttle: only log every 10th move to avoid flooding
    if (moveCount % 10 !== 0) return;
    
    const event = {
        type: 'mouse_move',
        timestamp: new Date().toISOString(),
        session_id: interactionSessionId,
        coordinates: { x: e.clientX, y: e.clientY },
        cumulative_moves: moveCount
    };
    
    try {
        analyticsWs.send(JSON.stringify(event));
    } catch(e) {
        console.error('[Analytics] Send error:', e);
    }
});

// Track cursor ring visibility changes (engagement indicator)
const cursorRing = document.getElementById('cursor-ring');
if (cursorRing) {
    cursorRing.addEventListener('mouseenter', () => {
        const event = {
            type: 'cursor_enter',
            timestamp: new.Date().toISOString(),
            session_id: interactionSessionId
        };
        try {
            analyticsWs && analyticsWs.readyState === WebSocket.OPEN && 
                analyticsWs.send(JSON.stringify(event));
        } catch(e) {}
    });
}

// Initialize on load
window.addEventListener('load', initAnalytics);
