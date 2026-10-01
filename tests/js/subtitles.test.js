const test = require("node:test");
const assert = require("node:assert/strict");

const {
    extractYouTubeVideoId,
    parseSubtitleFile,
    parseTimestamp,
} = require("../../static/subtitles.js");

test("extracts a YouTube ID from supported inputs", () => {
    assert.equal(extractYouTubeVideoId("dQw4w9WgXcQ"), "dQw4w9WgXcQ");
    assert.equal(
        extractYouTubeVideoId("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        "dQw4w9WgXcQ",
    );
    assert.equal(
        extractYouTubeVideoId("https://youtu.be/dQw4w9WgXcQ?t=5"),
        "dQw4w9WgXcQ",
    );
    assert.equal(extractYouTubeVideoId("https://example.com/video"), null);
});

test("parses and sorts JSON subtitles", () => {
    const cues = parseSubtitleFile(
        "captions.json",
        JSON.stringify([
            { start: 2, duration: 1, text: "Second" },
            { start: 0, end: 1.5, content: "First" },
        ]),
    );

    assert.deepEqual(cues, [
        { start: 0, duration: 1.5, text: "First" },
        { start: 2, duration: 1, text: "Second" },
    ]);
});

test("parses SRT subtitles", () => {
    const cues = parseSubtitleFile(
        "captions.srt",
        "1\n00:00:01,000 --> 00:00:03,500\nHello\nworld\n\n2\n00:00:04,000 --> 00:00:05,000\nAgain",
    );

    assert.equal(cues.length, 2);
    assert.deepEqual(cues[0], {
        start: 1,
        duration: 2.5,
        text: "Hello world",
    });
});

test("parses VTT cue settings and removes markup", () => {
    const cues = parseSubtitleFile(
        "captions.vtt",
        "WEBVTT\n\n00:01.000 --> 00:03.000 align:start\n<v Speaker>Hello &amp; <b>welcome</b>",
    );

    assert.deepEqual(cues, [
        { start: 1, duration: 2, text: "Hello & welcome" },
    ]);
});

test("rejects invalid timestamps and unsupported formats", () => {
    assert.throws(() => parseTimestamp("00:99.000"), /不正な時刻形式/);
    assert.throws(
        () => parseSubtitleFile("captions.txt", "hello"),
        /対応形式/,
    );
});
