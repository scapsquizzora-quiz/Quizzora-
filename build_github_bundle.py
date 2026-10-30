import json
import base64
import os
import re

def to_b64(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()

def build():
    print("Building standalone GitHub Pages index.html...")
    
    # 1. Base64 Encode All Images
    img_logo = to_b64("static/images/quizzora_logo_premium.png", "image/png")
    img_banner = to_b64("static/images/quizzora_logo_banner.png", "image/png")
    img_badge = to_b64("static/images/quizzora_badge_premium.png", "image/png")
    img_qr = to_b64("static/images/quizzora_registration_qr.png", "image/png")
    img_square = to_b64("static/images/quizzora_logo_square.jpg", "image/jpeg")

    # 2. Read Styles, Audio, Confetti
    with open("static/css/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    with open("static/js/audio.js", "r", encoding="utf-8") as f:
        audio_js = f.read()

    with open("static/js/confetti.js", "r", encoding="utf-8") as f:
        confetti_js = f.read()

    with open("scratch/all_questions.json", "r", encoding="utf-8") as f:
        questions_json = f.read()

    with open("scratch/settings.json", "r", encoding="utf-8") as f:
        settings_data = json.load(f)

    # 3. Read HTML template
    with open("static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Replace relative image URLs in HTML with base64 data URIs
    html = html.replace("/static/images/quizzora_logo_premium.png", img_logo)
    html = html.replace("/static/images/quizzora_logo_banner.png", img_banner)
    html = html.replace("/static/images/quizzora_badge_premium.png", img_badge)
    html = html.replace("/static/images/quizzora_registration_qr.png", img_qr)
    html = html.replace("/static/images/quizzora_logo_square.jpg", img_square)

    # Remove external stylesheet link and insert inline <style>
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', f"<style>\n{css}\n</style>")

    # Remove external script tags at the bottom
    script_pattern = re.compile(r'<script src="/static/js/audio\.js"></script>\s*<script src="/static/js/confetti\.js"></script>\s*<script src="/static/js/app\.js"></script>')

    # 4. Standalone JavaScript Logic with Built-in Database & Offline Resilience
    standalone_js = f"""
// ================= QUIZZORA GITHUB / STANDALONE ENGINE =================
const QUIZZORA_ASSETS = {{
    logo: "{img_logo}",
    banner: "{img_banner}",
    badge: "{img_badge}",
    qr: "{img_qr}",
    square: "{img_square}"
}};

const QUIZZORA_DEFAULT_SETTINGS = {json.dumps(settings_data, ensure_ascii=False, indent=2)};

const QUIZZORA_DEFAULT_CHAMPIONS = {{
    "junior": {{
        "player_nickname": "Open - No Champion Yet",
        "school_name": "Be the First to Set Record",
        "score": 0,
        "accuracy": 0,
        "date_achieved": "2026-10-30",
        "title": "Awaiting Champion"
    }},
    "commerce": {{
        "player_nickname": "Open - No Champion Yet",
        "school_name": "Be the First to Set Record",
        "score": 0,
        "accuracy": 0,
        "date_achieved": "2026-10-30",
        "title": "Awaiting Champion"
    }}
}};

const QUIZZORA_BUILTIN_QUESTIONS = {questions_json};

{audio_js}

{confetti_js}

// Initialize audio and confetti
window.quizzoraAudio = new QuizzoraAudio();
window.quizzoraConfetti = new QuizzoraConfetti();

const App = {{
    config: {{}},
    champions: {{}},
    questionsBank: [],
    isStandalone: true,
    player: {{
        nickname: localStorage.getItem('quizzora_nickname') || '',
        school: localStorage.getItem('quizzora_school') || '',
        category: 'junior',
        mode: 'standard',
        challengeId: null
    }},
    session: {{
        id: null,
        questions: [],
        currentIndex: 0,
        score: 0,
        streak: 0,
        correctCount: 0,
        timer: null,
        timeRemaining: 20,
        totalTimeTaken: 0,
        answered: false,
        startTime: null
    }},
    adminToken: null,

    async 
    toggleMobileMenu() {{
        const drawer = document.getElementById('mobile-nav-drawer');
        const backdrop = document.getElementById('mobile-nav-backdrop');
        if (drawer && backdrop) {{
            const isOpen = drawer.classList.contains('active');
            if (isOpen) {{
                this.closeMobileMenu();
            }} else {{
                drawer.classList.add('active');
                backdrop.classList.add('active');
                document.body.style.overflow = 'hidden';
            }}
        }}
    }},

    closeMobileMenu() {{
        const drawer = document.getElementById('mobile-nav-drawer');
        const backdrop = document.getElementById('mobile-nav-backdrop');
        if (drawer) drawer.classList.remove('active');
        if (backdrop) backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }},

    init() {{
        this.bindEvents();
        this.initCountdown();
        this.initQuestionBank();
        this.updateSoundIcon();
        this.loadPersonalBest();
        await this.loadConfig();
        await this.loadChampions();
        this.checkUrlParams();

        if (window.location.hash) {{
            const h = window.location.hash.substring(1);
            if (document.getElementById(h)) {{
                this.showView(h);
            }}
        }}
        window.addEventListener('hashchange', () => {{
            if (window.location.hash) {{
                const h = window.location.hash.substring(1);
                if (document.getElementById(h)) {{
                    this.showView(h);
                }}
            }}
        }});
    }},

    initQuestionBank() {{
        const stored = localStorage.getItem('quizzora_custom_questions');
        if (stored) {{
            try {{
                const custom = JSON.parse(stored);
                this.questionsBank = [...QUIZZORA_BUILTIN_QUESTIONS, ...custom];
                return;
            }} catch (e) {{}}
        }}
        this.questionsBank = [...QUIZZORA_BUILTIN_QUESTIONS];
    }},

    bindEvents() {{
        // Navigation links
        document.querySelectorAll('[data-view]').forEach(el => {{
            el.addEventListener('click', (e) => {{
                e.preventDefault();
                const targetView = el.getAttribute('data-view');
                this.showView(targetView);
            }});
        }});

        // Sound toggle
        const soundBtn = document.getElementById('sound-toggle-btn');
        if (soundBtn) {{
            soundBtn.addEventListener('click', () => {{
                const isMuted = window.quizzoraAudio.toggleMute();
                this.updateSoundIcon();
                this.showToast(isMuted ? 'Audio muted' : 'Audio enabled');
            }});
        }}

        // Category Cards Click
        document.getElementById('card-junior-quiz')?.addEventListener('click', () => {{
            this.handleCategoryPick('junior');
        }});
        document.getElementById('card-commerce-quiz')?.addEventListener('click', () => {{
            this.handleCategoryPick('commerce');
        }});

        // Hero CTA buttons
        document.getElementById('hero-play-btn')?.addEventListener('click', () => {{
            this.showView('view-category');
        }});
        document.getElementById('hero-challenge-btn')?.addEventListener('click', () => {{
            this.showView('view-challenge');
        }});
        document.getElementById('hero-register-btn')?.addEventListener('click', () => {{
            this.scrollToRegistration();
        }});

        // Champion Challenge Buttons
        document.getElementById('challenge-junior-champ-btn')?.addEventListener('click', () => {{
            this.challengeChampion('junior');
        }});
        document.getElementById('challenge-commerce-champ-btn')?.addEventListener('click', () => {{
            this.challengeChampion('commerce');
        }});

        // Start Quiz Form in Modal
        document.getElementById('start-quiz-form')?.addEventListener('submit', (e) => {{
            e.preventDefault();
            this.confirmAndStartQuiz();
        }});

        // Leaderboard Tabs
        document.querySelectorAll('.lb-tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                document.querySelectorAll('.lb-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.loadLeaderboard(tab.getAttribute('data-category'));
            }});
        }});

        // Keyboard navigation for options (1-4 or A-D)
        window.addEventListener('keydown', (e) => {{
            if (!document.getElementById('view-arena').classList.contains('active')) return;
            if (this.session.answered) return;

            const keyMap = {{
                '1': 0, 'a': 0, 'A': 0,
                '2': 1, 'b': 1, 'B': 1,
                '3': 2, 'c': 2, 'C': 2,
                '4': 3, 'd': 3, 'D': 3
            }};
            if (e.key in keyMap) {{
                const optBtns = document.querySelectorAll('.option-btn');
                const idx = keyMap[e.key];
                if (optBtns[idx] && !optBtns[idx].disabled) {{
                    optBtns[idx].click();
                }}
            }}
        }});
    }},

    updateSoundIcon() {{
        const svg = document.getElementById('sound-icon-svg');
        if (svg) {{
            const isMuted = window.quizzoraAudio ? window.quizzoraAudio.isMuted() : false;
            if (isMuted) {{
                svg.innerHTML = `
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <line x1="23" y1="9" x2="17" y2="15"></line>
                    <line x1="17" y1="9" x2="23" y2="15"></line>
                `;
            }} else {{
                svg.innerHTML = `
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                `;
            }}
        }}
    }},

    showView(viewId) {{
        document.querySelectorAll('.view-section').forEach(sec => {{
            sec.classList.remove('active');
        }});
        const target = document.getElementById(viewId);
        if (target) {{
            target.classList.add('active');
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
            if (link.getAttribute('data-view') === viewId) {{
                link.classList.add('active');
            }} else {{
                link.classList.remove('active');
            }}
        }});
        this.closeMobileMenu();

        if (viewId === 'view-leaderboard') {{
            const activeTab = document.querySelector('.lb-tab.active')?.getAttribute('data-category') || 'all';
            this.loadLeaderboard(activeTab);
            this.loadChampions();
        }} else if (viewId === 'view-home') {{
            this.loadChampions();
        }}
    }},

    showToast(msg, duration = 3000) {{
        const toast = document.getElementById('toast-notice');
        if (toast) {{
            toast.textContent = msg;
            toast.style.display = 'flex';
            setTimeout(() => {{
                toast.style.display = 'none';
            }}, duration);
        }}
    }},

    scrollToRegistration() {{
        this.showView('view-home');
        setTimeout(() => {{
            const el = document.getElementById('actual-registration-section');
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}, 80);
    }},

    scrollToBeatChampion() {{
        this.showView('view-leaderboard');
        setTimeout(() => {{
            const el = document.getElementById('beat-champion-section');
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}, 100);
    }},

    async loadConfig() {{
        try {{
            const res = await fetch('/api/config');
            if (res.ok) {{
                this.config = await res.json();
                this.isStandalone = false;
                this.applyConfig();
                return;
            }}
        }} catch (err) {{}}

        // Standalone Mode Fallback
        const saved = localStorage.getItem('quizzora_settings');
        this.config = saved ? JSON.parse(saved) : {{ ...QUIZZORA_DEFAULT_SETTINGS }};
        this.applyConfig();
    }},

    applyConfig() {{
        const banner = document.getElementById('top-announcement-text');
        if (banner && this.config.announcement_banner) {{
            banner.textContent = this.config.announcement_banner;
        }}
        const instaLinks = document.querySelectorAll('.official-insta-link');
        instaLinks.forEach(a => {{
            if (this.config.instagram_url) a.href = this.config.instagram_url;
        }});
        const formLinks = document.querySelectorAll('.official-form-link');
        formLinks.forEach(a => {{
            if (this.config.google_form_url) a.href = this.config.google_form_url;
        }});
    }},

    async loadChampions() {{
        try {{
            const res = await fetch('/api/champions');
            if (res.ok) {{
                this.champions = await res.json();
                this.renderChampionsUI();
                return;
            }}
        }} catch (err) {{}}

        // Standalone Mode Fallback
        let saved = localStorage.getItem('quizzora_champions');
        if (saved) {{
            try {{
                const parsed = JSON.parse(saved);
                if (parsed.junior && (parsed.junior.player_nickname === 'Aarav Krishna' || parsed.junior.score === 1780 || parsed.junior.player_nickname === 'Aditya Verma' || parsed.junior.score === 1850)) {{
                    localStorage.removeItem('quizzora_champions');
                    saved = null;
                }}
            }} catch (e) {{}}
        }}
        this.champions = saved ? JSON.parse(saved) : {{ ...QUIZZORA_DEFAULT_CHAMPIONS }};
        this.renderChampionsUI();
    }},

    renderChampionsUI() {{
        const j = this.champions ? this.champions.junior : null;
        if (j) {{
            const nameEl = document.getElementById('junior-champ-name');
            const schoolEl = document.getElementById('junior-champ-school');
            const scoreEl = document.getElementById('junior-champ-score');
            const accEl = document.getElementById('junior-champ-acc');
            const dateEl = document.getElementById('junior-champ-date');
            const btnEl = document.getElementById('challenge-junior-champ-btn');
            if (nameEl) nameEl.textContent = j.player_nickname || 'Open - No Champion Yet';
            if (schoolEl) schoolEl.textContent = j.school_name || 'Be the First to Set Record';
            if (scoreEl) scoreEl.textContent = `${{j.score || 0}} PTS`;
            if (accEl) accEl.textContent = `${{j.accuracy || 0}}%`;
            if (dateEl) dateEl.textContent = j.date_achieved || '2026-10-30';
            if (btnEl) {{
                btnEl.textContent = (j.score && j.score > 0) ? 'CHALLENGE JUNIOR CHAMPION' : 'CLAIM JUNIOR CHAMPION TITLE';
            }}
        }}

        const c = this.champions ? this.champions.commerce : null;
        if (c) {{
            const nameEl = document.getElementById('commerce-champ-name');
            const schoolEl = document.getElementById('commerce-champ-school');
            const scoreEl = document.getElementById('commerce-champ-score');
            const accEl = document.getElementById('commerce-champ-acc');
            const dateEl = document.getElementById('commerce-champ-date');
            const btnEl = document.getElementById('challenge-commerce-champ-btn');
            if (nameEl) nameEl.textContent = c.player_nickname || 'Open - No Champion Yet';
            if (schoolEl) schoolEl.textContent = c.school_name || 'Be the First to Set Record';
            if (scoreEl) scoreEl.textContent = `${{c.score || 0}} PTS`;
            if (accEl) accEl.textContent = `${{c.accuracy || 0}}%`;
            if (dateEl) dateEl.textContent = c.date_achieved || '2026-10-30';
            if (btnEl) {{
                btnEl.textContent = (c.score && c.score > 0) ? 'CHALLENGE COMMERCE CHAMPION' : 'CLAIM COMMERCE CHAMPION TITLE';
            }}
        }}
    }},

    resetChampions() {{
        if (!confirm('Are you sure you want to reset the State Champions back to 0 PTS baseline?')) return;
        this.champions = {{
            junior: {{
                player_nickname: 'Open - No Champion Yet',
                school_name: 'Be the First to Set Record',
                score: 0,
                accuracy: 0,
                date_achieved: new Date().toISOString().split('T')[0],
                title: 'Awaiting Champion'
            }},
            commerce: {{
                player_nickname: 'Open - No Champion Yet',
                school_name: 'Be the First to Set Record',
                score: 0,
                accuracy: 0,
                date_achieved: new Date().toISOString().split('T')[0],
                title: 'Awaiting Champion'
            }}
        }};
        localStorage.setItem('quizzora_champions', JSON.stringify(this.champions));
        this.renderChampionsUI();
        this.showToast('State Champions reset to 0 PTS! The next high score will claim the crown.');
        try {{
            fetch('/api/admin/reset-champions', {{ method: 'POST' }});
        }} catch(e) {{}}
    }},

    initCountdown() {{
        // Target: 19 November 2026 at Marian College Kuttikkanam (20 full calendar days from Oct 30)
        const targetDate = new Date('2026-11-19T23:59:59+05:30').getTime();
        const update = () => {{
            const n = new Date();
            // Normalize year to 2026 so any browser running with a 2024/2025 machine clock counts from today (30-10-2026)!
            if (n.getFullYear() < 2026) {{
                n.setFullYear(2026);
            }}
            const nowMs = n.getTime();
            const diff = targetDate - nowMs;

            const daysEl = document.getElementById('timer-days') || document.getElementById('count-days');
            const hoursEl = document.getElementById('timer-hours') || document.getElementById('count-hours');
            const minsEl = document.getElementById('timer-minutes') || document.getElementById('timer-mins') || document.getElementById('count-mins');
            const secsEl = document.getElementById('timer-seconds') || document.getElementById('timer-secs') || document.getElementById('count-secs');

            if (!daysEl || !hoursEl || !minsEl || !secsEl) return;

            if (diff <= 0) {{
                daysEl.textContent = '00';
                hoursEl.textContent = '00';
                minsEl.textContent = '00';
                secsEl.textContent = '00';
                return;
            }}

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const secs = Math.floor((diff % (1000 * 60)) / 1000);

            daysEl.textContent = String(days).padStart(2, '0');
            hoursEl.textContent = String(hours).padStart(2, '0');
            minsEl.textContent = String(mins).padStart(2, '0');
            secsEl.textContent = String(secs).padStart(2, '0');
        }};

        update();
        if (this._countdownTimer) clearInterval(this._countdownTimer);
        this._countdownTimer = setInterval(update, 1000);
    }},

    loadPersonalBest() {{
        const pb = localStorage.getItem('quizzora_personal_best') || '0';
        const pbEl = document.getElementById('personal-best-score');
        if (pbEl) pbEl.textContent = `${{pb}} PTS`;
        const heroPb = document.getElementById('hero-personal-best');
        if (heroPb) heroPb.textContent = `${{pb}} PTS`;
    }},

    // ---------------- Prelim Centres Filter, Switcher & Search ----------------
    switchCentresView(mode) {{
        const tableView = document.getElementById('centres-table-view');
        const cardsView = document.getElementById('centres-cards-view');
        const btnTable = document.getElementById('btn-view-table');
        const btnCards = document.getElementById('btn-view-cards');

        if (mode === 'table') {{
            if (tableView) tableView.style.display = 'block';
            if (cardsView) cardsView.style.display = 'none';
            if (btnTable) btnTable.classList.add('active');
            if (btnCards) btnCards.classList.remove('active');
        }} else {{
            if (tableView) tableView.style.display = 'none';
            if (cardsView) cardsView.style.display = 'block';
            if (btnTable) btnTable.classList.remove('active');
            if (btnCards) btnCards.classList.add('active');
        }}
    }},

    filterCentres(district) {{
        document.querySelectorAll('.centre-filter-btn').forEach(btn => {{
            if (btn.getAttribute('data-filter') === district) {{
                btn.classList.add('active');
            }} else {{
                btn.classList.remove('active');
            }}
        }});

        // Filter Table Rows if present
        document.querySelectorAll('.centre-table-row').forEach(row => {{
            const rowDistrict = row.getAttribute('data-district');
            if (district === 'all' || rowDistrict === district) {{
                row.style.display = '';
            }} else {{
                row.style.display = 'none';
            }}
        }});

        // Filter Directory Cards with count tracking
        let visibleCount = 0;
        document.querySelectorAll('.centres-directory-grid .centre-dir-card').forEach(card => {{
            const cardDistrict = card.getAttribute('data-district');
            if (district === 'all' || cardDistrict === district) {{
                card.style.display = 'flex';
                visibleCount++;
            }} else {{
                card.style.display = 'none';
            }}
        }});

        const countEl = document.getElementById('centre-results-count');
        if (countEl) {{
            if (district === 'all') {{
                countEl.textContent = `Showing all ${{visibleCount}} examination centres across Kottayam, Idukki, Pathanamthitta & Ernakulam`;
            }} else {{
                const names = {{
                    kottayam: 'Kottayam District',
                    idukki: 'Idukki District',
                    pathanamthitta: 'Pathanamthitta District',
                    ernakulam: 'Ernakulam District',
                    campus: 'Marian College Campus'
                }};
                countEl.textContent = `Showing ${{visibleCount}} official examination centre(s) for ${{names[district] || district}}`;
            }}
        }}
    }},

    searchCentres(query) {{
        const q = (query || '').toLowerCase().trim();

        // Search Table Rows if present
        document.querySelectorAll('.centre-table-row').forEach(row => {{
            const text = row.textContent.toLowerCase();
            if (!q || text.includes(q)) {{
                row.style.display = '';
            }} else {{
                row.style.display = 'none';
            }}
        }});

        // Search Directory Cards with count tracking
        let visibleCount = 0;
        document.querySelectorAll('.centres-directory-grid .centre-dir-card').forEach(card => {{
            const text = card.textContent.toLowerCase();
            if (!q || text.includes(q)) {{
                card.style.display = 'flex';
                visibleCount++;
            }} else {{
                card.style.display = 'none';
            }}
        }});

        const countEl = document.getElementById('centre-results-count');
        if (countEl) {{
            if (!q) {{
                countEl.textContent = `Showing all ${{visibleCount}} examination centres across Kottayam, Idukki, Pathanamthitta & Ernakulam`;
            }} else {{
                countEl.textContent = `Found ${{visibleCount}} matching centre(s) for "${{query}}"`;
            }}
        }}
    }},

    handleIncomingChallenge(chalId) {{
        let chalData = null;
        try {{
            chalData = JSON.parse(atob(decodeURIComponent(chalId)));
        }} catch(e) {{
            const stored = localStorage.getItem('quizzora_challenges');
            if (stored) {{
                const map = JSON.parse(stored);
                chalData = map[chalId];
            }}
        }}

        if (!chalData) return;

        const banner = document.getElementById('challenge-received-banner');
        if (banner) {{
            banner.style.display = 'block';
            document.getElementById('challenger-name-text').textContent = chalData.nickname || 'Classmate';
            document.getElementById('challenger-score-text').textContent = `${{chalData.score || '--'}} PTS`;
            document.getElementById('challenger-cat-text').textContent = chalData.category === 'junior' ? 'Junior Quiz' : 'Commerce Quiz';
        }}

        this.openStartModal(chalData.category, 'challenge', chalId, chalData.question_ids);
    }},

    handleCategoryPick(category) {{
        this.player.category = category;
        this.player.mode = 'standard';
        this.player.challengeId = null;
        this.openStartModal(category, 'standard');
    }},

    challengeChampion(category) {{
        this.player.category = category;
        this.player.mode = 'champion';
        this.player.challengeId = null;
        this.openStartModal(category, 'champion');
    }},

    openStartModal(category, mode = 'standard', challengeId = null, challengeQIds = null) {{
        this.player.category = category;
        this.player.mode = mode;
        this.player.challengeId = challengeId;
        this.player.challengeQIds = challengeQIds;

        const modal = document.getElementById('start-quiz-modal');
        const nickInput = document.getElementById('player-nickname-input');
        const schoolInput = document.getElementById('player-school-input');
        const titleEl = document.getElementById('modal-quiz-title');
        const modeBadge = document.getElementById('modal-mode-badge');

        if (nickInput) nickInput.value = this.player.nickname;
        if (schoolInput) schoolInput.value = this.player.school;

        const catName = category === 'junior' ? 'Junior Quiz (Classes 8-10)' : 'Senior Commerce Quiz (Classes 11-12)';
        if (titleEl) titleEl.textContent = catName;

        if (modeBadge) {{
            if (mode === 'champion') {{
                modeBadge.textContent = 'CHALLENGE THE CHAMPION MODE';
                modeBadge.className = 'hero-badge-pill';
                modeBadge.style.background = 'rgba(255, 215, 0, 0.2)';
                modeBadge.style.color = '#ffd700';
            }} else if (mode === 'challenge') {{
                modeBadge.textContent = 'FRIEND CHALLENGE MATCH';
                modeBadge.className = 'hero-badge-pill';
            }} else {{
                modeBadge.textContent = 'STANDARD 15-QUESTION BATTLE';
                modeBadge.className = 'hero-badge-pill';
            }}
        }}

        modal.classList.add('active');
    }},

    closeStartModal() {{
        document.getElementById('start-quiz-modal')?.classList.remove('active');
    }},

    async confirmAndStartQuiz() {{
        const nickname = document.getElementById('player-nickname-input').value.trim() || 'Quizzer';
        const school = document.getElementById('player-school-input').value.trim() || '';

        this.player.nickname = nickname;
        this.player.school = school;
        localStorage.setItem('quizzora_nickname', nickname);
        localStorage.setItem('quizzora_school', school);

        this.closeStartModal();

        // 1. Try API if online
        try {{
            const res = await fetch('/api/quiz/start', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    nickname: this.player.nickname,
                    school_name: this.player.school,
                    category: this.player.category,
                    mode: this.player.mode,
                    challenge_id: this.player.challengeId
                }})
            }});

            if (res.ok) {{
                const data = await res.json();
                this.session.id = data.session_id;
                this.session.questions = data.questions;
                this.session.currentIndex = 0;
                this.session.score = 0;
                this.session.streak = 0;
                this.session.correctCount = 0;
                this.session.totalTimeTaken = 0;
                this.session.startTime = Date.now();
                this.showView('view-arena');
                this.renderCurrentQuestion();
                return;
            }}
        }} catch (err) {{}}

        // 2. Standalone Client-Side Generation
        const catQuestions = this.questionsBank.filter(q => q.category === this.player.category);
        let selected = [];

        if (this.player.challengeQIds && Array.isArray(this.player.challengeQIds)) {{
            selected = this.player.challengeQIds.map(id => this.questionsBank.find(q => q.id === id)).filter(Boolean);
        }}
        if (selected.length < 15) {{
            const shuffled = [...catQuestions].sort(() => 0.5 - Math.random());
            selected = shuffled.slice(0, 15);
        }}

        this.session.id = 'standalone-' + Date.now();
        this.session.questions = selected;
        this.session.currentIndex = 0;
        this.session.score = 0;
        this.session.streak = 0;
        this.session.correctCount = 0;
        this.session.totalTimeTaken = 0;
        this.session.startTime = Date.now();

        this.showView('view-arena');
        this.renderCurrentQuestion();
    }},

    renderCurrentQuestion() {{
        const q = this.session.questions[this.session.currentIndex];
        if (!q) {{
            this.finishQuiz();
            return;
        }}

        this.session.answered = false;
        this.session.timeRemaining = 20;

        document.getElementById('hud-q-counter').textContent = `${{this.session.currentIndex + 1}} / ${{this.session.questions.length}}`;
        document.getElementById('hud-score').textContent = this.session.score;
        
        const streakEl = document.getElementById('hud-streak');
        if (this.session.streak > 1) {{
            streakEl.textContent = `${{this.session.streak}}X STREAK`;
            streakEl.style.display = 'block';
        }} else {{
            streakEl.style.display = 'none';
        }}

        const progressPct = ((this.session.currentIndex) / this.session.questions.length) * 100;
        document.getElementById('quiz-progress-bar-fill').style.width = `${{progressPct}}%`;

        document.getElementById('q-topic-badge').textContent = q.topic;
        document.getElementById('q-text').textContent = q.question;

        const fbBox = document.getElementById('feedback-box');
        if (fbBox) fbBox.style.display = 'none';

        const optGrid = document.getElementById('options-grid');
        optGrid.innerHTML = '';

        const keys = ['A', 'B', 'C', 'D'];
        q.options.forEach((optText, idx) => {{
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerHTML = `<span class="opt-key">${{keys[idx]}}</span><span>${{optText}}</span>`;
            btn.addEventListener('click', () => this.handleAnswerSelect(idx, btn));
            optGrid.appendChild(btn);
        }});

        this.startQuestionTimer();
    }},

    startQuestionTimer() {{
        clearInterval(this.session.timer);
        const timerText = document.getElementById('timer-sec-text');
        const timerCircle = document.getElementById('timer-circle-progress');
        const totalDuration = 20;
        const circumference = 2 * Math.PI * 27;

        timerCircle.style.strokeDasharray = `${{circumference}} ${{circumference}}`;
        timerCircle.style.stroke = 'var(--primary)';

        const step = () => {{
            timerText.textContent = Math.ceil(this.session.timeRemaining);
            const offset = circumference - (this.session.timeRemaining / totalDuration) * circumference;
            timerCircle.style.strokeDashoffset = offset;

            if (this.session.timeRemaining <= 5 && this.session.timeRemaining > 0) {{
                window.quizzoraAudio.playWarning();
                timerCircle.style.stroke = 'var(--danger)';
            }} else if (this.session.timeRemaining <= 10) {{
                timerCircle.style.stroke = '#ffb800';
            }}

            if (this.session.timeRemaining <= 0) {{
                clearInterval(this.session.timer);
                this.handleTimeUp();
            }} else {{
                this.session.timeRemaining -= 0.1;
                this.session.totalTimeTaken += 0.1;
            }}
        }};

        step();
        this.session.timer = setInterval(step, 100);
    }},

    async handleAnswerSelect(selectedIndex, selectedBtn) {{
        if (this.session.answered) return;
        this.session.answered = true;
        clearInterval(this.session.timer);

        const currentQ = this.session.questions[this.session.currentIndex];
        const allBtns = document.querySelectorAll('.option-btn');
        allBtns.forEach(b => b.disabled = true);

        // Try API first
        try {{
            const res = await fetch('/api/quiz/answer', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    session_id: this.session.id,
                    question_id: currentQ.id,
                    selected_index: selectedIndex,
                    time_remaining: Math.max(0, this.session.timeRemaining)
                }})
            }});

            if (res.ok) {{
                const data = await res.json();
                this.processAnswerResult(data, selectedIndex, selectedBtn, allBtns);
                return;
            }}
        }} catch (err) {{}}

        // Standalone Mode Calculation
        const isCorrect = (selectedIndex === currentQ.correct_index);
        let ptsAwarded = 0;
        if (isCorrect) {{
            this.session.streak++;
            this.session.correctCount++;
            const base = 100;
            const timeBonus = Math.round(Math.max(0, this.session.timeRemaining) * 5);
            const streakBonus = this.session.streak >= 3 ? 50 : (this.session.streak >= 2 ? 25 : 0);
            ptsAwarded = base + timeBonus + streakBonus;
            this.session.score += ptsAwarded;
        }} else {{
            this.session.streak = 0;
        }}

        const resultData = {{
            is_correct: isCorrect,
            correct_index: currentQ.correct_index,
            points_awarded: ptsAwarded,
            current_score: this.session.score,
            streak: this.session.streak,
            explanation: currentQ.explanation
        }};

        this.processAnswerResult(resultData, selectedIndex, selectedBtn, allBtns);
    }},

    processAnswerResult(data, selectedIndex, selectedBtn, allBtns) {{
        const isCorrect = data.is_correct;
        const fbBox = document.getElementById('feedback-box');
        const fbTitle = document.getElementById('feedback-title');
        const fbExpl = document.getElementById('feedback-explanation');

        if (isCorrect) {{
            selectedBtn.classList.add('correct');
            window.quizzoraAudio.playCorrect();
            if (fbBox) {{
                fbBox.style.display = 'block';
                fbTitle.innerHTML = `<span style="color:var(--success)">Correct! +${{data.points_awarded}} PTS</span>`;
                fbExpl.textContent = data.explanation || 'Excellent knowledge!';
            }}
        }} else {{
            selectedBtn.classList.add('wrong');
            if (allBtns[data.correct_index]) {{
                allBtns[data.correct_index].classList.add('correct');
            }}
            window.quizzoraAudio.playWrong();
            if (fbBox) {{
                fbBox.style.display = 'block';
                fbTitle.innerHTML = `<span style="color:var(--danger)">Incorrect</span>`;
                fbExpl.textContent = data.explanation || 'Review the correct answer highlighted above.';
            }}
        }}

        document.getElementById('hud-score').textContent = this.session.score;
        const streakEl = document.getElementById('hud-streak');
        if (this.session.streak > 1) {{
            streakEl.textContent = `${{this.session.streak}}X STREAK`;
            streakEl.style.display = 'block';
        }} else {{
            streakEl.style.display = 'none';
        }}

        setTimeout(() => {{
            this.session.currentIndex++;
            this.renderCurrentQuestion();
        }}, 1800);
    }},

    handleTimeUp() {{
        if (this.session.answered) return;
        this.session.answered = true;

        const currentQ = this.session.questions[this.session.currentIndex];
        const allBtns = document.querySelectorAll('.option-btn');
        allBtns.forEach(b => b.disabled = true);
        window.quizzoraAudio.playWrong();
        this.session.streak = 0;

        if (allBtns[currentQ.correct_index]) {{
            allBtns[currentQ.correct_index].classList.add('correct');
        }}

        const fbBox = document.getElementById('feedback-box');
        if (fbBox) {{
            fbBox.style.display = 'block';
            document.getElementById('feedback-title').innerHTML = `<span style="color:var(--danger)">TIME UP</span>`;
            document.getElementById('feedback-explanation').textContent = currentQ.explanation || 'Time ran out for this question.';
        }}

        setTimeout(() => {{
            this.session.currentIndex++;
            this.renderCurrentQuestion();
        }}, 1800);
    }},

    async finishQuiz() {{
        clearInterval(this.session.timer);
        const timeTakenSeconds = Math.max(1, Math.round(this.session.totalTimeTaken));

        // Try API first
        try {{
            const res = await fetch('/api/quiz/finish', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    session_id: this.session.id,
                    time_taken_seconds: timeTakenSeconds
                }})
            }});

            if (res.ok) {{
                const data = await res.json();
                this.renderResults(data);
                return;
            }}
        }} catch (err) {{}}

        // Standalone Mode Score Calculation
        const totalQ = this.session.questions.length || 15;
        const correctCount = this.session.correctCount;
        const accuracy = Math.round((correctCount / totalQ) * 1000) / 10;
        const finalScore = this.session.score;

        let title = "Quiz Beginner";
        if (finalScore >= 1600) title = "Quizzora Legend";
        else if (finalScore >= 1300) title = "Brain Champion";
        else if (finalScore >= 1000) title = "Quiz Master";
        else if (finalScore >= 600) title = "Knowledge Explorer";

        const currentChamp = (this.champions && this.champions[this.player.category]) ? this.champions[this.player.category] : {{ score: 0 }};
        const champScore = (currentChamp.score !== undefined && currentChamp.score !== null) ? currentChamp.score : 0;
        const isNewChampion = (finalScore > champScore);

        if (isNewChampion) {{
            const newChampObj = {{
                player_nickname: this.player.nickname,
                school_name: this.player.school,
                score: finalScore,
                accuracy: accuracy,
                date_achieved: new Date().toISOString().split('T')[0],
                title: title
            }};
            this.champions[this.player.category] = newChampObj;
            localStorage.setItem('quizzora_champions', JSON.stringify(this.champions));
            this.renderChampionsUI();
        }}

        // Save entry into localStorage leaderboard
        const lbKey = 'quizzora_leaderboard';
        const existingLb = JSON.parse(localStorage.getItem(lbKey) || '[]');
        const newEntry = {{
            id: 'score-' + Date.now(),
            player_nickname: this.player.nickname,
            school_name: this.player.school,
            category: this.player.category,
            score: finalScore,
            accuracy: accuracy,
            correct_count: correctCount,
            total_questions: totalQ,
            time_taken_seconds: timeTakenSeconds,
            streak_max: this.session.streak,
            title: title,
            created_at: new Date().toISOString()
        }};
        existingLb.push(newEntry);
        existingLb.sort((a, b) => b.score - a.score);
        localStorage.setItem(lbKey, JSON.stringify(existingLb));

        // Generate challenge payload string
        const qIds = this.session.questions.map(q => q.id);
        const chalObj = {{
            nickname: this.player.nickname,
            school: this.player.school,
            category: this.player.category,
            score: finalScore,
            question_ids: qIds
        }};
        const chalId = btoa(JSON.stringify(chalObj));

        const resultData = {{
            nickname: this.player.nickname,
            school: this.player.school,
            category: this.player.category,
            final_score: finalScore,
            correct_count: correctCount,
            total_questions: totalQ,
            accuracy: accuracy,
            time_taken_seconds: timeTakenSeconds,
            streak_max: this.session.streak,
            title: title,
            is_new_champion: isNewChampion,
            champion_nickname: currentChamp.player_nickname,
            champion_score: currentChamp.score,
            challenge_id: chalId
        }};

        this.renderResults(resultData);
    }},

    renderResults(data) {{
        this.showView('view-results');

        const prevPB = parseInt(localStorage.getItem('quizzora_personal_best') || '0', 10);
        if (data.final_score > prevPB) {{
            localStorage.setItem('quizzora_personal_best', data.final_score);
            this.loadPersonalBest();
        }}

        window.quizzoraConfetti.fire(4000, 150);

        if (data.is_new_champion) {{
            window.quizzoraAudio.playChampionAlert();
        }} else {{
            window.quizzoraAudio.playVictory();
        }}

        document.getElementById('results-player-name').textContent = this.player.nickname;
        document.getElementById('results-school-name').textContent = this.player.school || 'Quizzora Competitor';
        document.getElementById('results-title-badge').textContent = data.title.toUpperCase();
        document.getElementById('results-final-score').textContent = `${{data.final_score}} PTS`;
        document.getElementById('res-stat-accuracy').textContent = `${{data.accuracy}}%`;
        document.getElementById('res-stat-correct').textContent = `${{data.correct_count}}/${{data.total_questions}}`;
        document.getElementById('res-stat-time').textContent = `${{data.time_taken_seconds}}s`;
        document.getElementById('res-stat-streak').textContent = `${{data.streak_max}}`;

        const champVerdict = document.getElementById('results-champion-verdict');
        if (champVerdict) {{
            if (data.is_new_champion) {{
                champVerdict.className = 'champion-alert-banner champion-alert-win';
                champVerdict.innerHTML = `
                    <div class="champion-crown-tag" style="display:inline-block; margin-bottom:10px;">NEW STATE RECORD</div>
                    <h3 style="font-family: var(--font-heading); font-size: 1.6rem; color: var(--gold); margin-bottom: 6px;">
                        NEW CHAMPION ALERT
                    </h3>
                    <p style="font-weight: 700; font-size: 1.1rem; color: #fff; margin-bottom: 6px;">
                        OUTSTANDING! YOU HAVE DEFEATED THE QUIZZORA CHAMPION!
                    </p>
                    <p style="font-size: 0.95rem; color: #e2e8f0;">
                        You are now the reigning <strong>${{data.category === 'junior' ? 'Junior Quiz' : 'Senior Commerce'}}</strong> Champion! Can someone beat your score?
                    </p>
                `;
            }} else {{
                champVerdict.className = 'champion-alert-banner champion-alert-loss';
                champVerdict.innerHTML = `
                    <div class="champion-crown-tag" style="display:inline-block; margin-bottom:6px; border-color:var(--primary); color:var(--primary);">CHAMPIONSHIP STATUS</div>
                    <h4 style="font-family: var(--font-heading); font-size: 1.25rem; color: var(--primary); margin-bottom: 4px;">
                        THE CHAMPION STILL STANDS
                    </h4>
                    <p style="font-size: 0.92rem; color: var(--text-muted);">
                        Current Champion: <strong>${{data.champion_nickname || 'Reigning Champ'}}</strong> with <strong>${{data.champion_score}} PTS</strong>.<br>
                        You came close, but the crown is still theirs. Think you can do better? Play again!
                    </p>
                `;
            }}
        }}

        const baseUrl = window.location.origin + window.location.pathname;
        const challengeUrl = `${{baseUrl}}?c=${{data.challenge_id}}`;
        const chalInput = document.getElementById('results-challenge-link-input');
        if (chalInput) chalInput.value = challengeUrl;

        const waBtn = document.getElementById('results-whatsapp-share-btn');
        if (waBtn) {{
            const cleanShare = `I scored ${{data.final_score}} PTS (${{data.accuracy}}% accuracy) in Quizzora: ${{data.category === 'junior' ? 'Junior Quiz' : 'Senior Commerce'}}! Think you can beat me? Challenge link:`;
            const waText = encodeURIComponent(`${{cleanShare}} ${{challengeUrl}}`);
            waBtn.href = `https://api.whatsapp.com/send?text=${{waText}}`;
        }}

        const copyBtn = document.getElementById('results-copy-link-btn');
        if (copyBtn) {{
            copyBtn.onclick = () => {{
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(challengeUrl).then(() => {{
                        this.showToast('Challenge link copied to clipboard');
                    }}).catch(() => {{
                        if (chalInput) {{
                            chalInput.select();
                            document.execCommand('copy');
                        }}
                        this.showToast('Challenge link copied to clipboard');
                    }});
                }} else if (chalInput) {{
                    chalInput.select();
                    document.execCommand('copy');
                    this.showToast('Challenge link copied to clipboard');
                }}
            }};
        }}

        this.lastResult = data;
    }},

    loadImage(src) {{
        return new Promise((resolve) => {{
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => resolve(img);
            img.onerror = () => resolve(null);
            img.src = src;
        }});
    }},

    async generateInstagramStoryCard() {{
        if (!this.lastResult) {{
            this.showToast('No recent quiz result to export');
            return;
        }}

        const canvas = document.getElementById('instagram-story-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const res = this.lastResult;
        const nick = this.player.nickname || 'Quizzer';
        const school = this.player.school || 'Kerala High School';
        const cat = res.category === 'junior' ? 'JUNIOR QUIZ (CLASS 8-10)' : 'SENIOR COMMERCE QUIZ (CLASS 11-12)';

        this.showToast('Generating Instagram Story Card...');

        // 1. Background gradient
        const bgGrad = ctx.createLinearGradient(0, 0, 1080, 1920);
        bgGrad.addColorStop(0, '#060919');
        bgGrad.addColorStop(0.25, '#0b1236');
        bgGrad.addColorStop(0.75, '#140c32');
        bgGrad.addColorStop(1, '#060919');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, 1080, 1920);

        // Cyber grid subtle lines
        ctx.strokeStyle = 'rgba(0, 210, 255, 0.08)';
        ctx.lineWidth = 2;
        for (let x = 0; x < 1080; x += 60) {{
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, 1920);
            ctx.stroke();
        }}
        for (let y = 0; y < 1920; y += 60) {{
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(1080, y);
            ctx.stroke();
        }}

        // Neon Glow Orbs
        const radial1 = ctx.createRadialGradient(250, 350, 40, 250, 350, 400);
        radial1.addColorStop(0, 'rgba(0, 210, 255, 0.28)');
        radial1.addColorStop(1, 'transparent');
        ctx.fillStyle = radial1;
        ctx.fillRect(0, 0, 1080, 1920);

        const radial2 = ctx.createRadialGradient(850, 1250, 40, 850, 1250, 420);
        radial2.addColorStop(0, 'rgba(121, 40, 202, 0.28)');
        radial2.addColorStop(1, 'transparent');
        ctx.fillStyle = radial2;
        ctx.fillRect(0, 0, 1080, 1920);

        // 2. Official Quizzora Logo inside story card
        const logoImg = await this.loadImage(QUIZZORA_ASSETS.logo);
        if (logoImg) {{
            const logoW = 580;
            const logoH = Math.round(logoW * (logoImg.naturalHeight / logoImg.naturalWidth));
            const logoX = (1080 - logoW) / 2;
            const logoY = 90;
            ctx.shadowColor = 'rgba(0, 210, 255, 0.7)';
            ctx.shadowBlur = 24;
            ctx.drawImage(logoImg, logoX, logoY, logoW, logoH);
            ctx.shadowColor = 'transparent';
            ctx.shadowBlur = 0;
        }} else {{
            ctx.fillStyle = '#00d2ff';
            ctx.font = 'bold 54px "Space Grotesk", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('QUIZZORA', 540, 160);
        }}

        // Subtitle below logo
        ctx.fillStyle = '#ffd700';
        ctx.font = 'bold 26px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('INTER-SCHOOL STATE-LEVEL QUIZ COMPETITION', 540, 285);

        ctx.fillStyle = '#ffffff';
        ctx.font = '900 52px "Space Grotesk", sans-serif';
        ctx.fillText('CHALLENGE SCORECARD', 540, 355);

        // Category Tag Box
        ctx.beginPath();
        ctx.fillStyle = 'rgba(0, 210, 255, 0.15)';
        ctx.strokeStyle = '#00d2ff';
        ctx.lineWidth = 3;
        ctx.roundRect(170, 385, 740, 60, 30);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#00d2ff';
        ctx.font = 'bold 28px "Space Grotesk", sans-serif';
        ctx.fillText(cat, 540, 426);

        // 3. Central Glass Score Card
        ctx.beginPath();
        ctx.fillStyle = 'rgba(13, 20, 51, 0.92)';
        ctx.strokeStyle = 'rgba(255, 215, 0, 0.65)';
        ctx.lineWidth = 4;
        ctx.roundRect(90, 475, 900, 860, 32);
        ctx.fill();
        ctx.stroke();

        // Player Name & School
        ctx.fillStyle = '#ffffff';
        ctx.font = '900 60px "Space Grotesk", sans-serif';
        ctx.fillText(nick, 540, 570);

        ctx.fillStyle = '#94a3b8';
        ctx.font = '500 32px "Outfit", sans-serif';
        ctx.fillText(school, 540, 625);

        // Score Big Display
        ctx.shadowColor = 'rgba(255, 215, 0, 0.5)';
        ctx.shadowBlur = 30;
        ctx.fillStyle = '#ffd700';
        ctx.font = '900 138px "Space Grotesk", sans-serif';
        ctx.fillText(`${{res.final_score}} PTS`, 540, 775);
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#00d2ff';
        ctx.font = 'bold 36px "Space Grotesk", sans-serif';
        ctx.fillText(res.title.toUpperCase(), 540, 845);

        // 2x2 Stats Grid inside card
        const statBoxes = [
            {{ label: 'ACCURACY', val: `${{res.accuracy}}%`, x: 160, y: 910 }},
            {{ label: 'CORRECT', val: `${{res.correct_count}} / ${{res.total_questions}}`, x: 580, y: 910 }},
            {{ label: 'TIME TAKEN', val: `${{res.time_taken_seconds}}s`, x: 160, y: 1080 }},
            {{ label: 'MAX STREAK', val: `${{res.streak_max}}`, x: 580, y: 1080 }}
        ];

        statBoxes.forEach(sb => {{
            ctx.beginPath();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.06)';
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
            ctx.lineWidth = 2;
            ctx.roundRect(sb.x, sb.y, 340, 135, 16);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#ffffff';
            ctx.font = '900 48px "Space Grotesk", sans-serif';
            ctx.fillText(sb.val, sb.x + 170, sb.y + 68);

            ctx.fillStyle = '#94a3b8';
            ctx.font = 'bold 22px "Space Grotesk", sans-serif';
            ctx.fillText(sb.label, sb.x + 170, sb.y + 110);
        }});

        // 4. Challenge Dare Message
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 42px "Space Grotesk", sans-serif';
        ctx.fillText('CAN YOU BEAT MY SCORE?', 540, 1400);

        ctx.fillStyle = '#00d2ff';
        ctx.font = 'bold 32px "Outfit", sans-serif';
        ctx.fillText('TAG @scapsquizzora ON INSTAGRAM STORY', 540, 1460);

        ctx.fillStyle = '#ffd700';
        ctx.font = 'bold 27px "Space Grotesk", sans-serif';
        ctx.fillText('SEMI-FINALS & GRAND FINALE: 19 NOVEMBER 2026', 540, 1515);

        ctx.fillStyle = '#00d2ff';
        ctx.font = 'bold 22px "Outfit", sans-serif';
        ctx.fillText('VENUE: MARIAN COLLEGE KUTTIKKANAM (AUTONOMOUS)', 540, 1550);

        // 5. Registration QR code at bottom
        const qrImg = await this.loadImage(QUIZZORA_ASSETS.qr);
        if (qrImg) {{
            const qrSize = 170;
            const qrX = (1080 - qrSize) / 2;
            const qrY = 1575;

            ctx.beginPath();
            ctx.fillStyle = '#ffffff';
            ctx.roundRect(qrX - 10, qrY - 10, qrSize + 20, qrSize + 20, 14);
            ctx.fill();
            ctx.drawImage(qrImg, qrX, qrY, qrSize, qrSize);

            ctx.fillStyle = '#94a3b8';
            ctx.font = 'bold 22px "Outfit", sans-serif';
            ctx.fillText('SCAN QR CODE TO REGISTER FOR STATE FINALS', 540, 1805);
        }}

        // Download image directly
        const dataUrl = canvas.toDataURL('image/png');
        const dlLink = document.createElement('a');
        dlLink.download = `quizzora-challenge-${{nick.replace(/\\s+/g, '_')}}.png`;
        dlLink.href = dataUrl;
        dlLink.click();

        this.showToast('Instagram Story Card downloaded! Share to your Story and tag @scapsquizzora');
    }},

    async loadLeaderboard(category = 'all') {{
        const tableBody = document.getElementById('lb-table-body');
        if (tableBody) tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:30px;">Loading champions...</td></tr>';

        // Try API first
        try {{
            const res = await fetch(`/api/leaderboard?category=${{category}}`);
            if (res.ok) {{
                const data = await res.json();
                this.renderLeaderboardTable(data.leaderboard || []);
                return;
            }}
        }} catch (err) {{}}

        // Standalone Mode Fallback
        const stored = JSON.parse(localStorage.getItem('quizzora_leaderboard') || '[]');
        let filtered = stored;
        if (category === 'junior' || category === 'commerce') {{
            filtered = stored.filter(item => item.category === category);
        }}
        filtered.sort((a, b) => b.score - a.score);

        const list = filtered.map((item, idx) => ({{
            ...item,
            rank: idx + 1
        }}));

        this.renderLeaderboardTable(list);
    }},

    renderLeaderboardTable(list) {{
        const tableBody = document.getElementById('lb-table-body');

        // Render Podium (Top 3)
        const p1 = list[0] || null;
        const p2 = list[1] || null;
        const p3 = list[2] || null;

        this.renderPodiumSlot('podium-p1', p1, '1');
        this.renderPodiumSlot('podium-p2', p2, '2');
        this.renderPodiumSlot('podium-p3', p3, '3');

        // Render table
        if (tableBody) {{
            if (list.length === 0) {{
                tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:30px;">No quiz records yet. Be the first to play!</td></tr>';
                return;
            }}

            tableBody.innerHTML = list.map((item, idx) => {{
                const rankClass = idx === 0 ? 'rank-1' : (idx === 1 ? 'rank-2' : (idx === 2 ? 'rank-3' : ''));
                const catTag = item.category === 'junior' 
                    ? '<span class="topic-tag" style="color:var(--primary); border-color:var(--primary);">Junior GK</span>'
                    : '<span class="topic-tag" style="color:#c084fc; border-color:#c084fc;">Commerce</span>';

                return `
                    <tr>
                        <td><span class="rank-pill ${{rankClass}}">${{item.rank}}</span></td>
                        <td>
                            <strong>${{this.escapeHtml(item.player_nickname)}}</strong>
                            <div style="font-size:0.75rem; color:var(--text-muted);">${{this.escapeHtml(item.school_name || 'Kerala School')}}</div>
                        </td>
                        <td>${{catTag}}</td>
                        <td><strong style="color:var(--primary); font-family:var(--font-heading); font-size:1.1rem;">${{item.score}}</strong></td>
                        <td>${{item.accuracy}}%</td>
                        <td style="font-size:0.8rem; color:var(--text-muted);">${{item.title || 'Competitor'}}</td>
                    </tr>
                `;
            }}).join('');
        }}
    }},

    renderPodiumSlot(containerId, item, medalNum) {{
        const slot = document.getElementById(containerId);
        if (!slot) return;
        if (!item) {{
            slot.querySelector('.podium-player-name').textContent = 'Open Spot';
            slot.querySelector('.podium-player-score').textContent = '-- PTS';
            return;
        }}
        slot.querySelector('.podium-player-name').textContent = item.player_nickname;
        slot.querySelector('.podium-player-score').textContent = `${{item.score}} PTS`;
    }},

    escapeHtml(str) {{
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({{
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }}[tag] || tag)
        );
    }},

    // ---------------- Admin Features ----------------
    openAdminModal() {{
        document.getElementById('admin-login-modal')?.classList.add('active');
    }},

    closeAdminModal() {{
        document.getElementById('admin-login-modal')?.classList.remove('active');
    }},

    async handleAdminLogin() {{
        const pin = document.getElementById('admin-pin-input')?.value.trim();
        if (!pin) return;

        // Verify PIN
        const validPin = this.config.admin_pin || 'quizzora2026';
        if (pin === validPin) {{
            this.adminToken = pin;
            this.closeAdminModal();
            this.showView('view-admin');
            this.loadAdminStats();
            this.loadAdminQuestions();
            this.showToast('Admin Portal Unlocked');
        }} else {{
            this.showToast('Invalid Admin PIN');
        }}
    }},

    async loadAdminStats() {{
        const lb = JSON.parse(localStorage.getItem('quizzora_leaderboard') || '[]');
        const totalGames = lb.length;
        const uniquePlayers = new Set(lb.map(s => s.player_nickname)).size;
        const avgScore = totalGames ? Math.round(lb.reduce((a, b) => a + b.score, 0) / totalGames) : 0;
        const jQ = this.questionsBank.filter(q => q.category === 'junior').length;
        const cQ = this.questionsBank.filter(q => q.category === 'commerce').length;

        document.getElementById('adm-stat-total-games').textContent = totalGames;
        document.getElementById('adm-stat-unique-players').textContent = uniquePlayers;
        document.getElementById('adm-stat-avg-score').textContent = avgScore;
        document.getElementById('adm-stat-junior-q').textContent = jQ;
        document.getElementById('adm-stat-commerce-q').textContent = cQ;
    }},

    async loadAdminQuestions() {{
        const container = document.getElementById('admin-questions-list');
        if (!container) return;

        container.innerHTML = this.questionsBank.slice(0, 50).map(q => `
            <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <span class="topic-tag" style="color:var(--primary);">${{q.category.toUpperCase()}} • ${{this.escapeHtml(q.topic)}}</span>
                    <button onclick="App.deleteQuestion(${{q.id}})" class="btn btn-outline" style="padding:4px 10px; font-size:0.75rem; border-color:var(--danger); color:var(--danger);">Delete</button>
                </div>
                <h4 style="margin-bottom:8px; font-size:1rem;">${{this.escapeHtml(q.question)}}</h4>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:4px;">
                    Correct: <strong style="color:var(--success);">${{this.escapeHtml(q.options[q.correct_index])}}</strong>
                </div>
                <div style="font-size:0.8rem; color:#94a3b8;">${{this.escapeHtml(q.explanation || '')}}</div>
            </div>
        `).join('');
    }},

    async handleAddQuestion(e) {{
        e.preventDefault();
        const category = document.getElementById('new-q-category').value;
        const topic = document.getElementById('new-q-topic').value.trim();
        const question = document.getElementById('new-q-text').value.trim();
        const opt0 = document.getElementById('new-q-opt0').value.trim();
        const opt1 = document.getElementById('new-q-opt1').value.trim();
        const opt2 = document.getElementById('new-q-opt2').value.trim();
        const opt3 = document.getElementById('new-q-opt3').value.trim();
        const correctIndex = parseInt(document.getElementById('new-q-correct').value, 10);
        const explanation = document.getElementById('new-q-explanation').value.trim();

        const newQ = {{
            id: Date.now(),
            category,
            topic,
            question,
            options: [opt0, opt1, opt2, opt3],
            correct_index: correctIndex,
            explanation,
            difficulty: 'medium'
        }};

        this.questionsBank.unshift(newQ);
        const custom = JSON.parse(localStorage.getItem('quizzora_custom_questions') || '[]');
        custom.unshift(newQ);
        localStorage.setItem('quizzora_custom_questions', JSON.stringify(custom));

        this.showToast('Question Added Successfully!');
        document.getElementById('add-question-form').reset();
        this.loadAdminQuestions();
        this.loadAdminStats();
    }},

    async deleteQuestion(id) {{
        if (!confirm('Are you sure you want to delete this question?')) return;
        this.questionsBank = this.questionsBank.filter(q => q.id !== id);
        const custom = JSON.parse(localStorage.getItem('quizzora_custom_questions') || '[]');
        const updated = custom.filter(q => q.id !== id);
        localStorage.setItem('quizzora_custom_questions', JSON.stringify(updated));

        this.showToast('Question Deleted');
        this.loadAdminQuestions();
        this.loadAdminStats();
    }},

    async handleSaveSettings(e) {{
        e.preventDefault();
        const instaUrl = document.getElementById('adm-input-insta').value.trim();
        const formUrl = document.getElementById('adm-input-form').value.trim();
        const bannerText = document.getElementById('adm-input-banner').value.trim();

        if (instaUrl) this.config.instagram_url = instaUrl;
        if (formUrl) this.config.google_form_url = formUrl;
        if (bannerText) this.config.announcement_banner = bannerText;

        localStorage.setItem('quizzora_settings', JSON.stringify(this.config));
        this.showToast('Settings Updated Successfully!');
        this.applyConfig();
    }}
}};

window.App = App;

window.addEventListener('DOMContentLoaded', () => {{
    App.init();
}});
"""

    # Inject the inline script before </body> using lambda to avoid backslash escape template issues
    final_html = script_pattern.sub(lambda m: f"<script>\n{standalone_js}\n</script>", html)

    # Write out to root index.html
    out_path = "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    size = os.path.getsize(out_path)
    print(f"Generated standalone index.html at root: {size} bytes ({round(size/1024, 1)} KB)")

if __name__ == "__main__":
    build()
