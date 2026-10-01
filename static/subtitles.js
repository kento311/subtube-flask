(function exposeSubtitleTools(root, factory) {
    const tools = factory();
    root.SubtubeSubtitles = tools;
    if (typeof module === "object" && module.exports) {
        module.exports = tools;
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function createTools() {
    "use strict";

    const SUPPORTED_EXTENSIONS = new Set(["json", "srt", "vtt"]);

    function extractYouTubeVideoId(input) {
        const value = String(input || "").trim();
        if (/^[A-Za-z0-9_-]{11}$/.test(value)) return value;

        let url;
        try {
            url = new URL(value);
        } catch {
            return null;
        }

        const hostname = url.hostname.toLowerCase().replace(/^www\./, "");
        let candidate = null;
        if (hostname === "youtu.be") {
            candidate = url.pathname.split("/").filter(Boolean)[0];
        } else if (
            hostname === "youtube.com" ||
            hostname.endsWith(".youtube.com") ||
            hostname === "youtube-nocookie.com" ||
            hostname.endsWith(".youtube-nocookie.com")
        ) {
            candidate = url.searchParams.get("v");
            if (!candidate) {
                const pathParts = url.pathname.split("/").filter(Boolean);
                if (["embed", "shorts", "live"].includes(pathParts[0])) {
                    candidate = pathParts[1];
                }
            }
        }

        return /^[A-Za-z0-9_-]{11}$/.test(candidate || "")
            ? candidate
            : null;
    }

    function parseTimestamp(value) {
        const normalized = String(value).trim().replace(",", ".");
        const parts = normalized.split(":");
        if (parts.length < 2 || parts.length > 3) {
            throw new Error(`不正な時刻形式です: ${value}`);
        }

        const seconds = Number(parts.pop());
        const minutes = Number(parts.pop());
        const hours = parts.length ? Number(parts.pop()) : 0;
        if (
            !Number.isFinite(hours) ||
            !Number.isFinite(minutes) ||
            !Number.isFinite(seconds) ||
            hours < 0 ||
            minutes < 0 ||
            minutes >= 60 ||
            seconds < 0 ||
            seconds >= 60
        ) {
            throw new Error(`不正な時刻形式です: ${value}`);
        }
        return hours * 3600 + minutes * 60 + seconds;
    }

    function normalizeCue(cue, index) {
        if (!cue || typeof cue !== "object") {
            throw new Error(`${index + 1}件目の字幕がオブジェクトではありません。`);
        }

        const start = Number(cue.start);
        const duration =
            cue.duration !== undefined
                ? Number(cue.duration)
                : Number(cue.end) - start;
        const text = String(cue.text ?? cue.content ?? "").trim();

        if (!Number.isFinite(start) || start < 0) {
            throw new Error(`${index + 1}件目の開始時刻が不正です。`);
        }
        if (!Number.isFinite(duration) || duration <= 0) {
            throw new Error(`${index + 1}件目の表示時間が不正です。`);
        }
        if (!text) {
            throw new Error(`${index + 1}件目の字幕本文が空です。`);
        }

        return { start, duration, text };
    }

    function parseJsonSubtitles(source) {
        let parsed;
        try {
            parsed = JSON.parse(source);
        } catch {
            throw new Error("JSON字幕を解析できませんでした。");
        }

        const cues =
            Array.isArray(parsed) && parsed.length === 1 && Array.isArray(parsed[0])
                ? parsed[0]
                : parsed;
        if (!Array.isArray(cues) || cues.length === 0) {
            throw new Error("JSON字幕に字幕データがありません。");
        }
        return cues.map(normalizeCue).sort((left, right) => left.start - right.start);
    }

    function stripVttMarkup(value) {
        return value
            .replace(/<[^>]+>/g, "")
            .replace(/&nbsp;/g, " ")
            .replace(/&amp;/g, "&")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">");
    }

    function parseTimedTextSubtitles(source) {
        const normalized = source
            .replace(/^\uFEFF/, "")
            .replace(/\r\n?/g, "\n")
            .trim();
        const blocks = normalized.split(/\n{2,}/);
        const cues = [];

        for (const block of blocks) {
            const lines = block.split("\n").map((line) => line.trim());
            if (
                !lines.length ||
                lines[0].startsWith("WEBVTT") ||
                lines[0].startsWith("NOTE") ||
                lines[0] === "STYLE" ||
                lines[0] === "REGION"
            ) {
                continue;
            }

            const timingIndex = lines.findIndex((line) => line.includes("-->"));
            if (timingIndex === -1) continue;

            const [startValue, rawEndValue] = lines[timingIndex]
                .split("-->")
                .map((value) => value.trim());
            const endValue = rawEndValue.split(/\s+/)[0];
            const start = parseTimestamp(startValue);
            const end = parseTimestamp(endValue);
            const text = stripVttMarkup(lines.slice(timingIndex + 1).join(" ")).trim();
            if (!text || end <= start) continue;
            cues.push({ start, duration: end - start, text });
        }

        if (!cues.length) {
            throw new Error("字幕キューを読み取れませんでした。");
        }
        return cues.sort((left, right) => left.start - right.start);
    }

    function parseSubtitleFile(fileName, source) {
        const extension = String(fileName || "")
            .toLowerCase()
            .split(".")
            .pop();
        if (!SUPPORTED_EXTENSIONS.has(extension)) {
            throw new Error("対応形式は JSON・VTT・SRT です。");
        }
        if (extension === "json") return parseJsonSubtitles(source);
        return parseTimedTextSubtitles(source);
    }

    return {
        extractYouTubeVideoId,
        parseJsonSubtitles,
        parseSubtitleFile,
        parseTimedTextSubtitles,
        parseTimestamp,
    };
});
