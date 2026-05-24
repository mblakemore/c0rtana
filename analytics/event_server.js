#!/usr/bin/env node
/**
 * Analytics Event Receiver Server
 * Listens for POST requests at /events and appends to interactions.jsonl
 */

const http = require('http');
const fs = require('fs').promises;
const path = require('path');

const PORT = 8767;
const EVENTS_FILE = path.join(__dirname, 'interactions.jsonl');
const VIZ_DIR = path.join(__dirname, '..', 'visualization');

// Ensure events file exists with header line if not present
async function initEventsFile() {
    try {
        await fs.access(EVENTS_FILE);
    } catch {
        // File doesn't exist - create empty
        await fs.writeFile(EVENTS_FILE, '');
    }
}

const server = http.createServer(async (req, res) => {
    if (req.method === 'POST' && req.url === '/events') {
        let body = '';
        
        req.on('data', chunk => {
            body += chunk.toString();
        });
        
        req.on('end', async () => {
            try {
                const event = JSON.parse(body);
                
                // Append to JSONL file
                const timestamp = new Date().toISOString();
                const record = JSON.stringify({ ...event, received_at: timestamp }) + '\n';
                await fs.appendFile(EVENTS_FILE, record);
                
                console.log(`[Analytics] Event recorded: ${event.type} at ${timestamp}`);
                
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'ok', recorded: true }));
            } catch (err) {
                console.error('[Analytics] Parse error:', err.message);
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'error', message: err.message }));
            }
        });
    } else if (req.method === 'GET' && req.url.startsWith('/visualization/')) {
        // Serve static files from visualization directory
        const filePath = path.join(VIZ_DIR, req.url.replace('/visualization/', ''));
        try {
            const content = await fs.readFile(filePath);
            const ext = path.extname(filePath).toLowerCase();
            const typeMap = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css' };
            res.writeHead(200, { 'Content-Type': typeMap[ext] || 'application/octet-stream' });
            res.end(content);
        } catch (err) {
            res.writeHead(404);
            res.end('File not found');
        }
    } else {
        res.writeHead(404);
        res.end('Not found - use /events for POST or /visualization/<file> for GET');
    }
});

server.listen(PORT, () => {
    console.log(`[Analytics Server] Listening on port ${PORT}`);
    console.log(`[Analytics Server] Events will be written to: ${EVENTS_FILE}`);
    initEventsFile();
});
