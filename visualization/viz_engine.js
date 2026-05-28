export default class VisualizationEngine {
    constructor(options = {}) {
        this.state = { phase: 'INIT', cycle: 0, internal_tension: 0.5 };
        this.canvas = document.getElementById('vizCanvas');
        if (!this.canvas) throw new Error('vizCanvas not found');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 300;
        this.cursorX = 0;
        this.cursorY = 0;
        this.esp32Url = options.esp32Url || 'http://192.168.4.38';
        this.sensorData = { temperature: 22, humidity: 60, touchActive: false };
        this.sensorCallbacks = [];
        this.burstActive = false;
        this.burstTimer = 0;
        this.phaseColors = {
            'PERCEIVE': { h: 180, s: 80, l: 60 },
            'REFLECT': { h: 220, s: 70, l: 55 },
            'DECIDE': { h: 260, s: 75, l: 60 },
            'ACT': { h: 30, s: 85, l: 55 },
            'CONSOLIDATE': { h: 140, s: 70, l: 50 },
            'PERSIST': { h: 45, s: 80, l: 55 },
        };
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.canvas.parentElement.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.cursorX = e.clientX - rect.left;
            this.cursorY = e.clientY - rect.top;
        });
        this.initParticles();
        this.animate();
        if (options.enableSensors) {
            this.startSensorPolling(options.sensorPollInterval || 5000);
        }
    }

    onSensorUpdate(callback) {
        this.sensorCallbacks.push(callback);
    }

    async pollSensor(endpoint, fallback) {
        try {
            const resp = await fetch(this.esp32Url + endpoint);
            if (!resp.ok) return fallback;
            return await resp.json();
        } catch {
            return fallback;
        }
    }

    async updateSensors() {
        const [tempData, humidityData, touchData] = await Promise.allSettled([
            this.pollSensor('/api/sensor/temp', { value: this.sensorData.temperature }),
            this.pollSensor('/api/sensor/humidity', { value: this.sensorData.humidity }),
            this.pollSensor('/api/sensor/touch', { active: false }),
        ]);

        const prevTouch = this.sensorData.touchActive;
        this.sensorData.temperature = tempData.value?.value ?? this.sensorData.temperature;
        this.sensorData.humidity = humidityData.value?.value ?? this.sensorData.humidity;
        this.sensorData.touchActive = touchData.value?.active ?? false;

        // Trigger burst on touch rise
        if (this.sensorData.touchActive && !prevTouch) {
            this.burstActive = true;
            this.burstTimer = 60;
            this.particles.forEach(p => {
                p.vx += (Math.random() - 0.5) * 8;
                p.vy += (Math.random() - 0.5) * 8;
            });
        }
        if (this.burstTimer > 0) this.burstTimer--;
        if (this.burstTimer === 0) this.burstActive = false;

        this.sensorCallbacks.forEach(cb => cb(this.sensorData));
    }

    startSensorPolling(intervalMs) {
        this.updateSensors();
        setInterval(() => this.updateSensors(), intervalMs);
    }

    resize() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
    }

    initParticles() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push(this.createParticle());
        }
    }

    createParticle() {
        const angle = Math.random() * Math.PI * 2;
        const radius = 50 + Math.random() * 200;
        return {
            x: this.centerX + Math.cos(angle) * radius,
            y: this.centerY + Math.sin(angle) * radius,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            baseRadius: 1 + Math.random() * 2,
            radius: 1 + Math.random() * 2,
            alpha: 0.3 + Math.random() * 0.7,
            life: Math.random(),
            orbitAngle: angle,
            orbitRadius: radius,
            orbitSpeed: (0.001 + Math.random() * 0.003) * (Math.random() > 0.5 ? 1 : -1),
        };
    }

    update(state) {
        if (state) this.state = { ...this.state, ...state };
        const phase = this.state.phase;
        const tension = this.state.internal_tension || 0.5;

        // Temperature maps to velocity scale (18-26°C typical, scale linearly)
        const tempScale = Math.max(0.5, Math.min(2.0, (this.sensorData.temperature - 18) / 8));

        // Humidity maps to particle density (40-100% typical)
        const humidityFactor = (this.sensorData.humidity - 40) / 60;
        const targetCount = 200 + Math.floor(tension * 200) + Math.floor(humidityFactor * 100);
        while (this.particles.length < targetCount) {
            this.particles.push(this.createParticle());
        }
        while (this.particles.length > targetCount) {
            this.particles.pop();
        }

        this.particles.forEach((p, i) => {
            const formation = this.getFormationTarget(p, i, phase, tension);

            // Spiral formation behavior — temperature modulates speed
            p.orbitAngle += p.orbitSpeed * (1 + tension * 2) * tempScale;
            const targetX = formation.x;
            const targetY = formation.y;

            // Lerp toward formation target — humidity makes particles "heavier" (slower to respond)
            const lerpFactor = 0.02 * (1 - humidityFactor * 0.5);
            p.x += (targetX - p.x) * lerpFactor;
            p.y += (targetY - p.y) * lerpFactor;

            // Cursor interaction - particles repel from cursor
            const dx = p.x - this.cursorX;
            const dy = p.y - this.cursorY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 80) {
                const force = (80 - dist) / 80;
                p.vx += (dx / dist) * force * 2;
                p.vy += (dy / dist) * force * 2;
            }

            // Damping — temperature affects energy retention
            const damping = 0.92 + (1 - tempScale) * 0.06;
            p.vx *= damping;
            p.vy *= damping;
            p.x += p.vx * tempScale;
            p.y += p.vy * tempScale;

            // Oscillation frequency based on tension
            p.life += 0.01 * (1 + tension * 3);
            p.radius = p.baseRadius * (1 + Math.sin(p.life * Math.PI * 2) * 0.3);
        });
    }

    getFormationTarget(p, index, phase, tension) {
        const baseAngle = p.orbitAngle;
        const baseRadius = p.orbitRadius;
        let formationRadius = baseRadius;
        let formationAngle = baseAngle;

        switch (phase) {
            case 'PERCEIVE':
                // Expanding ring - sensing outward
                formationRadius = baseRadius + Math.sin(p.life * Math.PI) * 30;
                break;
            case 'REFLECT':
                // Inward spiral - focusing inward
                formationRadius = baseRadius * 0.7 + Math.cos(p.life * Math.PI) * 20;
                break;
            case 'DECIDE':
                // Converging points - decision crystallization
                formationRadius = baseRadius * 0.5 + Math.sin(p.life * Math.PI * 2) * 15;
                formationAngle += tension * 0.1;
                break;
            case 'ACT':
                // Outward burst - energy release
                formationRadius = baseRadius + Math.sin(p.life * Math.PI) * 50 * tension;
                break;
            case 'CONSOLIDATE':
                // Gentle convergence - knowledge integration
                formationRadius = baseRadius * 0.85 + Math.cos(p.life * Math.PI * 2) * 10;
                break;
            case 'PERSIST':
                // Stable orbit - state preservation
                formationRadius = baseRadius;
                break;
            default:
                formationRadius = baseRadius + Math.sin(p.life * Math.PI) * 20;
        }

        return {
            x: this.centerX + Math.cos(formationAngle) * formationRadius,
            y: this.centerY + Math.sin(formationAngle) * formationRadius,
        };
    }

    getColor(p, index) {
        const phase = this.state.phase;
        const colorDef = this.phaseColors[phase] || { h: 180, s: 80, l: 60 };
        const tension = this.state.internal_tension || 0.5;

        // Color temperature shifts with confidence (inverse of tension)
        const hueShift = (1 - tension) * 30;
        const hue = colorDef.h + hueShift + Math.sin(p.life * Math.PI) * 10;
        const saturation = colorDef.s;
        const lightness = colorDef.l + tension * 15;

        return `hsla(${hue}, ${saturation}%, ${lightness}%, ${p.alpha * (0.5 + tension * 0.5)})`;
    }

    drawConnections() {
        const maxDist = 60;
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < maxDist) {
                    const alpha = (1 - dist / maxDist) * 0.15;
                    this.ctx.strokeStyle = `rgba(0, 255, 204, ${alpha})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }
    }

    animate() {
        this.update();
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw connections
        this.drawConnections();

        // Draw particles
        this.particles.forEach((p, i) => {
            this.ctx.fillStyle = this.getColor(p, i);
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
        });

        // Draw center glow
        const tension = this.state.internal_tension || 0.5;
        const gradient = this.ctx.createRadialGradient(
            this.centerX, this.centerY, 0,
            this.centerX, this.centerY, 100 + tension * 50
        );
        const colorDef = this.phaseColors[this.state.phase] || { h: 180, s: 80, l: 60 };
        gradient.addColorStop(0, `hsla(${colorDef.h}, ${colorDef.s}%, ${colorDef.l}%, ${0.1 + tension * 0.1})`);
        gradient.addColorStop(1, 'transparent');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        requestAnimationFrame(() => this.animate());
    }
}
