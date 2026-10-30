import subprocess
import time
import json
import urllib.request
import websocket

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

proc = subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    'about:blank'
])
time.sleep(1.5)

try:
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    ws = websocket.create_connection(tabs[0]['webSocketDebuggerUrl'])

    payload = {
        'id': 1,
        'method': 'Runtime.evaluate',
        'params': {
            'expression': f"try {{ new Function({json.dumps(js_code)}); 'VALID SYNTAX' }} catch(e) {{ e.message + ' at line ' + e.lineNumber }}",
            'returnByValue': True
        }
    }
    ws.send(json.dumps(payload))
    res = json.loads(ws.recv())
    print("Syntax Check Result:", res.get('result', {}).get('result', {}).get('value'))
finally:
    proc.kill()
