let player;
let transcript = [];
let syncTimer;

const MAX_SUBTITLE_FILE_SIZE = 5 * 1024 * 1024;
const translationEnabled =
    document.body.dataset.translationEnabled === "true";

const youtubeApiScript = document.createElement("script");
youtubeApiScript.src = "https://www.youtube.com/iframe_api";
const firstScriptTag = document.getElementsByTagName("script")[0];
firstScriptTag.parentNode.insertBefore(youtubeApiScript, firstScriptTag);

function onYouTubeIframeAPIReady() {}

let tapCount = 0;
let tapTimer = null;

document.addEventListener("selectionchange", () => {});
document.getElementById("loadButton").addEventListener("click", loadVideo);
document
    .getElementById("closeDictionaryButton")
    .addEventListener("click", closeDictionary);
document
    .getElementById("subtitle-area")
    .addEventListener("touchend", checkSelection);
document
    .getElementById("subtitle-area")
    .addEventListener("mouseup", checkSelection);

function checkSelection() {
    setTimeout(() => {
        const selection = window.getSelection();
        let rawText = selection.toString();
        rawText = rawText.replace(/▶/g, "");
        rawText = rawText.replace(/\r?\n/g, " ");
        const selectedText = rawText.replace(/\s+/g, " ").trim();

        if (selectedText.length > 0) {
            selection.removeAllRanges();
            translateLine(selectedText);
        }
    }, 100);
}

document.body.addEventListener("click", (event) => {
    if (event.target.closest(".word")) {
        const selection = window.getSelection();
        if (selection.toString().length === 0) {
            const wordText = event.target.closest(".word").dataset.word;
            lookupEnglish(wordText);
        }
        return;
    }

    const dictionaryBox = document.getElementById("definition-box");
    if (dictionaryBox.classList.contains("open")) {
        if (event.target.closest("#definition-box")) return;
        window.getSelection().removeAllRanges();
        closeDictionary();
        return;
    }

    if (event.target.closest("input, button, .close-btn")) return;

    const appRoot = document.getElementById("app-root");
    const isLandscape = appRoot.classList.contains("landscape-style");
    const isTouchStrip = event.target.id === "touch-strip";
    if (isLandscape && !isTouchStrip) return;

    tapCount += 1;
    clearTimeout(tapTimer);
    if (tapCount === 3) {
        toggleForceRotate();
        tapCount = 0;
    } else {
        tapTimer = setTimeout(() => {
            if (tapCount === 2 && isLandscape) toggleSubtitles();
            tapCount = 0;
        }, 350);
    }
});

function toggleForceRotate() {
    document.body.classList.toggle("force-rotate");
    updateLayout();
    showToast(
        document.body.classList.contains("force-rotate")
            ? "寝ながらモード ON"
            : "寝ながらモード OFF",
    );
}

function toggleSubtitles() {
    document.body.classList.toggle("subs-hidden");
    showToast(
        document.body.classList.contains("subs-hidden")
            ? "字幕 OFF"
            : "字幕 ON",
    );
}

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.style.opacity = "1";
    setTimeout(() => {
        toast.style.opacity = "0";
    }, 1500);
}

function updateLayout() {
    const isPhysicalLandscape = window.innerWidth > window.innerHeight;
    const isForceRotate = document.body.classList.contains("force-rotate");
    const appRoot = document.getElementById("app-root");
    if (isPhysicalLandscape || isForceRotate) {
        appRoot.classList.add("landscape-style");
    } else {
        appRoot.classList.remove("landscape-style");
    }
}

window.addEventListener("resize", updateLayout);
updateLayout();

async function loadVideo() {
    const rawInput = document.getElementById("videoIdInput").value;
    const videoId = SubtubeSubtitles.extractYouTubeVideoId(rawInput);
    if (!videoId) {
        showSubtitleMessage("有効なYouTube動画URLを入力してください。", true);
        return;
    }

    const subtitleFile = document.getElementById("subtitleFileInput").files[0];
    if (!subtitleFile) {
        showSubtitleMessage("字幕ファイルを選択してください。", true);
        return;
    }
    if (subtitleFile.size > MAX_SUBTITLE_FILE_SIZE) {
        showSubtitleMessage("字幕ファイルは5MB以下にしてください。", true);
        return;
    }

    showSubtitleMessage("字幕ファイルを読み込んでいます…");
    try {
        const source = await subtitleFile.text();
        transcript = SubtubeSubtitles.parseSubtitleFile(subtitleFile.name, source);

        if (!window.YT || typeof YT.Player !== "function") {
            showSubtitleMessage(
                "YouTubeプレーヤーを準備中です。数秒後にもう一度押してください。",
                true,
            );
            return;
        }

        if (player) {
            player.loadVideoById(videoId);
        } else {
            player = new YT.Player("player", {
                width: "100%",
                height: "100%",
                videoId,
            });
        }

        renderSubtitles();
        startSync();
    } catch (error) {
        showSubtitleMessage(error.message || "字幕ファイルを読み込めませんでした。", true);
    }
}

function showSubtitleMessage(message, isError = false) {
    const subtitleContainer = document.getElementById("subtitles");
    const messageElement = document.createElement("p");
    messageElement.className = isError
        ? "subtitle-message subtitle-message-error"
        : "subtitle-message";
    messageElement.textContent = message;
    subtitleContainer.replaceChildren(messageElement);
}

function renderSubtitles() {
    const container = document.getElementById("subtitles");
    container.replaceChildren();
    transcript.forEach((line, index) => {
        const lineElement = document.createElement("div");
        lineElement.className = "line";
        lineElement.id = `line-${index}`;

        const timeButton = document.createElement("span");
        timeButton.className = "time-btn";
        timeButton.innerText = "▶";
        timeButton.onclick = () => player.seekTo(line.start);
        lineElement.appendChild(timeButton);

        const lineContent = line.text || line.content || "";
        lineContent.split(" ").forEach((word) => {
            const wordElement = document.createElement("span");
            wordElement.className = "word";
            wordElement.innerText = word;
            wordElement.dataset.word = word.replace(/[^a-zA-Z0-9'-]/g, "");
            lineElement.appendChild(wordElement);
            lineElement.appendChild(document.createTextNode(" "));
        });
        container.appendChild(lineElement);
    });
}

async function translateLine(text) {
    const definitionContent = document.getElementById("def-content");
    document.getElementById("definition-box").classList.add("open");
    if (player && typeof player.pauseVideo === "function") player.pauseVideo();

    if (!translationEnabled) {
        setDefinitionMessage(
            "翻訳機能は無効です。DEEPL_API_KEYを設定すると利用できます。",
        );
        return;
    }

    setDefinitionMessage("選択範囲を翻訳しています…");

    try {
        const response = await fetch("/api/translate_text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || "翻訳に失敗しました。");
        }

        const originalText = document.createElement("div");
        originalText.className = "original-text";
        originalText.textContent = `"${text}"`;

        const translatedText = document.createElement("div");
        translatedText.className = "full-trans-result";
        translatedText.textContent = data.translation;
        definitionContent.replaceChildren(originalText, translatedText);
    } catch (error) {
        setDefinitionMessage(error.message || "翻訳に失敗しました。", true);
    }
}

async function lookupEnglish(word) {
    if (!word) return;

    const definitionContent = document.getElementById("def-content");
    document.getElementById("definition-box").classList.add("open");
    if (player && typeof player.pauseVideo === "function") player.pauseVideo();
    setDefinitionMessage(`${word} を検索しています…`);

    try {
        const response = await fetch(
            `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`,
        );
        const data = await response.json();
        if (!response.ok && data.title !== "No Definitions Found") {
            throw new Error("辞書検索に失敗しました。");
        }

        const wordElement = document.createElement("div");
        wordElement.className = "dict-word";
        wordElement.textContent = word;

        const definitionElement = document.createElement("div");
        definitionElement.className = "dict-def";
        if (data.title === "No Definitions Found") {
            definitionElement.textContent = "No definition found.";
        } else {
            const definition = data[0].meanings[0].definitions[0].definition;
            const phonetic = data[0].phonetic || "";
            if (phonetic) {
                const phoneticElement = document.createElement("span");
                phoneticElement.className = "dict-phonetic";
                phoneticElement.textContent = ` ${phonetic}`;
                wordElement.appendChild(phoneticElement);
            }
            definitionElement.textContent = definition;
        }

        const resultElement = document.createElement("div");
        resultElement.id = "jp-result";
        const elements = [wordElement, definitionElement];
        if (translationEnabled) {
            const buttonWrapper = document.createElement("div");
            const translationButton = document.createElement("button");
            translationButton.className = "trans-btn";
            translationButton.type = "button";
            translationButton.textContent = "🇯🇵 単語を翻訳";
            translationButton.addEventListener("click", () => lookupJapanese(word));
            buttonWrapper.appendChild(translationButton);
            elements.push(buttonWrapper, resultElement);
        }
        definitionContent.replaceChildren(...elements);
    } catch (error) {
        setDefinitionMessage(error.message || "辞書検索に失敗しました。", true);
    }
}

async function lookupJapanese(word) {
    const japaneseResult = document.getElementById("jp-result");
    const status = document.createElement("div");
    status.className = "jp-meaning jp-meaning-pending";
    status.textContent = "翻訳しています…";
    japaneseResult.replaceChildren(status);

    try {
        const response = await fetch("/api/translate_text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: word }),
        });
        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || "翻訳に失敗しました。");
        }

        const translatedWord = document.createElement("div");
        translatedWord.className = "jp-meaning";
        translatedWord.textContent = data.translation;
        japaneseResult.replaceChildren(translatedWord);
    } catch (error) {
        const errorElement = document.createElement("div");
        errorElement.className = "jp-meaning jp-meaning-error";
        errorElement.textContent = error.message || "翻訳に失敗しました。";
        japaneseResult.replaceChildren(errorElement);
    }
}

function setDefinitionMessage(message, isError = false) {
    const definitionContent = document.getElementById("def-content");
    const messageElement = document.createElement("div");
    messageElement.className = isError
        ? "definition-status definition-status-error"
        : "definition-status";
    messageElement.textContent = message;
    definitionContent.replaceChildren(messageElement);
}

function closeDictionary() {
    document.getElementById("definition-box").classList.remove("open");
    window.getSelection().removeAllRanges();
    if (player && typeof player.playVideo === "function") player.playVideo();
}

let isUserScrolling = false;
let scrollTimeout = null;
let isAutoScrolling = false;
const subtitleArea = document.getElementById("subtitle-area");

subtitleArea.addEventListener("scroll", () => {
    if (!isAutoScrolling) {
        isUserScrolling = true;
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            isUserScrolling = false;
        }, 3000);
    }
});

function startSync() {
    clearInterval(syncTimer);
    syncTimer = setInterval(() => {
        if (!player || !player.getCurrentTime) return;
        const time = player.getCurrentTime();
        let activeIndex = -1;

        for (let index = 0; index < transcript.length; index += 1) {
            const line = transcript[index];
            if (time >= line.start && time < line.start + line.duration) {
                activeIndex = index;
                break;
            }
        }

        if (activeIndex === -1) return;
        const activeLine = document.getElementById(`line-${activeIndex}`);
        if (!activeLine || activeLine.classList.contains("active")) return;

        document
            .querySelectorAll(".active")
            .forEach((element) => element.classList.remove("active"));
        activeLine.classList.add("active");
        if (!isUserScrolling) {
            isAutoScrolling = true;
            const container = document.getElementById("subtitle-area");
            container.scrollTo({
                top: activeLine.offsetTop - 15,
                behavior: "smooth",
            });
            setTimeout(() => {
                isAutoScrolling = false;
            }, 500);
        }
    }, 500);
}
