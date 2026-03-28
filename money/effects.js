// ============================================================
// ALZ — Premium Visual Effects (v2 — Rebuilt)
// Lightweight: IntersectionObserver reveals, Three.js particles,
// custom cursor, magnetic buttons, tilt cards, counters
// NO Lenis, NO GSAP scroll-triggered opacity animations
// ============================================================

(function () {
    'use strict';

    const isMobile = window.innerWidth < 768;
    const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ─── INTERSECTION OBSERVER REVEALS ────────────────────────
    // Pure CSS transitions — elements appear INSTANTLY when scrolled into view
    function initReveals() {
        const reveals = document.querySelectorAll('.reveal');
        if (!reveals.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target); // only once
                }
            });
        }, {
            threshold: 0.08, // fire as soon as 8% is visible
            rootMargin: '0px 0px -30px 0px'
        });

        reveals.forEach(el => observer.observe(el));
    }

    // ─── THREE.JS PARTICLE HERO ──────────────────────────────
    function initParticleHero() {
        const canvas = document.getElementById('hero-canvas');
        if (!canvas) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, canvas.offsetWidth / canvas.offsetHeight, 0.1, 1000);
        camera.position.z = 5;

        const renderer = new THREE.WebGLRenderer({
            canvas,
            alpha: true,
            antialias: true,
        });
        renderer.setSize(canvas.offsetWidth, canvas.offsetHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const particleCount = isMobile ? 150 : 400;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);

        const colorPalette = [
            new THREE.Color('#6366f1'), // indigo
            new THREE.Color('#a855f7'), // purple
            new THREE.Color('#ec4899'), // pink
            new THREE.Color('#8b5cf6'), // violet
        ];

        for (let i = 0; i < particleCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 18;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 14;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 12;

            const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;

            sizes[i] = Math.random() * 1.5 + 0.4;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.ShaderMaterial({
            vertexShader: `
                attribute float size;
                varying vec3 vColor;
                void main() {
                    vColor = color;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_PointSize = size * (200.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                void main() {
                    float d = length(gl_PointCoord - vec2(0.5));
                    if (d > 0.5) discard;
                    float alpha = 1.0 - smoothstep(0.1, 0.5, d);
                    gl_FragColor = vec4(vColor, alpha * 0.35);
                }
            `,
            transparent: true,
            vertexColors: true,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
        });

        const particles = new THREE.Points(geometry, material);
        scene.add(particles);

        const mouse = { x: 0, y: 0 };
        const targetMouse = { x: 0, y: 0 };

        document.addEventListener('mousemove', (e) => {
            targetMouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            targetMouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        });

        const clock = new THREE.Clock();

        function animate() {
            const elapsed = clock.getElapsedTime();

            mouse.x += (targetMouse.x - mouse.x) * 0.05;
            mouse.y += (targetMouse.y - mouse.y) * 0.05;

            particles.rotation.y = elapsed * 0.04 + mouse.x * 0.3;
            particles.rotation.x = elapsed * 0.02 + mouse.y * 0.2;

            const posArr = geometry.attributes.position.array;
            for (let i = 0; i < particleCount; i++) {
                posArr[i * 3 + 1] += Math.sin(elapsed + i * 0.1) * 0.0008;
            }
            geometry.attributes.position.needsUpdate = true;

            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        animate();

        window.addEventListener('resize', () => {
            const w = canvas.offsetWidth;
            const h = canvas.offsetHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });
    }

    // ─── CUSTOM CURSOR ───────────────────────────────────────
    function initCustomCursor() {
        if (isMobile || isReducedMotion) return;

        const cursor = document.getElementById('custom-cursor');
        const cursorDot = document.getElementById('cursor-dot');
        if (!cursor || !cursorDot) return;

        let cursorX = 0, cursorY = 0;
        let dotX = 0, dotY = 0;
        let ringX = 0, ringY = 0;

        document.addEventListener('mousemove', (e) => {
            cursorX = e.clientX;
            cursorY = e.clientY;
        });

        function updateCursor() {
            dotX += (cursorX - dotX) * 0.5;
            dotY += (cursorY - dotY) * 0.5;
            cursorDot.style.transform = `translate(${dotX - 4}px, ${dotY - 4}px)`;

            ringX += (cursorX - ringX) * 0.15;
            ringY += (cursorY - ringY) * 0.15;
            cursor.style.transform = `translate(${ringX - 20}px, ${ringY - 20}px)`;

            requestAnimationFrame(updateCursor);
        }
        updateCursor();

        const interactiveEls = document.querySelectorAll('a, button, .pricing-card, .service-card, .problem-card, .stat-card');
        interactiveEls.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.classList.add('cursor-hover');
                cursorDot.classList.add('cursor-hover');
            });
            el.addEventListener('mouseleave', () => {
                cursor.classList.remove('cursor-hover');
                cursorDot.classList.remove('cursor-hover');
            });
        });

        document.addEventListener('mouseleave', () => {
            cursor.style.opacity = '0';
            cursorDot.style.opacity = '0';
        });
        document.addEventListener('mouseenter', () => {
            cursor.style.opacity = '1';
            cursorDot.style.opacity = '1';
        });
    }

    // ─── MAGNETIC BUTTONS ────────────────────────────────────
    function initMagneticButtons() {
        if (isMobile) return;

        document.querySelectorAll('.btn-primary, .btn-secondary, .pricing-cta').forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = '';
            });
        });
    }

    // ─── TILT CARDS ──────────────────────────────────────────
    function initTiltCards() {
        if (isMobile) return;

        document.querySelectorAll('.service-card, .pricing-card, .problem-card').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;

                const tiltX = (y - 0.5) * 8;
                const tiltY = (x - 0.5) * -8;

                card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.02)`;
                card.style.setProperty('--mouse-x', `${x * 100}%`);
                card.style.setProperty('--mouse-y', `${y * 100}%`);
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    }

    // ─── ANIMATED GRADIENT TEXT ──────────────────────────────
    function initGradientShift() {
        document.querySelectorAll('.gradient-text').forEach(el => {
            el.style.backgroundSize = '300% 100%';
            el.style.animation = 'gradientShift 4s ease-in-out infinite';
        });
    }

    // ─── COUNTER ANIMATION ──────────────────────────────────
    function initCounters() {
        const statNumbers = document.querySelectorAll('.stat-number');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const stat = entry.target;
                const text = stat.textContent.trim();
                const match = text.match(/^([+<>]?\s*)(\d+)(%?)$/);
                if (!match) return;

                const prefix = match[1];
                const target = parseInt(match[2]);
                const suffix = match[3];
                let current = 0;
                const duration = 1500;
                const start = performance.now();

                function step(now) {
                    const progress = Math.min((now - start) / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
                    current = Math.floor(eased * target);
                    stat.textContent = `${prefix}${current}${suffix}`;
                    if (progress < 1) requestAnimationFrame(step);
                }

                requestAnimationFrame(step);
                observer.unobserve(stat);
            });
        }, { threshold: 0.5 });

        statNumbers.forEach(stat => observer.observe(stat));
    }

    // ─── HERO ENTRANCE ANIMATION (CSS classes, no GSAP) ─────
    function initHeroEntrance() {
        // Stagger hero elements with CSS classes
        const elements = [
            { selector: '.hero .badge', delay: 100 },
            { selector: '.hero h1', delay: 200 },
            { selector: '.hero p', delay: 400 },
            { selector: '.hero-buttons', delay: 600 },
            { selector: '.hero-mockup', delay: 800 },
        ];

        elements.forEach(({ selector, delay }) => {
            const el = document.querySelector(selector);
            if (el) {
                el.classList.add('hero-animate');
                setTimeout(() => el.classList.add('hero-animate-in'), delay);
            }
        });

        // Stagger stat cards
        document.querySelectorAll('.stat-card').forEach((card, i) => {
            card.classList.add('hero-animate');
            setTimeout(() => card.classList.add('hero-animate-in'), 900 + i * 150);
        });
    }

    // ─── INIT EVERYTHING ─────────────────────────────────────
    function init() {
        initReveals();
        initHeroEntrance();
        initParticleHero();
        initCustomCursor();
        initMagneticButtons();
        initTiltCards();
        initGradientShift();
        initCounters();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
