import subprocess
import json
import sys
from flask import Flask, render_template_string, jsonify, request

# ★ 翻訳ライブラリ
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("エラー: 'deep-translator' がインストールされていません。")
    sys.exit(1)

app = Flask(__name__)

# ========================================================
# フロントエンド (HTML/CSS/JS)
# ========================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Subtube</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", sans-serif; background: #000; color: #fff; margin: 0; overflow: hidden; width: 100vw; height: 100vh; -webkit-tap-highlight-color: transparent; }
        #app-root { width: 100%; height: 100%; display: flex; flex-direction: column; transition: transform 0.3s ease; position: relative; }
        #touch-strip { display: none; position: fixed; z-index: 9999; background: transparent; }
        .landscape-style #touch-strip { display: block; top: 0; left: 20%; width: 60%; height: 30%; }
        #header { flex: 0 0 auto; padding: 10px; padding-top: max(10px, env(safe-area-inset-top)); background: #222; border-bottom: 1px solid #333; display: flex; gap: 8px; z-index: 50; }
        #videoIdInput { flex-grow: 1; padding: 10px; border-radius: 6px; border: none; font-size: 16px; background: #fff; color: #000; }
        
        /* ★ボタン：水色に戻しました */
        button { padding: 8px 15px; border-radius: 6px; border: none; background: #4facfe; color: white; font-weight: bold; cursor: pointer; }
        
        #video-container { flex: 0 0 auto; width: 100%; background: #000; position: relative; z-index: 10; }
        .video-wrapper { position: relative; padding-bottom: 56.25%; height: 0; width: 100%; }
        #player { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        
        /* メニュー封じ */
        #subtitle-area { 
            flex: 1; overflow-y: scroll; background: #111; padding: 15px; padding-bottom: 100px; 
            -webkit-overflow-scrolling: touch; z-index: 20; position: relative; 
            user-select: text; -webkit-user-select: text;
            -webkit-touch-callout: none;
        }
        
        /* ★辞書枠：水色に戻しました */
        #definition-box { position: absolute; bottom: 0; left: 0; width: 100%; height: 0; background: rgba(20, 20, 20, 0.98); backdrop-filter: blur(15px); border-top: 2px solid #4facfe; border-radius: 20px 20px 0 0; box-sizing: border-box; overflow-y: auto; z-index: 999; transition: height 0.25s cubic-bezier(0.16, 1, 0.3, 1); pointer-events: auto !important; user-select: text; -webkit-user-select: text; }
        
        #definition-box.open { height: 60vh; padding: 20px; padding-bottom: 120px; }
        .line { margin-bottom: 12px; line-height: 1.6; padding: 4px 8px; font-size: 16px; border-bottom: 1px solid #222; display: flex; flex-wrap: wrap; align-items: center; }
        
        /* ★アクティブ行：水色に戻しました */
        .line.active { background: #222; border-left: 3px solid #4facfe; }
        
        /* ★再生ボタン：ここだけ「白」のまま（選択不可） */
        .time-btn { 
            display: inline-block; 
            color: #fff; /* 水色じゃなく白 */
            font-size: 1.2em; 
            cursor: pointer; 
            padding: 5px 10px 5px 0; 
            margin-right: 5px; 
            opacity: 0.7;
            user-select: none; 
            -webkit-user-select: none; 
        }
        
        /* ★単語ホバー：水色に戻しました */
        .word { cursor: pointer; display: inline-block; padding: 2px 1px; margin-right: 4px; border-radius: 4px; }
        @media (hover: hover) { .word:hover { color: #4facfe; } }
        
        .close-btn { position: absolute; top: 15px; right: 15px; background: #333; color: #fff; border: none; width: 44px; height: 44px; border-radius: 50%; font-size: 24px; cursor: pointer; z-index: 1000; }
        .dict-word { font-size: 1.8em; font-weight: bold; color: #fff; margin-bottom: 5px; }
        .dict-def { font-size: 1.2em; color: #ddd; line-height: 1.6; margin-top: 15px; }
        
        /* ★翻訳ボタン：赤に戻しました（アクセント） */
        .trans-btn { background: #ff6b6b; color: white; border: none; padding: 12px 20px; margin-top: 20px; border-radius: 30px; font-size: 16px; font-weight: bold; width: 100%; }
        
        /* ★翻訳結果：シアン（水色）に戻しました */
        .full-trans-result { font-size: 1.4em; color: #81ecec; font-weight: bold; line-height: 1.5; padding: 10px; }
        .original-text { font-size: 1em; color: #aaa; margin-bottom: 10px; padding: 0 10px; font-style: italic;}
        .jp-meaning { margin-top: 20px; padding-top: 15px; border-top: 1px dashed #555; color: #81ecec; font-weight: bold; font-size: 1.4em; }
        
        #toast { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.8); color: #fff; padding: 15px 30px; border-radius: 30px; font-weight: bold; font-size: 1.2em; pointer-events: none; opacity: 0; transition: opacity 0.3s; z-index: 2000; }
        
        .landscape-style #header { display: none; } 
        .landscape-style { flex-direction: row !important; }
        .landscape-style #video-container { position: fixed; top: 0; left: 0; width: 100% !important; height: 100% !important; z-index: 1; border: none; background: #000; }
        .landscape-style .video-wrapper { height: 100%; padding-bottom: 0; }
        .landscape-style #subtitle-area { position: fixed; bottom: 0; left: 0; width: 100%; height: 120px; z-index: 2; background: transparent; pointer-events: auto; padding: 0 15px; scrollbar-width: none; mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%); -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%); }
        .landscape-style #subtitle-area::-webkit-scrollbar { display: none; }
        .landscape-style .line { display: block; opacity: 1; border-bottom: none; padding: 5px 0; color: #fff; text-shadow: 2px 2px 3px #000, -1px -1px 3px #000; font-size: 17px; font-weight: 600; min-height: 40px; display: flex; align-items: center; white-space: nowrap; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; }
        .landscape-style .line::-webkit-scrollbar { display: none; }
        .landscape-style .line.active { background: transparent !important; border-left: none !important; opacity: 1; }
        .force-rotate #definition-box.open { height: 60%; }
        @media (orientation: landscape) { #definition-box.open { height: 70vh; } }
        body.subs-hidden #subtitle-area { opacity: 0; pointer-events: none; }
        body.force-rotate #app-root { width: 100vh; height: 100vw; transform: rotate(90deg); transform-origin: top left; position: fixed; top: 0; left: 100vw; }
        @media (orientation: landscape) { body.force-rotate #app-root { transform: none; width: 100%; height: 100%; left: 0; position: static; } }
    </style>
</head>
<body>
    <div id="app-root">
        <div id="touch-strip"></div>
        <div id="header">
            <input type="text" id="videoIdInput" placeholder="動画URL">
            <button onclick="loadVideo()">Load</button>
        </div>
        <div id="video-container"><div class="video-wrapper"><div id="player"></div></div></div>
        <div id="subtitle-area">
            <div id="subtitles">
                <div style="color:#666; text-align:center; margin-top:50px; font-size:0.9em;">
                    <b>操作ガイド</b><br><br>
                    <b>【基本操作】</b><br>
                    単語タップ ➜ 辞書検索<br>
                    <b>文字を長押しして選択 ➜ 範囲翻訳</b><br><br>
                    <b>【縦画面】</b><br>
                    どこでも3回タップ ➜ 寝ながらモード<br><br>
                    <b>【寝ながらモード】</b><br>
                    画面上部を操作<br>
                    3回タップ ➜ 元に戻る<br>
                    2回タップ ➜ 字幕 ON/OFF
                </div>
            </div>
        </div>
        <div id="definition-box"><button class="close-btn" onclick="closeDictionary()">×</button><div id="def-content"></div></div>
    </div>
    <div id="toast">Message</div>
    <script>
        var player;
        var transcript = [];
        var tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        function onYouTubeIframeAPIReady() {}

        let tapCount = 0;
        let tapTimer = null;
        document.addEventListener('selectionchange', () => {});
        document.getElementById('subtitle-area').addEventListener('touchend', checkSelection);
        document.getElementById('subtitle-area').addEventListener('mouseup', checkSelection);

        function checkSelection() {
            setTimeout(() => {
                const selection = window.getSelection();
                let rawText = selection.toString();
                // データの整形
                rawText = rawText.replace(/▶/g, '');
                rawText = rawText.replace(/\\r?\\n/g, ' ');
                const selectedText = rawText.replace(/\\s+/g, ' ').trim();

                if (selectedText.length > 0) { 
                    selection.removeAllRanges();
                    translateLine(selectedText); 
                }
            }, 100);
        }

        document.body.addEventListener('click', (e) => {
            if (e.target.closest('.word')) {
                const selection = window.getSelection();
                if (selection.toString().length === 0) {
                    const wordText = e.target.closest('.word').dataset.word;
                    lookupEnglish(wordText);
                }
                return;
            }
            const dictBox = document.getElementById('definition-box');
            if (dictBox.classList.contains('open')) {
                if (e.target.closest('#definition-box')) return;
                window.getSelection().removeAllRanges();
                closeDictionary();
                return; 
            }
            if (e.target.closest('input, button, .close-btn')) return;
            const appRoot = document.getElementById('app-root');
            const isLandscape = appRoot.classList.contains('landscape-style');
            const isTouchStrip = e.target.id === 'touch-strip';
            if (isLandscape && !isTouchStrip) return;
            tapCount++; clearTimeout(tapTimer);
            if (tapCount === 3) { toggleForceRotate(); tapCount = 0; } 
            else { tapTimer = setTimeout(() => { if (tapCount === 2 && isLandscape) { toggleSubtitles(); } tapCount = 0; }, 350); }
        });

        function toggleForceRotate() { document.body.classList.toggle('force-rotate'); updateLayout(); showToast(document.body.classList.contains('force-rotate') ? "寝ながらモード ON" : "寝ながらモード OFF"); }
        function toggleSubtitles() { document.body.classList.toggle('subs-hidden'); showToast(document.body.classList.contains('subs-hidden') ? "字幕 OFF" : "字幕 ON"); }
        function showToast(msg) { const t = document.getElementById('toast'); t.innerText = msg; t.style.opacity = '1'; setTimeout(() => { t.style.opacity = '0'; }, 1500); }
        function updateLayout() {
            const isPhysicalLandscape = window.innerWidth > window.innerHeight;
            const isForceRotate = document.body.classList.contains('force-rotate');
            const appRoot = document.getElementById('app-root');
            if (isPhysicalLandscape || isForceRotate) { appRoot.classList.add('landscape-style'); } else { appRoot.classList.remove('landscape-style'); }
        }
        window.addEventListener('resize', updateLayout); updateLayout();

        async function loadVideo() {
            var rawInput = document.getElementById('videoIdInput').value;
            var videoId = rawInput; 
            const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=|live\/)([^#&?]*).*/;
            const match = rawInput.match(regExp);
            if (match && match[2].length === 11) { videoId = match[2]; }
            if (!videoId) { alert("URLを入れてください"); return; }
            if (player) { player.loadVideoById(videoId); } 
            else { player = new YT.Player('player', { width: '100%', height: '100%', videoId: videoId }); }

            const subContainer = document.getElementById('subtitles');
            subContainer.innerHTML = '<p style="text-align:center; padding:20px;">Loading...</p>';
            try {
                const response = await fetch(`/api/transcript/${videoId}`);
                const data = await response.json();
                if (data.error) { subContainer.innerHTML = `<p style="color:#ff6b6b; text-align:center;">${data.error}</p>`; return; }
                transcript = data;
                renderSubtitles();
                startSync();
            } catch (e) { subContainer.innerText = "Error: " + e; }
        }

        function renderSubtitles() {
            const container = document.getElementById('subtitles');
            container.innerHTML = '';
            transcript.forEach((line, index) => {
                const div = document.createElement('div');
                div.className = 'line';
                div.id = `line-${index}`;
                
                // 再生ボタン
                const timeSpan = document.createElement('span');
                timeSpan.className = 'time-btn';
                timeSpan.innerText = "▶";
                timeSpan.onclick = () => { player.seekTo(line.start); };
                div.appendChild(timeSpan);
                
                const lineContent = line.text || line.content || "";
                const words = lineContent.split(' ');
                words.forEach(word => {
                    const span = document.createElement('span');
                    span.className = 'word';
                    span.innerText = word;
                    span.dataset.word = word.replace(/[^a-zA-Z0-9'-]/g, ""); 
                    div.appendChild(span);
                    div.appendChild(document.createTextNode(' '));
                });
                container.appendChild(div);
            });
        }

        async function translateLine(text) {
            const defContent = document.getElementById('def-content');
            document.getElementById('definition-box').classList.add('open');
            if (player && typeof player.pauseVideo === 'function') player.pauseVideo();
            defContent.innerHTML = `<div style="padding:10px;">Translating selection...</div>`;
            try {
                const res = await fetch('/api/translate_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                const data = await res.json();
                if (data.error) { defContent.innerText = "Error: " + data.error; } 
                else { defContent.innerHTML = `<div class="original-text">"${text}"</div><div class="full-trans-result">${data.translation}</div>`; }
            } catch (e) { defContent.innerText = "Error: " + e; }
        }

        async function lookupEnglish(word) {
            if (!word) return;
            const defContent = document.getElementById('def-content');
            document.getElementById('definition-box').classList.add('open');
            if (player && typeof player.pauseVideo === 'function') { player.pauseVideo(); }
            defContent.innerHTML = `<div style="padding:10px;">Searching <b>${word}</b>...</div>`;
            try {
                const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`);
                const data = await res.json();
                let htmlContent = "";
                if (data.title === "No Definitions Found") { htmlContent = `<div class="dict-word">${word}</div><div style="color:#888;">No definition found.</div>`; } 
                else {
                    const def = data[0].meanings[0].definitions[0].definition;
                    const phonetic = data[0].phonetic || "";
                    htmlContent = `<div class="dict-word">${word}<span class="dict-phonetic">${phonetic}</span></div><div class="dict-def">${def}</div>`;
                }
                htmlContent += `<div><button class="trans-btn" onclick="lookupJapanese('${word}')">🇯🇵 単語を翻訳</button></div><div id="jp-result"></div>`;
                defContent.innerHTML = htmlContent;
            } catch (e) { defContent.innerText = "Error"; }
        }

        async function lookupJapanese(word) {
            const jpBox = document.getElementById('jp-result');
            jpBox.innerHTML = `<div class="jp-meaning" style="color:#aaa;">翻訳中...</div>`;
            try {
                const res = await fetch(`/api/translate/${word}`);
                const data = await res.json();
                if (data.error) { jpBox.innerText = "Error"; } 
                else { jpBox.innerHTML = `<div class="jp-meaning">${data.meaning}</div>`; }
            } catch (e) { jpBox.innerText = "Error"; }
        }

        function closeDictionary() {
            document.getElementById('definition-box').classList.remove('open');
            window.getSelection().removeAllRanges();
            if (player && typeof player.playVideo === 'function') { player.playVideo(); }
        }

        let isUserScrolling = false; let scrollTimeout = null; let isAutoScrolling = false;
        const subArea = document.getElementById('subtitle-area');
        subArea.addEventListener('scroll', () => {
            if (!isAutoScrolling) { isUserScrolling = true; clearTimeout(scrollTimeout); scrollTimeout = setTimeout(() => { isUserScrolling = false; }, 3000); }
        });

        function startSync() {
            setInterval(() => {
                if (!player || !player.getCurrentTime) return;
                const time = player.getCurrentTime();
                let activeIndex = -1;
                for (let i = 0; i < transcript.length; i++) {
                    if (time >= transcript[i].start && time < transcript[i].start + transcript[i].duration) { activeIndex = i; break; }
                }
                if (activeIndex !== -1) {
                    const activeDiv = document.getElementById(`line-${activeIndex}`);
                    if (activeDiv && !activeDiv.classList.contains('active')) {
                        document.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
                        activeDiv.classList.add('active');
                        if (!isUserScrolling) {
                            isAutoScrolling = true;
                            const container = document.getElementById('subtitle-area');
                            container.scrollTo({ top: activeDiv.offsetTop - 15, behavior: "smooth" });
                            setTimeout(() => { isAutoScrolling = false; }, 500);
                        }
                    }
                }
            }, 500);
        }
    </script>
</body>
</html>
"""

# ========================================================
# バックエンド
# ========================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/translate/<word>')
def translate_word(word):
    try:
        translator = GoogleTranslator(source='auto', target='ja')
        translated_text = translator.translate(word)
        return jsonify({"word": word, "meaning": translated_text})
    except Exception as e:
        return jsonify({"error": "Error"})

@app.route('/api/translate_text', methods=['POST'])
def translate_sentence():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'})
        translated = GoogleTranslator(source='auto', target='ja').translate(text)
        return jsonify({'translation': translated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcript/<video_id>')
def get_transcript(video_id):
    try:
        cmd = ["youtube_transcript_api", video_id, "--format", "json", "--languages", "ja", "en"]
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if not result:
            return jsonify({"error": "字幕データが空でした"})
        raw_data = json.loads(result)
        transcript = raw_data[0] if (isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], list)) else raw_data
        return jsonify(transcript)
    except subprocess.CalledProcessError as e:
        error_msg = e.output.decode()
        return jsonify({"error": "字幕取得エラー: " + error_msg})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # ポートを環境変数から取るように変更（Render対策）
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
