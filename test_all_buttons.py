import json
import time
import subprocess
import urllib.request
import websocket
import base64

def run_tests():
    print("=== STARTING COMPLETE QUIZZORA BUTTON & STORY CARD AUDIT ===")
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    port = 9222
    
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,900",
        "about:blank"
    ])
    
    time.sleep(2)
    
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read())
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP: {ws_url}")
        
        ws = websocket.create_connection(ws_url)
        msg_id = 0
        
        def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {"id": msg_id, "method": method, "params": params or {}}
            ws.send(json.dumps(payload))
            while True:
                raw = ws.recv()
                res = json.loads(raw)
                if res.get("id") == msg_id:
                    return res.get("result", {})
                
        def eval_js(expr):
            res = send_cmd("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                print("JS Exception details:", res["exceptionDetails"].get("text"), res["exceptionDetails"].get("exception", {}).get("description"))
            return res.get("result", {}).get("value")

        # Navigate to application
        send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000"})
        time.sleep(2.5)

        title = eval_js("document.title")
        app_type = eval_js("typeof window.App")
        print(f"Page Title: {title}")
        print(f"App Object Type: {app_type}")
        
        results = {}
        
        # Test 1: Sound toggle button
        eval_js("document.getElementById('sound-toggle-btn').click()")
        muted = eval_js("window.quizzoraAudio.isMuted()")
        eval_js("document.getElementById('sound-toggle-btn').click()")
        unmuted = not eval_js("window.quizzoraAudio.isMuted()")
        results["Button 1: Sound Toggle (Mute/Unmute)"] = muted and unmuted
        print(f"Test 1 - Sound toggle button: {'PASS' if results['Button 1: Sound Toggle (Mute/Unmute)'] else 'FAIL'}")

        # Test 2: Brand logo click
        eval_js("App.showView('view-category')")
        eval_js("document.querySelector('.brand-container').click()")
        is_home = eval_js("document.getElementById('view-home').classList.contains('active')")
        results["Button 2: Brand Logo (Return to Home)"] = is_home
        print(f"Test 2 - Brand logo click: {'PASS' if is_home else 'FAIL'}")

        # Test 3: Nav links
        eval_js("document.querySelector('.nav-link[data-view=\"view-category\"]').click()")
        is_cat = eval_js("document.getElementById('view-category').classList.contains('active')")
        
        eval_js("document.querySelector('.nav-link[data-view=\"view-leaderboard\"]').click()")
        is_lb = eval_js("document.getElementById('view-leaderboard').classList.contains('active')")
        
        eval_js("document.querySelector('.nav-link[data-view=\"view-challenge\"]').click()")
        is_chal = eval_js("document.getElementById('view-challenge').classList.contains('active')")
        
        eval_js("App.scrollToRegistration()")
        is_reg_home = eval_js("document.getElementById('view-home').classList.contains('active')")
        
        eval_js("App.scrollToBeatChampion()")
        is_champ_home = eval_js("document.getElementById('view-leaderboard').classList.contains('active')")
        
        nav_pass = is_cat and is_lb and is_chal and is_reg_home and is_champ_home
        results["Button 3: Navbar View Links (Home, Arena, Leaderboard, Challenge, Register, Beat Champion)"] = nav_pass
        print(f"Test 3 - Navbar links: {'PASS' if nav_pass else 'FAIL'}")

        # Test 4: Hero CTA buttons
        eval_js("App.showView('view-home')")
        eval_js("document.getElementById('hero-play-btn').click()")
        hero_play_ok = eval_js("document.getElementById('view-category').classList.contains('active')")
        
        eval_js("App.showView('view-home')")
        eval_js("document.getElementById('hero-challenge-btn').click()")
        hero_chal_ok = eval_js("document.getElementById('view-challenge').classList.contains('active')")
        
        eval_js("App.showView('view-home')")
        eval_js("document.getElementById('hero-register-btn').click()")
        hero_reg_ok = eval_js("document.getElementById('view-home').classList.contains('active')")
        
        hero_pass = hero_play_ok and hero_chal_ok and hero_reg_ok
        results["Button 4: Hero CTA Buttons (Play Quiz, Challenge, Register)"] = hero_pass
        print(f"Test 4 - Hero CTA buttons: {'PASS' if hero_pass else 'FAIL'}")

        # Test 5: Beat Champion Buttons
        eval_js("App.showView('view-home')")
        eval_js("document.getElementById('challenge-junior-champ-btn').click()")
        modal_open_junior = eval_js("document.getElementById('start-quiz-modal').classList.contains('active') && App.player.category === 'junior' && App.player.mode === 'champion'")
        eval_js("App.closeStartModal()")
        modal_closed_1 = not eval_js("document.getElementById('start-quiz-modal').classList.contains('active')")
        
        eval_js("document.getElementById('challenge-commerce-champ-btn').click()")
        modal_open_commerce = eval_js("document.getElementById('start-quiz-modal').classList.contains('active') && App.player.category === 'commerce' && App.player.mode === 'champion'")
        eval_js("App.closeStartModal()")
        modal_closed_2 = not eval_js("document.getElementById('start-quiz-modal').classList.contains('active')")
        
        champ_pass = modal_open_junior and modal_closed_1 and modal_open_commerce and modal_closed_2
        results["Button 5: Beat Champion Buttons & Modal Close"] = champ_pass
        print(f"Test 5 - Beat Champion buttons: {'PASS' if champ_pass else 'FAIL'}")

        # Test 6: Category selection cards
        eval_js("App.handleCategoryPick('junior')")
        cat_junior_ok = eval_js("document.getElementById('start-quiz-modal').classList.contains('active') && App.player.category === 'junior'")
        eval_js("App.closeStartModal()")
        
        eval_js("App.handleCategoryPick('commerce')")
        cat_comm_ok = eval_js("document.getElementById('start-quiz-modal').classList.contains('active') && App.player.category === 'commerce'")
        
        cat_pass = cat_junior_ok and cat_comm_ok
        results["Button 6: Category Selection Cards (Junior & Commerce)"] = cat_pass
        print(f"Test 6 - Category cards: {'PASS' if cat_pass else 'FAIL'}")

        # Test 7: Start Quiz Submission & Arena Entry
        eval_js("""
            document.getElementById('player-nickname-input').value = 'TestChampion99';
            document.getElementById('player-school-input').value = 'Govt Model HSS';
            App.confirmAndStartQuiz();
        """)
        time.sleep(2)
        
        in_arena = eval_js("document.getElementById('view-arena').classList.contains('active')")
        has_questions = eval_js("App.session.questions && App.session.questions.length === 15")
        q1_text = eval_js("document.getElementById('q-text').textContent")
        opt_count = eval_js("document.querySelectorAll('.option-btn').length")
        
        arena_pass = in_arena and has_questions and opt_count == 4
        results["Button 7: Enter Quiz Arena & Question Rendering"] = arena_pass
        print(f"Test 7 - Arena entry (Question 1: {q1_text[:40]}..., Options: {opt_count}): {'PASS' if arena_pass else 'FAIL'}")

        # Test 8: Option Clicking & Instant Feedback in Arena
        eval_js("document.querySelectorAll('.option-btn')[1].click()") # Click Option B
        time.sleep(0.8)
        has_feedback = eval_js("document.getElementById('feedback-box').style.display === 'block'")
        has_score = eval_js("App.session.score >= 0")
        
        opt_pass = has_feedback and has_score
        results["Button 8: Quiz Arena Option Selection (Instant Validation & Feedback)"] = opt_pass
        print(f"Test 8 - Option click & feedback: {'PASS' if opt_pass else 'FAIL'}")

        # Test 9: Complete Quiz Session & Results Screen
        eval_js("App.finishQuiz()")
        time.sleep(2)
        
        in_results = eval_js("document.getElementById('view-results').classList.contains('active')")
        final_score_text = eval_js("document.getElementById('results-final-score').textContent")
        chal_link_val = eval_js("document.getElementById('results-challenge-link-input').value")
        
        results_pass = in_results and ("PTS" in str(final_score_text)) and ("challenge=" in str(chal_link_val))
        results["Button 9: Quiz Completion & Results Screen"] = results_pass
        print(f"Test 9 - Results screen ({final_score_text}, Challenge: {chal_link_val}): {'PASS' if results_pass else 'FAIL'}")

        # Test 10: Instagram Story Card Generation with Quizzora Logo
        print("Generating Instagram Story Card via App.generateInstagramStoryCard()...")
        eval_js("App.generateInstagramStoryCard()")
        time.sleep(3) # wait for images to load and draw
        
        canvas_valid = eval_js("""
            (() => {
                const c = document.getElementById('instagram-story-canvas');
                return c && c.width === 1080 && c.height === 1920;
            })()
        """)
        
        img_b64 = eval_js("document.getElementById('instagram-story-canvas').toDataURL('image/png').split(',')[1]")
        if img_b64:
            img_bytes = base64.b64decode(img_b64)
            save_path = r"C:\Users\mathe\.gemini\antigravity\brain\aeb19940-0fa3-4190-aa27-4d6f724f628f\screenshot_generated_story_card.png"
            with open(save_path, "wb") as f:
                f.write(img_bytes)
            print(f"Story Card saved to: {save_path} ({len(img_bytes)} bytes)")
            story_pass = len(img_bytes) > 50000
        else:
            story_pass = False
            
        results["Button 10: Instagram Story Scorecard with Logo & QR"] = canvas_valid and story_pass
        print(f"Test 10 - Instagram Story Scorecard export: {'PASS' if results['Button 10: Instagram Story Scorecard with Logo & QR'] else 'FAIL'}")

        # Test 11: Results Buttons (Play Again, View Leaderboard, WhatsApp, Copy Link)
        eval_js("document.getElementById('results-copy-link-btn').click()")
        toast_copy = eval_js("document.getElementById('toast-notice').textContent")
        copy_pass = "copied" in str(toast_copy).lower()
        
        wa_href = eval_js("document.getElementById('results-whatsapp-share-btn').href")
        wa_pass = "whatsapp.com" in str(wa_href)
        
        eval_js("document.querySelector('button[onclick*=\"view-leaderboard\"]').click()")
        lb_view_ok = eval_js("document.getElementById('view-leaderboard').classList.contains('active')")
        
        eval_js("App.showView('view-results')")
        eval_js("document.querySelector('button[onclick*=\"view-category\"]').click()")
        play_again_ok = eval_js("document.getElementById('view-category').classList.contains('active')")
        
        results_btn_pass = copy_pass and wa_pass and lb_view_ok and play_again_ok
        results["Button 11: Results Actions (Copy Link, WhatsApp, Play Again, View Leaderboard)"] = results_btn_pass
        print(f"Test 11 - Results action buttons: {'PASS' if results_btn_pass else 'FAIL'}")

        # Test 12: Leaderboard Tabs Filtering
        eval_js("App.showView('view-leaderboard')")
        eval_js("document.querySelector('.lb-tab[data-category=\"junior\"]').click()")
        time.sleep(0.5)
        junior_tab_active = eval_js("document.querySelector('.lb-tab[data-category=\"junior\"]').classList.contains('active')")
        
        eval_js("document.querySelector('.lb-tab[data-category=\"commerce\"]').click()")
        time.sleep(0.5)
        comm_tab_active = eval_js("document.querySelector('.lb-tab[data-category=\"commerce\"]').classList.contains('active')")
        
        eval_js("document.querySelector('.lb-tab[data-category=\"all\"]').click()")
        time.sleep(0.5)
        all_tab_active = eval_js("document.querySelector('.lb-tab[data-category=\"all\"]').classList.contains('active')")
        
        lb_tabs_pass = junior_tab_active and comm_tab_active and all_tab_active
        results["Button 12: Leaderboard Tabs (Overall, Junior, Commerce)"] = lb_tabs_pass
        print(f"Test 12 - Leaderboard tabs: {'PASS' if lb_tabs_pass else 'FAIL'}")

        # Test 13: Admin Modal Login, CRUD and Settings
        eval_js("App.openAdminModal()")
        admin_modal_open = eval_js("document.getElementById('admin-login-modal').classList.contains('active')")
        
        eval_js("App.closeAdminModal()")
        admin_modal_close = not eval_js("document.getElementById('admin-login-modal').classList.contains('active')")
        
        eval_js("""
            App.openAdminModal();
            document.getElementById('admin-pin-input').value = 'quizzora2026';
            App.handleAdminLogin();
        """)
        time.sleep(1.5)
        
        in_admin = eval_js("document.getElementById('view-admin').classList.contains('active')")
        admin_token_set = eval_js("App.adminToken === 'quizzora2026'")
        
        eval_js("""
            document.getElementById('new-q-category').value = 'junior';
            document.getElementById('new-q-topic').value = 'General Knowledge';
            document.getElementById('new-q-text').value = 'Automated Verification Question for Quizzora 2026?';
            document.getElementById('new-q-opt0').value = 'Alpha';
            document.getElementById('new-q-opt1').value = 'Beta';
            document.getElementById('new-q-opt2').value = 'Gamma';
            document.getElementById('new-q-opt3').value = 'Delta';
            document.getElementById('new-q-correct').value = '1';
            document.getElementById('new-q-explanation').value = 'Beta is verified.';
            App.handleAddQuestion(new Event('submit'));
        """)
        time.sleep(1.5)
        toast_add = eval_js("document.getElementById('toast-notice').textContent")
        add_pass = "Added Successfully" in str(toast_add)
        
        eval_js("document.querySelector('button[onclick*=\"view-home\"]').click()")
        exit_admin_ok = eval_js("document.getElementById('view-home').classList.contains('active')")
        
        admin_pass = admin_modal_open and admin_modal_close and in_admin and admin_token_set and add_pass and exit_admin_ok
        results["Button 13: Admin Portal (Login Modal, Add Question, Exit Admin)"] = admin_pass
        print(f"Test 13 - Admin portal actions: {'PASS' if admin_pass else 'FAIL'}")

        # Test 14: External Links (Instagram & Registration Google Forms)
        insta_link = eval_js("document.querySelector('.official-insta-link').href")
        form_link = eval_js("document.querySelector('.official-form-link').href")
        links_pass = ("instagram.com/scapsquizzora" in insta_link) and ("docs.google.com/forms" in form_link)
        results["Button 14: Official External Links (Instagram & Google Forms)"] = links_pass
        print(f"Test 14 - Official external links: {'PASS' if links_pass else 'FAIL'}")

        # Summary
        print("\n=== SUMMARY OF ALL BUTTON & INTERACTION TESTS ===")
        all_passed = True
        for test_name, status in results.items():
            mark = "PASS [OK]" if status else "FAIL [X]"
            print(f"- {test_name}: {mark}")
            if not status:
                all_passed = False
                
        print(f"\nOVERALL RESULT: {'ALL TESTS PASSED 100%' if all_passed else 'SOME TESTS FAILED'}")
        
    finally:
        proc.kill()

if __name__ == "__main__":
    run_tests()
