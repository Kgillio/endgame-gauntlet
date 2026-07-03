import json
import random
import secrets
import time
from pathlib import Path

import chess
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Endgame Gauntlet", page_icon="♟️", layout="wide")

# Visual theme: lighter blue/gray page background.
# Rating ladder: fake Premove Rating, permanent title unlocks, generated challenge ratings.
# Instant timer: typed seconds apply to the board without pressing Enter.
# Last move highlight: origin and destination squares glow like Chess.com.
# Held move fix: engine replies no longer auto-drop hovered pieces; release controls the drop.
# White piece fix: white uses the same filled glyph design as black, with a cleaner lighter outline.
# Premove chain fix: promoted pieces can premove back onto earlier path squares without freezing.
# Queued premove fix: holding a piece no longer blocks already-queued premoves from firing.
# Left ladder UI: vertical master progress bar added under the PREMOVES text.
# Left ladder render fix: HTML is built without Markdown indentation so it does not show as code.
# Promotion notice fix: title unlocks now appear beside the ladder, not over the board.
# Held piece dots fix: legal-move dots stay visible after Stockfish redraws the board.
# Loss overlay fix: game-over card now has Review, 10-Round, and Unlimited buttons.
# Countdown sound fix: 3-2-1-GO plays boop sounds when the round begins.
# Engine ladder fix: browser Stockfish is configured with gradually rising Elo/Skill and visible status.
# Stockfish load fix: tries reliable asm.js CDN builds before fallback.
# Increment control: players can set seconds added after each completed move.
# Master Tournament: loads master_tournament_positions.json built from Lichess puzzles.
# Master Tournament random start fix: opener is a direct random pick from the full Lichess pool, no buckets.
# Clean UI fix: sound/delay controls hidden; delay locked at 2100ms; position loader hidden.
# Board text cleanup: premove/engine text hidden; top bar only shows round badge; bottom space preserved.
# Material UI: bottom capture row shows player material +/- and black captured pieces are brighter.
# Board annotation UI: right-click drag draws smooth green arrows; knight arrows draw as L-shapes.
# Drag cursor fix: custom piece drag replaces native browser drag, so the grabbing-hand cursor stays visible.
# Master Tournament loader fix: shared normalize_positions helper added.
# Loss overlay fix: Master Tournament restart option added.
# Draw rule fix: draws now count as losses and show the restart menu.
# Master Tournament time fix: tournament defaults to 60 seconds but uses editable Time Control.
# Drag fix: held pieces can be dropped after the engine replies.
# Board proportions: 576px board, 72px squares, ~65px pieces.
# Layout fix: board column widened/fit so the board is not clipped.
# Hover-drop fix: held promotion premoves finish when the engine reply lands.
# Cursor fix: dragging keeps a grabbing-hand feel and highlighted target square.
# Sound update: check given and check received have unique sounds.
# Check sounds: louder wooden knocks/thumps instead of arcade tones.

st.markdown("""
<style>
.side-shell{
    background:linear-gradient(180deg, rgba(35,49,68,.78), rgba(25,38,56,.86));
    border:1px solid rgba(173,190,255,.14);
    border-radius:24px;
    padding:14px;
    box-shadow:0 18px 42px rgba(2,8,22,.22), inset 0 1px 0 rgba(255,255,255,.04);
    backdrop-filter: blur(12px);
}
.side-card{
    background:linear-gradient(180deg, rgba(53,69,93,.58), rgba(32,47,68,.78));
    border:1px solid rgba(255,255,255,.10);
    border-radius:20px;
    padding:18px 18px;
    box-shadow:0 14px 30px rgba(2,8,22,.18), inset 0 1px 0 rgba(255,255,255,.04);
    color:#eef2ff;
    margin-bottom:14px;
}
.side-card h3{margin:0 0 8px 0;font-size:20px;font-weight:700;font-family:Georgia, 'Times New Roman', serif;color:#f4f6ff;}
.side-card .sub{font-size:14px;color:#c7d2ef;}
.side-divider{height:14px;}

.side-card-light{
    background:linear-gradient(180deg, rgba(255,255,255,.20), rgba(234,240,252,.14));
    border:1px solid rgba(255,255,255,.22);
    border-radius:20px;
    padding:18px 18px;
    box-shadow:0 14px 30px rgba(2,8,22,.16), inset 0 1px 0 rgba(255,255,255,.30);
    color:#f7fbff;
    margin-bottom:14px;
    backdrop-filter: blur(10px);
}


.premove-side-wrap{display:flex;justify-content:flex-end;align-items:flex-start;height:100%;padding-top:130px;padding-right:14px;}
.premove-side-card{
    min-height:720px;
    width:170px;
    display:flex;
    flex-direction:column;
    align-items:flex-end;
    justify-content:flex-start;
    gap:26px;
}
.word-stack{display:flex;flex-direction:column;align-items:flex-end;gap:18px;text-align:right;}
.word-stack .stack-line{
    display:block;
    font-weight:1000;
    letter-spacing:1px;
    font-family:'Trebuchet MS','Arial Black','Segoe UI',sans-serif;
    text-shadow:0 4px 16px rgba(0,0,0,.22), 0 0 18px rgba(255,130,160,.14);
    white-space:nowrap;
    transform:rotate(-4deg);
}
.word-stack .line-premoves{font-size:40px;color:#ff6b7d;}
.word-stack .line-takes-1{font-size:32px;color:#ff5f86; margin-right:22px;}
.word-stack .line-takes-2{font-size:32px;color:#ff9f43; margin-right:6px; transform:rotate(3deg);}
.word-stack .line-takes-3{font-size:32px;color:#7ee0ff; margin-right:28px; transform:rotate(-2deg);}
@media (max-width: 1400px){
    .premove-side-wrap{padding-top:70px;padding-right:20px;}
    .word-stack .line-premoves{font-size:46px;}
    .word-stack .line-takes-1,.word-stack .line-takes-2,.word-stack .line-takes-3{font-size:36px;}
}


.left-ladder-card {
    width:155px;
    height:360px;
    margin-top:26px;
    position:relative;
    border-radius:24px;
    padding:14px 12px;
    background:
        radial-gradient(circle at top, rgba(143,105,255,.24), transparent 34%),
        linear-gradient(180deg, rgba(16,28,48,.64), rgba(7,13,28,.72));
    border:1px solid rgba(255,255,255,.16);
    box-shadow:0 18px 36px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.08);
    overflow:hidden;
}
.left-ladder-title {
    color:#ffffff;
    font-size:12px;
    font-weight:1000;
    letter-spacing:.10em;
    text-align:center;
    margin-bottom:8px;
    text-transform:uppercase;
    text-shadow:0 2px 8px rgba(0,0,0,.36);
}
.left-ladder-rating {
    text-align:center;
    font-size:26px;
    line-height:1;
    font-weight:1000;
    color:#ffffff;
    margin-bottom:8px;
    text-shadow:0 3px 12px rgba(0,0,0,.34);
}
.left-ladder-track {
    position:absolute;
    left:48px;
    right:48px;
    top:74px;
    bottom:38px;
    border-radius:999px;
    background:rgba(3,8,20,.52);
    border:1px solid rgba(255,255,255,.15);
    box-shadow:inset 0 2px 8px rgba(0,0,0,.42);
    overflow:hidden;
}
.left-ladder-fill {
    position:absolute;
    left:0;
    right:0;
    bottom:0;
    height:0%;
    border-radius:999px;
    background:linear-gradient(0deg,#74e2ff 0%,#8f69ff 48%,#ffe0a3 100%);
    box-shadow:0 0 18px rgba(143,105,255,.44), inset 0 1px 0 rgba(255,255,255,.35);
    transition:height .35s ease;
}
.left-ladder-glow {
    position:absolute;
    left:-14px;
    right:-14px;
    height:26px;
    top:calc(100% - var(--fill-height));
    transform:translateY(-50%);
    background:radial-gradient(circle, rgba(255,224,163,.60), transparent 68%);
    opacity:.85;
    pointer-events:none;
}
.left-ladder-tick {
    position:absolute;
    left:18px;
    right:15px;
    height:1px;
    background:rgba(255,255,255,.18);
}
.left-ladder-tick::after {
    content:attr(data-label);
    position:absolute;
    left:43px;
    top:-8px;
    color:#e9efff;
    font-size:10px;
    font-weight:900;
    text-shadow:0 2px 6px rgba(0,0,0,.45);
    white-space:nowrap;
}
.left-ladder-tick.unlocked::after {
    color:#ffe0a3;
}
.left-ladder-current-title {
    position:absolute;
    left:12px;
    right:12px;
    bottom:12px;
    text-align:center;
    color:#dbe6ff;
    font-size:11px;
    font-weight:900;
    line-height:1.25;
}
.left-ladder-current-title b {
    color:#ffe0a3;
}


.left-title-toast {
    width:165px;
    margin-top:12px;
    padding:12px 12px;
    border-radius:18px;
    text-align:center;
    color:#ffffff;
    background:
        radial-gradient(circle at top, rgba(255,224,163,.32), transparent 38%),
        linear-gradient(180deg, rgba(92,74,165,.94), rgba(20,30,58,.96));
    border:1px solid rgba(255,224,163,.48);
    box-shadow:0 16px 34px rgba(0,0,0,.24), 0 0 24px rgba(143,105,255,.20);
    animation:leftTitleToast 5.2s ease forwards;
}
.left-title-toast .toast-small {
    color:#ffe0a3;
    font-size:10px;
    font-weight:1000;
    letter-spacing:.14em;
    text-transform:uppercase;
    margin-bottom:4px;
}
.left-title-toast .toast-title {
    font-size:18px;
    line-height:1.05;
    font-weight:1000;
    text-shadow:0 2px 10px rgba(0,0,0,.28);
}
.left-title-toast .toast-full {
    margin-top:4px;
    color:#eaf0ff;
    font-size:11px;
    font-weight:900;
}
.left-title-toast .toast-next {
    margin-top:7px;
    color:#dbe6ff;
    font-size:10px;
    font-weight:800;
    line-height:1.25;
}
@keyframes leftTitleToast {
    0% { opacity:0; transform:translateY(8px) scale(.97); }
    10% { opacity:1; transform:translateY(0) scale(1); }
    82% { opacity:1; transform:translateY(0) scale(1); }
    100% { opacity:0; transform:translateY(-4px) scale(.98); }
}


/* Remove blank wrapper-card look; style real Streamlit blocks instead */
[data-testid="stExpander"] {
    background: linear-gradient(180deg, rgba(53,69,93,.58), rgba(32,47,68,.78)) !important;
    border: 1px solid rgba(255,255,255,.10) !important;
    border-radius: 18px !important;
    box-shadow: 0 14px 30px rgba(2,8,22,.18), inset 0 1px 0 rgba(255,255,255,.04) !important;
    color: #eef2ff !important;
}


/* Keep the full chessboard visible inside the center column */
[data-testid="stIFrame"] {
    overflow: visible !important;
}
[data-testid="stVerticalBlock"] {
    overflow: visible !important;
}


/* Clean game view: hide extra labels/buttons that clutter the page */
#engineStatus,
#gameStatus {
    display:none !important;
    width:0 !important;
    max-width:0 !important;
    overflow:hidden !important;
}

#premoveStatus,
.premove-status {
    visibility:hidden !important;
    color:transparent !important;
}

.message,
.buttons,
.move-nav {
    display:none !important;
}

.side-card .sub {
    display:none !important;
}


/* Layout fix: keep the 576px board fully visible */
[data-testid="stIFrame"],
iframe {
    max-width: 100% !important;
    overflow: visible !important;
}
[data-testid="column"] {
    overflow: visible !important;
}

</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
POSITIONS_FILE = BASE_DIR / "positions.json"
MASTER_TOURNAMENT_FILE = BASE_DIR / "master_tournament_positions.json"
MASTER_RECENT_OPENERS_FILE = BASE_DIR / ".master_recent_openers.json"
COMPONENT_DIR = BASE_DIR / "browser_chess_component"
COMPONENT_FILE = COMPONENT_DIR / "index.html"
TIME_INPUT_DIR = BASE_DIR / "instant_time_component"
TIME_INPUT_FILE = TIME_INPUT_DIR / "index.html"

DEFAULT_POSITIONS = [
    {"id":"rook_up_001","title":"Rook Up Endgame","opponent":"Master Defense Bot","year":"Sample","fen":"8/6k1/8/8/8/8/6K1/R7 w - - 0 1","player_color":"white","difficulty":1,"goal":"win","intro":"You are up a rook. Convert the endgame."},
    {"id":"queen_001","title":"Queen Conversion","opponent":"Last Stand Bot","year":"Sample","fen":"6k1/8/8/8/8/4Q3/6K1/8 w - - 0 1","player_color":"white","difficulty":1,"goal":"win","intro":"Queen against king. Force mate."},
    {"id":"bishop_pawns_001","title":"Bishop and Pawns","opponent":"Technique Bot","year":"Sample","fen":"8/5k2/8/3P4/5P2/2B5/6K1/8 w - - 0 1","player_color":"white","difficulty":2,"goal":"win","intro":"Use the bishop and pawns well."}
]


TIME_INPUT_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
html, body {
    margin:0;
    padding:0;
    background:transparent;
    font-family:Arial, sans-serif;
    overflow:hidden;
}
.time-shell {
    width:100%;
    box-sizing:border-box;
}
label {
    display:block;
    color:#e9efff;
    font-size:13px;
    font-weight:800;
    margin-bottom:7px;
}
input {
    width:100%;
    box-sizing:border-box;
    border:1px solid rgba(255,255,255,.20);
    border-radius:12px;
    background:rgba(8,15,30,.42);
    color:#ffffff;
    padding:10px 12px;
    font-size:18px;
    font-weight:900;
    outline:none;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
}
input:focus {
    border-color:rgba(255,224,163,.70);
    box-shadow:0 0 0 3px rgba(255,224,163,.12), inset 0 1px 0 rgba(255,255,255,.06);
}
.help {
    color:#cbd6f5;
    font-size:12px;
    line-height:1.35;
    margin-top:7px;
}
</style>
</head>
<body>
<div class="time-shell">
    <label id="inputLabel" for="valueInput">Seconds per round</label>
    <input id="valueInput" type="number" min="1" max="999" step="1" inputmode="decimal" />
    <div id="inputHelp" class="help">Updates as you type. No Enter needed.</div>
</div>
<script>
function sendMessageToStreamlit(type,data){
    window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},data),"*");
}
function setComponentReady(){
    sendMessageToStreamlit("streamlit:componentReady",{apiVersion:1});
}
function setFrameHeight(height){
    sendMessageToStreamlit("streamlit:setFrameHeight",{height:height});
}
function setComponentValue(value){
    sendMessageToStreamlit("streamlit:setComponentValue",{value:value});
}

const input=document.getElementById("valueInput");
const label=document.getElementById("inputLabel");
const help=document.getElementById("inputHelp");

let lastSent=null;
let hydrated=false;
let actionName="set_time_limit";
let minValue=1;
let maxValue=999;
let stepValue=1;
let decimals=0;

function clampValue(value){
    const n=parseFloat(value);
    if(!Number.isFinite(n))return null;
    const clamped=Math.max(minValue,Math.min(maxValue,n));
    const factor=Math.pow(10,decimals);
    return Math.round(clamped*factor)/factor;
}
function displayValue(value){
    const n=clampValue(value);
    if(n===null)return "";
    if(decimals<=0)return String(Math.round(n));
    return String(n).replace(/\.0+$/,"").replace(/(\.\d*?)0+$/,"$1");
}
function sendValue(){
    const value=clampValue(input.value);
    if(value===null)return;
    if(value===lastSent)return;
    lastSent=value;

    const payload={
        action:actionName,
        value:value,
        nonce:Date.now().toString()+"-"+Math.random().toString(16).slice(2)
    };

    if(actionName==="set_time_limit")payload.seconds=value;
    if(actionName==="set_increment")payload.increment=value;

    setComponentValue(payload);
}
input.addEventListener("input",sendValue);
input.addEventListener("change",sendValue);

window.addEventListener("message",event=>{
    if(event.data.type!=="streamlit:render")return;
    const args=event.data.args||{};

    actionName=args.action||"set_time_limit";
    minValue=Number(args.min_value ?? (actionName==="set_increment"?0:1));
    maxValue=Number(args.max_value ?? (actionName==="set_increment"?60:999));
    stepValue=Number(args.step ?? (actionName==="set_increment"?0.1:1));
    decimals=Number(args.decimals ?? (stepValue<1?1:0));

    label.textContent=args.label || (actionName==="set_increment" ? "Increment per move" : "Seconds per round");
    help.textContent=args.help_text || "Updates as you type. No Enter needed.";

    input.min=String(minValue);
    input.max=String(maxValue);
    input.step=String(stepValue);

    const value=clampValue(args.value ?? args.seconds ?? args.increment ?? (actionName==="set_increment"?0:10));

    // Do not fight the user's cursor while they are typing.
    if(value!==null && (!hydrated || document.activeElement!==input)){
        input.value=displayValue(value);
        lastSent=value;
        hydrated=true;
    }

    setFrameHeight(82);
});
setComponentReady();
setFrameHeight(82);
</script>
</body>
</html>
"""

COMPONENT_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<style>
html, body { margin:0; padding:0; background:transparent; overflow:hidden; font-family:Arial,sans-serif; scroll-behavior:auto!important; }
.wrap { width:640px; margin:0 auto; background:#2b2b2b; padding:14px; border-radius:8px; box-shadow:0 18px 35px rgba(0,0,0,.22); user-select:none; position:relative; overflow:visible; }
.top {
    width:576px;
    height:42px;
    margin:0 auto 10px;
    display:flex;
    justify-content:flex-start;
    align-items:center;
    color:#eee;
    font-size:13px;
    font-weight:800;
    overflow:hidden;
}
#gameStatus {
    display:none !important;
    width:0 !important;
    max-width:0 !important;
    min-width:0 !important;
    overflow:hidden !important;
}
.pill {
    background:rgba(255,255,255,.12);
    border:1px solid rgba(255,255,255,.18);
    border-radius:999px;
    padding:6px 10px;
    color:white;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
    text-align:center;
}
#roundBadge {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    width:auto;
    max-width:none;
    min-width:0;
}
#engineStatus {
    display:none !important;
}
.capture-row {
    width:576px;
    height:32px;
    min-height:32px;
    max-height:32px;
    display:flex;
    align-items:center;
    justify-content:flex-start;
    margin:0 auto 8px;
    gap:6px;
    flex-wrap:nowrap;
    overflow:hidden;
}
.capture-row.bottom {
    height:52px;
    min-height:52px;
    max-height:52px;
    justify-content:space-between;
    margin:8px auto 0;
}
.capture-strip {
    display:flex;
    align-items:center;
    gap:6px;
    height:32px;
    min-height:32px;
    max-height:32px;
    flex-wrap:nowrap;
    flex:1;
    overflow:hidden;
}
.cap { font-size:24px; line-height:1; opacity:1; }
.cap.white {
    color:#faf7ee;
    -webkit-text-stroke:.28px rgba(38,38,38,.60);
    paint-order:stroke fill;
    text-shadow:0 1px 0 rgba(36,36,36,.65),0 2px 3px rgba(0,0,0,.28);
}
.cap.black {
    color:#111111;
    -webkit-text-stroke:.42px rgba(255,255,255,.52);
    paint-order:stroke fill;
    text-shadow:
        0 1px 0 rgba(255,255,255,.58),
        0 0 6px rgba(255,255,255,.34),
        0 2px 4px rgba(0,0,0,.58);
}
.material-score {
    min-width:42px;
    height:28px;
    display:flex;
    align-items:center;
    justify-content:center;
    margin-left:8px;
    margin-right:8px;
    border-radius:999px;
    font-size:17px;
    font-weight:1000;
    letter-spacing:.02em;
    color:#ffffff;
    background:rgba(8,15,30,.34);
    border:1px solid rgba(255,255,255,.16);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.08), 0 8px 16px rgba(0,0,0,.16);
    text-shadow:0 2px 5px rgba(0,0,0,.45);
}
.material-score.up {
    color:#c8ffdf;
    border-color:rgba(109,255,173,.30);
}
.material-score.down {
    color:#ffccd4;
    border-color:rgba(255,91,118,.30);
}
.material-score.even {
    visibility:hidden;
}
.board { width:576px; height:576px; margin:0 auto; display:grid; grid-template-columns:repeat(8,72px); grid-template-rows:repeat(8,72px); border:1px solid rgba(0,0,0,.38); touch-action:none; position:relative; }
.square { width:72px; height:72px; position:relative; display:flex; align-items:center; justify-content:center; }
.light{background:#f0d9b5}.dark{background:#b58863}
.rank-label{position:absolute;top:5px;left:7px;font-size:14px;font-weight:800;color:rgba(0,0,0,.48);z-index:6}.file-label{position:absolute;bottom:4px;right:7px;font-size:14px;font-weight:800;color:rgba(0,0,0,.48);z-index:6}
.piece {
    font-size:65px;
    line-height:1;
    cursor:grab;
    z-index:10;
    transition:transform .06s ease;
    opacity:1;
}
.piece:active { cursor:grabbing; transform:scale(1.06); }
.piece.white {
    color:#faf7ee;
    -webkit-text-stroke:.38px rgba(38,38,38,.64);
    paint-order:stroke fill;
    text-shadow:
        0 1px 0 rgba(35,35,35,.72),
        0 2px 2px rgba(0,0,0,.44),
        0 3px 4px rgba(0,0,0,.24);
}
.piece.black { color:#202020; text-shadow:0 1px 0 rgba(255,255,255,.25),0 3px 4px rgba(0,0,0,.25); }
.piece.player-start-glow {
    animation: playerStartGlow 1s ease-out 1;
}
.piece.white.player-start-glow {
    text-shadow:
        0 0 6px rgba(255,255,255,1),
        0 0 14px rgba(170,235,255,.95),
        0 0 28px rgba(80,200,255,.9),
        0 0 44px rgba(20,135,255,.65),
        0 1px 0 #333,
        0 3px 4px rgba(0,0,0,.45);
}
.piece.black.player-start-glow {
    text-shadow:
        0 0 6px rgba(255,255,255,1),
        0 0 14px rgba(170,235,255,.95),
        0 0 28px rgba(80,200,255,.9),
        0 0 44px rgba(20,135,255,.65),
        0 1px 0 rgba(255,255,255,.25),
        0 3px 4px rgba(0,0,0,.25);
}
@keyframes playerStartGlow {
    0% { transform:scale(1); filter:brightness(1) saturate(1); }
    20% { transform:scale(1.08); filter:brightness(1.45) saturate(1.25); }
    70% { transform:scale(1.03); filter:brightness(1.22) saturate(1.15); }
    100% { transform:scale(1); filter:brightness(1) saturate(1); }
}
.square.last-move {
    background-image:linear-gradient(rgba(83,205,232,.36), rgba(83,205,232,.36));
    background-blend-mode:screen;
}
.square.selected { box-shadow:inset 0 0 0 5px #7fbf4d; }
.square.legal-empty::after { content:""; width:16px; height:16px; border-radius:50%; background:rgba(45,120,40,.45); position:absolute; z-index:2; }
.square.legal-capture { box-shadow:inset 0 0 0 5px rgba(45,120,40,.8); }
.square.user-red-highlight {
    box-shadow:
        inset 0 0 0 999px rgba(255,45,76,.24),
        inset 0 0 0 5px rgba(255,45,76,.95) !important;
}
.arrow-layer {
    position:absolute;
    inset:0;
    width:576px;
    height:576px;
    pointer-events:none;
    z-index:8;
    overflow:visible;
}
.move-arrow {
    stroke:#2fbf58;
    stroke-width:6;
    stroke-linecap:round;
    opacity:.78;
    filter:drop-shadow(0 2px 3px rgba(0,0,0,.30));
}
.move-arrow.preview {
    opacity:.62;
}
.square.in-check { box-shadow:inset 0 0 0 5px #d64545; }
.square.premove-from{box-shadow:inset 0 0 0 999px rgba(255,51,82,.18),inset 0 0 0 4px rgba(255,51,82,.88)}
.square.premove-to{box-shadow:inset 0 0 0 999px rgba(255,51,82,.36),inset 0 0 0 5px rgba(255,51,82,.95)}
.square.premove-chain{box-shadow:inset 0 0 0 999px rgba(255,51,82,.22)}
.square.premove-to::before{content:"";width:42px;height:46px;border-radius:50%;border:5px solid rgba(255,51,82,.95);background:rgba(255,51,82,.12);position:absolute;z-index:4;pointer-events:none}
.badge{position:absolute;top:4px;right:5px;background:rgba(255,51,82,.95);color:white;border-radius:999px;padding:3px 7px;font-size:13px;font-weight:900;z-index:12;box-shadow:0 2px 5px rgba(0,0,0,.28)}
.timer{color:#fff;font-size:36px;font-weight:900;line-height:1;letter-spacing:1px;min-width:130px;text-align:right;font-variant-numeric:tabular-nums;text-shadow:0 1px 0 rgba(0,0,0,.35),0 3px 8px rgba(0,0,0,.45)}
.premove-status{
    visibility:hidden !important;
    text-align:center;
    color:transparent !important;
    font-size:12px;
    font-weight:800;
    height:18px;
    min-height:18px;
    max-height:18px;
    margin-top:6px;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
.message{
    visibility:hidden !important;
    color:transparent !important;
    height:18px;
    min-height:18px;
    max-height:18px;
    line-height:18px;
    margin-top:8px;
    overflow:hidden;
}
.buttons{
    visibility:hidden !important;
    height:31px;
    min-height:31px;
    max-height:31px;
    margin-top:8px;
    overflow:hidden;
}
.move-nav{
    display:none !important;
}
.buttons button{background:#fff;border:none;border-radius:7px;padding:6px 12px;font-size:12px;cursor:pointer;color:#222}


.move-nav {
    height:36px;
    min-height:36px;
    max-height:36px;
    margin-top:8px;
    display:flex;
    justify-content:center;
    align-items:center;
    gap:10px;
    overflow:hidden;
}
.move-nav button {
    width:38px;
    height:30px;
    border:none;
    border-radius:999px;
    background:#ffffff;
    color:#111827;
    font-size:18px;
    font-weight:900;
    cursor:pointer;
    line-height:1;
}
.move-nav button:disabled {
    opacity:.38;
    cursor:not-allowed;
}
.move-nav span {
    min-width:92px;
    text-align:center;
    color:#e5e7eb;
    font-size:12px;
    font-weight:850;
    white-space:nowrap;
}


.promotion-panel {
    position:absolute;
    display:none;
    width:72px;
    background:#f8f8f8;
    border-radius:7px;
    overflow:hidden;
    z-index:9998;
    box-shadow:0 13px 28px rgba(0,0,0,.42);
    border:1px solid rgba(0,0,0,.08);
}
.promotion-panel.show {
    display:block;
}
.promotion-panel button {
    display:flex;
    align-items:center;
    justify-content:center;
    width:72px;
    height:72px;
    border:0;
    border-bottom:1px solid rgba(0,0,0,.08);
    background:#f8f8f8;
    color:#faf7ee;
    font-size:52px;
    line-height:1;
    cursor:pointer;
    -webkit-text-stroke:.38px rgba(38,38,38,.64);
    paint-order:stroke fill;
    text-shadow:
        0 1px 0 rgba(35,35,35,.72),
        0 2px 4px rgba(0,0,0,.28);
}
.promotion-panel button.black-choice {
    color:#202020;
    text-shadow:
        0 1px 0 rgba(255,255,255,.25),
        0 3px 4px rgba(0,0,0,.25);
}
.promotion-panel button:hover {
    background:#e9eef4;
}
.promotion-panel button:last-child {
    border-bottom:0;
}
.promotion-cancel {
    height:48px !important;
    font-size:30px !important;
    color:#8b8b8b !important;
    text-shadow:none !important;
    font-weight:800;
}
.square.promotion-target {
    box-shadow: inset 0 0 0 5px rgba(255,255,95,.95), inset 0 0 32px rgba(255,255,95,.48);
}


.countdown-overlay {
    position:absolute;
    inset:0;
    display:none;
    align-items:center;
    justify-content:center;
    z-index:9996;
    background:rgba(0,0,0,.20);
    pointer-events:none;
}
.countdown-overlay.show {
    display:flex;
}
.countdown-card {
    width:220px;
    height:220px;
    border-radius:36px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:rgba(17,24,39,.68);
    border:1px solid rgba(255,255,255,.16);
    box-shadow:0 26px 80px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.08);
    backdrop-filter:blur(10px);
}
.countdown-text {
    font-size:82px;
    font-weight:1000;
    color:#ffffff;
    letter-spacing:.5px;
    text-shadow:
        0 0 18px rgba(170,235,255,.45),
        0 6px 20px rgba(0,0,0,.40);
    transform:scale(1);
    animation:countdownPop .55s ease-out;
}
.countdown-text.go {
    color:#7ee0ff;
    font-size:72px;
    text-shadow:
        0 0 18px rgba(126,224,255,.72),
        0 0 34px rgba(126,224,255,.38),
        0 6px 20px rgba(0,0,0,.40);
}
@keyframes countdownPop {
    0% { transform:scale(.72); opacity:.2; }
    35% { transform:scale(1.12); opacity:1; }
    100% { transform:scale(1); opacity:1; }
}


.result-overlay {
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.62);
    display:none;
    align-items:center;
    justify-content:center;
    z-index:9999;
}
.result-overlay.show { display:flex; }
.result-card {
    width:430px;
    max-width:calc(100% - 40px);
    background:#111827;
    color:#ffffff;
    border:1px solid rgba(255,255,255,.18);
    border-radius:22px;
    padding:28px 26px;
    text-align:center;
    box-shadow:0 24px 80px rgba(0,0,0,.45);
}
.result-title {
    font-size:44px;
    font-weight:950;
    letter-spacing:.5px;
    margin-bottom:8px;
    color:#ff5a66;
    text-shadow:0 0 18px rgba(255,90,102,.35);
}
.result-detail {
    font-size:15px;
    line-height:1.45;
    color:#d1d5db;
    margin-bottom:20px;
}
.result-actions{
    display:flex;
    justify-content:center;
    align-items:center;
    gap:10px;
    flex-wrap:wrap;
    margin-top:2px;
}
.result-btn {
    background:rgba(255,255,255,.12);
    color:#ffffff;
    border:1px solid rgba(255,255,255,.18);
    border-radius:999px;
    padding:10px 16px;
    font-size:14px;
    font-weight:900;
    cursor:pointer;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.12), 0 8px 18px rgba(0,0,0,.18);
}
.result-btn.primary {
    background:#ffffff;
    color:#111827;
    border-color:#ffffff;
}
.result-btn.master {
    background:linear-gradient(180deg, rgba(255,224,163,.24), rgba(143,105,255,.24));
    color:#ffe8b5;
    border-color:rgba(255,224,163,.38);
}
.result-btn:hover { filter:brightness(1.08); transform:translateY(-1px); }

/* Hide clutter inside the chessboard component */
#engineStatus,
.message,
.buttons,
.move-nav {
    display:none !important;
    visibility:hidden !important;
    height:0 !important;
    min-height:0 !important;
    max-height:0 !important;
    margin:0 !important;
    padding:0 !important;
    overflow:hidden !important;
}

.capture-row.bottom {
    margin-bottom:0 !important;
}


/* Hide top-center engine thinking text when engine is moving */
#gameStatus:empty {
    visibility:hidden !important;
}


/* Chess.com-like held piece feel while dragging */
html.dragging-piece,
html.dragging-piece *,
body.dragging-piece,
body.dragging-piece *,
.wrap.dragging-piece,
.wrap.dragging-piece *,
.board.dragging-piece,
.board.dragging-piece *,
.square.drag-hover,
.square.drag-hover *,
.piece.drag-held {
    cursor: grabbing !important;
}

.square.drag-hover {
    box-shadow: inset 0 0 0 4px rgba(126,191,77,.70);
}

.drag-image-piece {
    position: fixed;
    left: -9999px;
    top: -9999px;
    width: 72px;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 65px;
    line-height: 1;
    pointer-events: none;
    z-index: 999999;
}
.drag-follow-piece {
    position: fixed;
    left: 0;
    top: 0;
    width: 72px;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 65px;
    line-height: 1;
    pointer-events: none;
    z-index: 999999;
    transform: translate(-50%, -50%) scale(1.08);
    cursor: grabbing !important;
    opacity: .96;
}
.piece.source-held {
    opacity: .22;
}

</style>
</head>
<body>
<div class="wrap">
  <div class="top"><div id="roundBadge" class="pill">Round 1 / 10</div><div id="gameStatus">Loading board...</div><div id="engineStatus" class="pill">Engine loading...</div></div>
  <div class="capture-row"><div id="capturedTop" class="capture-strip"></div></div>
  <div id="board" class="board"></div>
  <div id="promotionPanel" class="promotion-panel">
    <button data-promotion-piece="n" title="Knight">♘</button>
    <button data-promotion-piece="q" title="Queen">♕</button>
    <button data-promotion-piece="r" title="Rook">♖</button>
    <button data-promotion-piece="b" title="Bishop">♗</button>
    <button id="cancelPromotionButton" class="promotion-cancel" title="Cancel">×</button>
  </div>
  <div class="capture-row bottom"><div id="capturedBottom" class="capture-strip"></div><div id="materialScore" class="material-score even">0</div><div id="timerDisplay" class="timer">0:10.0</div></div>
  <div id="premoveStatus" class="premove-status"></div>
  <div class="message">Premove challenge. Right-click drag to draw green arrows. Right-click once to mark a square red. Left-click anywhere to clear annotations.</div>
  <div class="buttons"><button id="soundTestButton">Test move sound</button><button id="clearPremoveButton">Clear premoves</button></div>
  <div class="move-nav">
    <button id="prevMoveButton" title="Previous move">←</button>
    <span id="moveNavStatus">Move 0 / 0</span>
    <button id="nextMoveButton" title="Next move">→</button>
  </div>

  <div id="startCountdownOverlay" class="countdown-overlay">
    <div class="countdown-card">
      <div id="startCountdownText" class="countdown-text">3</div>
    </div>
  </div>
</div>

<div id="lossOverlay" class="result-overlay">
  <div class="result-card">
    <div class="result-title">LOST</div>
    <div id="lossOverlayDetail" class="result-detail">Time ran out.</div>
    <div class="result-actions">
      <button id="reviewBoardButton" class="result-btn primary">Review board</button>
      <button id="lossTenRoundButton" class="result-btn">10-Round Game</button>
      <button id="lossUnlimitedButton" class="result-btn">Unlimited Game</button>
      <button id="lossMasterTournamentButton" class="result-btn master">Master Tournament</button>
    </div>
  </div>
</div>

<script>
function sendMessageToStreamlit(type,data){window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},data),"*")}
function setComponentReady(){sendMessageToStreamlit("streamlit:componentReady",{apiVersion:1})}
function setFrameHeight(height){sendMessageToStreamlit("streamlit:setFrameHeight",{height:height})}
function saveParentScroll(){try{const y=window.parent.scrollY||window.parent.document.documentElement.scrollTop||0;window.parent.sessionStorage.setItem("browser_engine_scroll_y",y.toString())}catch(e){}}
function restoreParentScroll(){try{const saved=window.parent.sessionStorage.getItem("browser_engine_scroll_y");if(saved===null)return;const y=Number(saved);if(!Number.isFinite(y))return;setTimeout(()=>window.parent.scrollTo(0,y),25);setTimeout(()=>window.parent.scrollTo(0,y),125);setTimeout(()=>window.parent.scrollTo(0,y),300)}catch(e){}}
function setComponentValue(value){saveParentScroll();sendMessageToStreamlit("streamlit:setComponentValue",{value:value})}

const PIECES={P:"♟",N:"♞",B:"♝",R:"♜",Q:"♛",K:"♚",p:"♟",n:"♞",b:"♝",r:"♜",q:"♛",k:"♚"};
const files=["a","b","c","d","e","f","g","h"], ranks=["8","7","6","5","4","3","2","1"];function displayFiles(){return playerChar==="b"?["h","g","f","e","d","c","b","a"]:files}function displayRanks(){return playerChar==="b"?["1","2","3","4","5","6","7","8"]:ranks}
let chess=null, playerColor="white", playerChar="w", currentFen="", currentToken=null, currentRoundNumber=1, currentTotalRounds=10;
let selectedSquare=null, draggedFrom=null, premoveQueue=[], visualPieces=null, showPlayerStartGlow=false, playerGlowTimer=null, roundEnded=false, lossOverlayVisible=false, dismissedLossToken=null, positionTimeline=[], timelineIndex=0, browsingTimeline=false, previewMode=false, pendingPromotion=null, countdownActive=false, countdownTimer=null, playerHasMovedThisRound=false, lastDragClientX=0, lastDragClientY=0, lastDragHoverSquare=null, lastMoveFrom=null, lastMoveTo=null;
let timerInterval=null, remainingMs=10000, lastTickMs=Date.now(), timerTimeoutSent=false, currentTimerInitialSeconds=10, currentTimerIncrementSeconds=0, timerIncrementMs=0;const PREMOVE_PENALTY_MS=100;
let engineWorker=null, engineReady=false, engineThinking=false, engineFallback=true, engineMoveTimeMs=1500;
let currentStockfishElo=800, currentStockfishSkill=0, lastEngineStatusPayload="";
let soundEnabled=true, audioCtx=null;
let userMarkedSquares=new Set();
let drawnArrows=[], arrowDraftFrom=null, arrowDraftTo=null, arrowDraftPoint=null, arrowMouseDown=false, suppressNextSquareClick=false;
let customPieceDragActive=false, customPieceDragFrom=null, customPieceDragGhost=null, customPieceDragSourceEl=null, customPieceDragMoved=false, customPieceDragStartX=0, customPieceDragStartY=0;
function reportEngineStatus(status,detail,stockfish){
    const payload=status+"|"+detail+"|"+stockfish+"|"+currentStockfishElo+"|"+currentStockfishSkill;
    if(payload===lastEngineStatusPayload)return;
    lastEngineStatusPayload=payload;

    setComponentValue({
        action:"engine_status",
        status:status,
        detail:detail,
        stockfish:stockfish===true,
        elo:currentStockfishElo,
        skill:currentStockfishSkill,
        nonce:Date.now().toString()+"-"+Math.random().toString()
    });
}
function configureStockfishStrength(){
    if(!engineWorker||!engineReady||engineFallback)return;

    const visibleElo=Math.max(800,Math.min(3200,Number(currentStockfishElo||800)));
    const skill=Math.max(0,Math.min(20,Number(currentStockfishSkill||0)));

    try{
        engineWorker.postMessage("setoption name Skill Level value "+skill);
        engineWorker.postMessage("setoption name UCI_LimitStrength value true");
        engineWorker.postMessage("setoption name UCI_Elo value "+Math.max(1320,Math.min(3190,visibleElo)));
        engineWorker.postMessage("isready");
    }catch(e){}
}
function nameToColorChar(n){return n==="black"?"b":"w"}
function isPlayerTurn(){return chess&&chess.turn()===playerChar&&!engineThinking&&!countdownActive}
function isEngineTurn(){return chess&&chess.turn()!==playerChar&&!chess.game_over()&&!countdownActive}
function unlockAudio(){try{const AC=window.AudioContext||window.webkitAudioContext;if(!audioCtx)audioCtx=new AC();if(audioCtx.state==="suspended")audioCtx.resume()}catch(e){}}
function playMoveSound(){try{unlockAudio();if(!audioCtx||!soundEnabled)return;const now=audioCtx.currentTime;function knock(t,v,p){const dur=.075,bs=Math.floor(audioCtx.sampleRate*dur),buf=audioCtx.createBuffer(1,bs,audioCtx.sampleRate),data=buf.getChannelData(0);for(let i=0;i<bs;i++){const d=Math.pow(1-i/bs,4.5);data[i]=(Math.random()*2-1)*d}const noise=audioCtx.createBufferSource();noise.buffer=buf;const bp=audioCtx.createBiquadFilter();bp.type="bandpass";bp.frequency.setValueAtTime(p,t);bp.Q.setValueAtTime(7.5,t);const g=audioCtx.createGain();g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(v,t+.006);g.gain.exponentialRampToValueAtTime(.0001,t+dur);noise.connect(bp);bp.connect(g);g.connect(audioCtx.destination);noise.start(t);noise.stop(t+dur)}knock(now,.42,950);knock(now+.045,.28,1350)}catch(e){}}
function playCountdownBoop(text){
    try{
        unlockAudio();
        if(!audioCtx||!soundEnabled)return;

        const now=audioCtx.currentTime;
        const isGo=text==="GO!";
        const freq=isGo?880:520;
        const freq2=isGo?1320:650;
        const dur=isGo?.18:.12;
        const volume=isGo?.22:.16;

        function boop(t,f,v,d){
            const osc=audioCtx.createOscillator();
            const gain=audioCtx.createGain();
            const low=audioCtx.createBiquadFilter();

            osc.type="sine";
            osc.frequency.setValueAtTime(f,t);
            osc.frequency.exponentialRampToValueAtTime(f*0.82,t+d);

            low.type="lowpass";
            low.frequency.setValueAtTime(1800,t);

            gain.gain.setValueAtTime(.0001,t);
            gain.gain.exponentialRampToValueAtTime(v,t+.014);
            gain.gain.exponentialRampToValueAtTime(.0001,t+d);

            osc.connect(low);
            low.connect(gain);
            gain.connect(audioCtx.destination);

            osc.start(t);
            osc.stop(t+d);
        }

        boop(now,freq,volume,dur);

        if(isGo){
            boop(now+.075,freq2,.16,.13);
        }
    }catch(e){}
}
function playWoodHit(t,volume,frequency,duration=.105,q=9.5){
    const samples=Math.floor(audioCtx.sampleRate*duration);
    const buffer=audioCtx.createBuffer(1,samples,audioCtx.sampleRate);
    const data=buffer.getChannelData(0);
    for(let i=0;i<samples;i++){
        const fade=Math.pow(1-i/samples,5.2);
        data[i]=(Math.random()*2-1)*fade;
    }

    const noise=audioCtx.createBufferSource();
    noise.buffer=buffer;

    const body=audioCtx.createBiquadFilter();
    body.type="bandpass";
    body.frequency.setValueAtTime(frequency,t);
    body.Q.setValueAtTime(q,t);

    const low=audioCtx.createBiquadFilter();
    low.type="lowpass";
    low.frequency.setValueAtTime(2400,t);

    const gain=audioCtx.createGain();
    gain.gain.setValueAtTime(.0001,t);
    gain.gain.exponentialRampToValueAtTime(volume,t+.005);
    gain.gain.exponentialRampToValueAtTime(.0001,t+duration);

    noise.connect(body);
    body.connect(low);
    low.connect(gain);
    gain.connect(audioCtx.destination);
    noise.start(t);
    noise.stop(t+duration);
}
function playWoodThump(t,volume,frequency=145,duration=.16){
    const osc=audioCtx.createOscillator();
    const gain=audioCtx.createGain();
    const low=audioCtx.createBiquadFilter();
    osc.type="sine";
    osc.frequency.setValueAtTime(frequency,t);
    osc.frequency.exponentialRampToValueAtTime(Math.max(60,frequency*.55),t+duration);
    low.type="lowpass";
    low.frequency.setValueAtTime(420,t);
    gain.gain.setValueAtTime(.0001,t);
    gain.gain.exponentialRampToValueAtTime(volume,t+.006);
    gain.gain.exponentialRampToValueAtTime(.0001,t+duration);
    osc.connect(low);
    low.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(t);
    osc.stop(t+duration);
}
function playCheckOpponentSound(){
    try{
        unlockAudio();
        if(!audioCtx||!soundEnabled)return;
        const now=audioCtx.currentTime;

        // Louder attacking check: crisp wooden double-tap plus a small body thump.
        playWoodThump(now,.16,170,.13);
        playWoodHit(now,.72,1050,.105,10.5);
        playWoodHit(now+.060,.54,1450,.085,11.5);
        playWoodHit(now+.128,.38,1850,.070,12.5);
    }catch(e){}
}
function playYouAreCheckedSound(){
    try{
        unlockAudio();
        if(!audioCtx||!soundEnabled)return;
        const now=audioCtx.currentTime;

        // Louder warning check: deeper wooden knock, less arcade, more urgent.
        playWoodThump(now,.24,120,.19);
        playWoodHit(now,.82,620,.135,8.5);
        playWoodHit(now+.115,.62,430,.145,7.5);
    }catch(e){}
}
function playMoveOrCheckSound(){try{if(chess&&(chess.in_checkmate()||chess.in_check())){if(chess.turn()===playerChar)playYouAreCheckedSound();else playCheckOpponentSound();return}playMoveSound()}catch(e){playMoveSound()}}
function formatTime(ms){const safe=Math.max(0,Math.floor(ms)),totalSec=Math.floor(safe/1000),min=Math.floor(totalSec/60),sec=totalSec%60,tenth=Math.floor((safe%1000)/100);return min.toString()+":"+sec.toString().padStart(2,"0")+"."+tenth.toString()}
function updateTimerDisplay(){const el=document.getElementById("timerDisplay");if(el)el.textContent=formatTime(remainingMs)}
function hideStartCountdown(){
    countdownActive=false;
    if(countdownTimer){clearTimeout(countdownTimer);countdownTimer=null}
    const overlay=document.getElementById("startCountdownOverlay");
    if(overlay)overlay.classList.remove("show");
}
function showStartCountdownText(text){
    const overlay=document.getElementById("startCountdownOverlay");
    const el=document.getElementById("startCountdownText");
    if(!overlay||!el)return;
    el.textContent=text;
    el.classList.toggle("go",text==="GO!");
    el.style.animation="none";
    void el.offsetWidth;
    el.style.animation="countdownPop .55s ease-out";
    overlay.classList.add("show");
    playCountdownBoop(text);
}
function startRoundCountdown(onDone){
    if(previewMode){onDone&&onDone();return}
    if(countdownTimer){clearTimeout(countdownTimer);countdownTimer=null}
    countdownActive=true;
    engineThinking=false;
    const sequence=["3","2","1","GO!"];
    let index=0;
    function step(){
        if(!countdownActive)return;
        if(index<sequence.length){
            showStartCountdownText(sequence[index]);
            updateStatus("Starting in "+sequence[index].replace("GO!","GO"));
            index+=1;
            countdownTimer=setTimeout(step,850);
            return;
        }
        hideStartCountdown();
        onDone&&onDone();
    }
    step();
}
function startTimer(sec){remainingMs=sec*1000;lastTickMs=Date.now();timerTimeoutSent=false;if(timerInterval)clearInterval(timerInterval);if(previewMode){updateTimerDisplay();return}function tick(){const now=Date.now();if(isPlayerTurn()&&remainingMs>0)remainingMs-=(now-lastTickMs);lastTickMs=now;updateTimerDisplay();if(remainingMs<=0&&!timerTimeoutSent&&!roundEnded){remainingMs=0;updateTimerDisplay();timerTimeoutSent=true;finishRound("loss","Time ran out.")}}tick();timerInterval=setInterval(tick,30)}
function addMoveIncrement(){if(timerIncrementMs>0&&!previewMode&&!roundEnded){remainingMs+=timerIncrementMs;updateTimerDisplay()}}
function deductPremovePenalty(){remainingMs=Math.max(0,remainingMs-PREMOVE_PENALTY_MS);updateTimerDisplay()}
function pieceMapFromChess(game){const map={},board=game.board();for(let r=0;r<8;r++){for(let f=0;f<8;f++){const p=board[r][f];if(!p)continue;const sq=files[f]+ranks[r],sym=p.color==="w"?p.type.toUpperCase():p.type.toLowerCase();map[sq]={symbol:PIECES[sym],color:p.color==="w"?"white":"black",type:p.type,colorChar:p.color}}}return map}
function clonePieces(map){return JSON.parse(JSON.stringify(map))}
function getDisplayChess(){
    if(browsingTimeline&&positionTimeline[timelineIndex]){
        try{return new Chess(positionTimeline[timelineIndex])}catch(e){}
    }
    return chess;
}
function currentPiecesForDisplay(){return visualPieces||pieceMapFromChess(getDisplayChess())}
function updateMoveNavStatus(){
    const status=document.getElementById("moveNavStatus");
    const prev=document.getElementById("prevMoveButton");
    const next=document.getElementById("nextMoveButton");
    const max=Math.max(0,positionTimeline.length-1);
    if(status)status.textContent="Move "+timelineIndex+" / "+max;
    if(prev)prev.disabled=timelineIndex<=0;
    if(next)next.disabled=timelineIndex>=max;
}
function recordTimeline(){
    if(!chess)return;
    const fen=chess.fen();
    if(positionTimeline.length&&positionTimeline[positionTimeline.length-1]===fen){
        timelineIndex=positionTimeline.length-1;
        browsingTimeline=false;
        updateMoveNavStatus();
        return;
    }
    if(browsingTimeline){
        positionTimeline=positionTimeline.slice(0,timelineIndex+1);
    }
    positionTimeline.push(fen);
    timelineIndex=positionTimeline.length-1;
    browsingTimeline=false;
    updateMoveNavStatus();
}
function navigateMove(dir){
    if(!positionTimeline.length||engineThinking)return;
    const max=positionTimeline.length-1;
    const next=Math.max(0,Math.min(max,timelineIndex+dir));
    if(next===timelineIndex)return;
    premoveQueue=[];
    visualPieces=null;
    selectedSquare=null;
    draggedFrom=null;
    timelineIndex=next;
    browsingTimeline=timelineIndex!==max;
    buildBoard(true);
    updateStatus(browsingTimeline?"Move review "+timelineIndex+" / "+max:"Current position");
    updateMoveNavStatus();
}
function prepareBoardForInteraction(){
    if(!browsingTimeline)return true;
    if(roundEnded&&positionTimeline[timelineIndex]){
        try{
            chess=new Chess(positionTimeline[timelineIndex]);
            positionTimeline=positionTimeline.slice(0,timelineIndex+1);
            timelineIndex=positionTimeline.length-1;
            browsingTimeline=false;
            visualPieces=null;
            updateMoveNavStatus();
            return true;
        }catch(e){}
    }
    timelineIndex=Math.max(0,positionTimeline.length-1);
    browsingTimeline=false;
    visualPieces=null;
    buildBoard(false);
    updateMoveNavStatus();
    return false;
}
function promotionSymbol(colorChar,promo){return PIECES[colorChar==="w"?promo.toUpperCase():promo.toLowerCase()]}
function applyVisualMove(map,uci){const from=uci.slice(0,2),to=uci.slice(2,4),p=map[from];if(!p)return map;delete map[from];map[to]=p;if(p.type==="p"&&((p.colorChar==="w"&&to[1]==="8")||(p.colorChar==="b"&&to[1]==="1"))){const promo=(uci.length>4?uci[4]:"q");map[to].symbol=promotionSymbol(p.colorChar,promo);map[to].type=promo}if(p.type==="k"&&p.colorChar==="w"&&from==="e1"&&to==="g1"&&map.h1){map.f1=map.h1;delete map.h1}if(p.type==="k"&&p.colorChar==="w"&&from==="e1"&&to==="c1"&&map.a1){map.d1=map.a1;delete map.a1}if(p.type==="k"&&p.colorChar==="b"&&from==="e8"&&to==="g8"&&map.h8){map.f8=map.h8;delete map.h8}if(p.type==="k"&&p.colorChar==="b"&&from==="e8"&&to==="c8"&&map.a8){map.d8=map.a8;delete map.a8}return map}
function rebuildVisualPiecesFromQueue(){const map=clonePieces(pieceMapFromChess(chess));premoveQueue.forEach(uci=>applyVisualMove(map,uci));visualPieces=premoveQueue.length?map:null}
function legalUci(from,to,promotion="q"){if(!chess)return null;for(const m of chess.moves({square:from,verbose:true})){if(m.to===to)return from+to+(m.promotion?promotion:"")}return null}
function playerPieceAt(sq){const p=currentPiecesForDisplay()[sq];return p&&p.colorChar===playerChar}
function realOwnPieceAt(sq){const p=pieceMapFromChess(chess)[sq];return p&&p.colorChar===chess.turn()}
function legalTargets(from){return chess?chess.moves({square:from,verbose:true}).map(m=>m.to):[]}
function squareFR(sq){return{f:files.indexOf(sq[0]),r:parseInt(sq[1],10)}}
function squareFromFR(f,r){if(f<0||f>7||r<1||r>8)return null;return files[f]+r.toString()}
function isClearLine(map,from,to,df,dr){let a=squareFR(from),b=squareFR(to);let f=a.f+df,r=a.r+dr;while(f!==b.f||r!==b.r){const sq=squareFromFR(f,r);if(!sq)return false;if(map[sq])return false;f+=df;r+=dr}return true}
function premoveUci(from,to,promotion="q"){
    const map=currentPiecesForDisplay();
    const p=map[from];
    if(!p||p.colorChar!==playerChar)return null;

    const a=squareFR(from),b=squareFR(to);
    const dx=b.f-a.f,dy=b.r-a.r;
    const adx=Math.abs(dx),ady=Math.abs(dy);
    let ok=false;
    let promo="";

    // Premove validation is intentionally geometry-based.
    // This lets players queue "hope" premoves like Q to a8 or pawn diagonal captures.
    // When the move actually fires, chess.js validates the real board.
    // If a piece is still blocking it then, the premove is suspended and the board snaps back.
    if(p.type==="p"){
        const dir=p.colorChar==="w"?1:-1;
        const startRank=p.colorChar==="w"?2:7;
        const promoteRank=p.colorChar==="w"?8:1;

        if(dx===0&&dy===dir)ok=true;
        if(dx===0&&dy===2*dir&&a.r===startRank)ok=true;
        if(adx===1&&dy===dir)ok=true;

        if(ok&&b.r===promoteRank)promo=promotion||"q";
    }else if(p.type==="n"){
        ok=(adx===1&&ady===2)||(adx===2&&ady===1);
    }else if(p.type==="b"){
        ok=adx===ady&&adx>0;
    }else if(p.type==="r"){
        ok=(dx===0&&ady>0)||(dy===0&&adx>0);
    }else if(p.type==="q"){
        ok=(adx===ady&&adx>0)||((dx===0&&ady>0)||(dy===0&&adx>0));
    }else if(p.type==="k"){
        ok=adx<=1&&ady<=1&&(adx+ady)>0;
    }

    return ok?from+to+promo:null;
}
function premoveTargets(from){const targets=[];for(const f of files){for(let r=1;r<=8;r++){const to=f+r.toString();if(to!==from&&premoveUci(from,to))targets.push(to)}}return targets}
function squareCenter(sq){
    const df=displayFiles();
    const dr=displayRanks();
    const col=df.indexOf(sq[0]);
    const row=dr.indexOf(sq[1]);
    if(col<0||row<0)return null;
    return {x:(col*72)+36,y:(row*72)+36};
}
function pointFromClient(x,y){
    const board=document.getElementById("board");
    if(!board)return null;

    const rect=board.getBoundingClientRect();
    const px=Math.max(0,Math.min(576,x-rect.left));
    const py=Math.max(0,Math.min(576,y-rect.top));

    return {x:px,y:py};
}
function squareOnlyFromClientPoint(x,y){
    const el=document.elementFromPoint(x,y);
    if(!el)return null;
    const sqEl=el.closest ? el.closest(".square") : null;
    return sqEl&&sqEl.dataset.square ? sqEl.dataset.square : null;
}
function annotationPieceType(square){
    const map=currentPiecesForDisplay ? currentPiecesForDisplay() : {};
    const p=map&&map[square] ? map[square] : (pieceMapFromChess(chess)[square]||null);
    return p ? String(p.type||"").toLowerCase() : "";
}
function annotationTargets(square){
    const map=currentPiecesForDisplay ? currentPiecesForDisplay() : pieceMapFromChess(chess);
    const p=map&&map[square] ? map[square] : null;
    if(!p)return null;

    const out=[];
    const seen=new Set();
    const start=squareFR(square);

    function addTarget(f,r){
        const sq=squareFromFR(f,r);
        if(!sq||sq===square)return false;
        const occ=map[sq]||null;
        if(occ&&occ.colorChar===p.colorChar)return false;
        if(!seen.has(sq)){
            out.push(sq);
            seen.add(sq);
        }
        return !occ;
    }
    function ray(df,dr){
        let f=start.f+df, r=start.r+dr;
        while(true){
            const sq=squareFromFR(f,r);
            if(!sq)break;
            const occ=map[sq]||null;
            if(occ&&occ.colorChar===p.colorChar)break;
            if(!seen.has(sq)){
                out.push(sq);
                seen.add(sq);
            }
            if(occ)break;
            f+=df;
            r+=dr;
        }
    }

    if(p.type==='p'){
        const dir=p.colorChar==='w'?1:-1;
        const startRank=p.colorChar==='w'?2:7;
        const one=squareFromFR(start.f,start.r+dir);
        if(one&&!map[one]){
            out.push(one); seen.add(one);
            const two=squareFromFR(start.f,start.r+(2*dir));
            if(start.r===startRank&&two&&!map[two]){ out.push(two); seen.add(two); }
        }
        [[-1,dir],[1,dir]].forEach(([df,dr])=>{
            const sq=squareFromFR(start.f+df,start.r+dr);
            const occ=sq?map[sq]:null;
            if(sq&&occ&&occ.colorChar!==p.colorChar&&!seen.has(sq)){
                out.push(sq);
                seen.add(sq);
            }
        });
    }else if(p.type==='n'){
        [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]].forEach(([df,dr])=>addTarget(start.f+df,start.r+dr));
    }else if(p.type==='b'){
        [[1,1],[1,-1],[-1,1],[-1,-1]].forEach(([df,dr])=>ray(df,dr));
    }else if(p.type==='r'){
        [[1,0],[-1,0],[0,1],[0,-1]].forEach(([df,dr])=>ray(df,dr));
    }else if(p.type==='q'){
        [[1,1],[1,-1],[-1,1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]].forEach(([df,dr])=>ray(df,dr));
    }else if(p.type==='k'){
        for(let df=-1;df<=1;df++){
            for(let dr=-1;dr<=1;dr++){
                if(df===0&&dr===0)continue;
                addTarget(start.f+df,start.r+dr);
            }
        }
    }
    return out;
}
function annotationTargetSet(square){
    const list=annotationTargets(square);
    return list?new Set(list):null;
}
function annotationAllowsTarget(from,to){
    const set=annotationTargetSet(from);
    return !set || set.has(to);
}
function shouldDrawKnightArrow(from,toOrPoint){
    return annotationPieceType(from)==='n';
}
function ensureArrowLayer(){
    const board=document.getElementById("board");
    if(!board)return null;

    let svg=document.getElementById("moveArrowLayer");

    if(svg)return svg;

    svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("id","moveArrowLayer");
    svg.setAttribute("class","arrow-layer");
    svg.setAttribute("viewBox","0 0 576 576");

    const defs=document.createElementNS("http://www.w3.org/2000/svg","defs");
    const marker=document.createElementNS("http://www.w3.org/2000/svg","marker");
    marker.setAttribute("id","greenArrowHead");
    marker.setAttribute("markerWidth","10");
    marker.setAttribute("markerHeight","10");
    marker.setAttribute("refX","8.5");
    marker.setAttribute("refY","5");
    marker.setAttribute("orient","auto");
    marker.setAttribute("markerUnits","strokeWidth");

    const path=document.createElementNS("http://www.w3.org/2000/svg","path");
    path.setAttribute("d","M1.5,1.5 L8.5,5 L1.5,8.5 Z");
    path.setAttribute("fill","#2fbf58");
    path.setAttribute("opacity",".88");

    marker.appendChild(path);
    defs.appendChild(marker);
    svg.appendChild(defs);
    board.appendChild(svg);
    return svg;
}
function shortenedEndPoint(prev,end,shorten=18){
    const dx=end.x-prev.x;
    const dy=end.y-prev.y;
    const len=Math.sqrt(dx*dx+dy*dy)||1;

    if(len<=shorten)return end;

    return {
        x:end.x-(dx/len)*shorten,
        y:end.y-(dy/len)*shorten
    };
}
function buildArrowPoints(from,target,forceKnight=false){
    const start=squareCenter(from);
    const end=target&&target.square ? squareCenter(target.square) : target;

    if(!start||!end)return [];

    if(!forceKnight){
        const shortened=shortenedEndPoint(start,end,18);
        return [start,shortened];
    }

    const dx=end.x-start.x;
    const dy=end.y-start.y;
    let bend;

    // Knight arrows get a proper L shape.
    // The longer leg is drawn first, like a visual knight move path.
    if(Math.abs(dx)>Math.abs(dy)){
        bend={x:end.x,y:start.y};
    }else{
        bend={x:start.x,y:end.y};
    }

    const shortened=shortenedEndPoint(bend,end,18);

    return [start,bend,shortened];
}
function drawArrowPath(svg,from,target,preview=false,forceKnight=false){
    const points=buildArrowPoints(from,target,forceKnight);

    if(!svg||points.length<2)return;

    const start=points[0];
    const end=points[points.length-1];

    if(Math.abs(start.x-end.x)<2&&Math.abs(start.y-end.y)<2)return;

    const path=document.createElementNS("http://www.w3.org/2000/svg","path");
    const d=points.map((p,i)=>(i===0?"M":"L")+p.x.toFixed(1)+","+p.y.toFixed(1)).join(" ");

    path.setAttribute("class","move-arrow"+(preview?" preview":""));
    path.setAttribute("d",d);
    path.setAttribute("fill","none");
    path.setAttribute("marker-end","url(#greenArrowHead)");
    svg.appendChild(path);
}
function renderUserArrows(){
    const old=document.getElementById("moveArrowLayer");
    if(old)old.remove();

    if(!drawnArrows.length && !(arrowDraftFrom&&arrowDraftPoint))return;

    const svg=ensureArrowLayer();
    if(!svg)return;

    drawnArrows.forEach(a=>{
        drawArrowPath(svg,a.from,{square:a.to},false,a.knight===true);
    });

    if(arrowDraftFrom&&arrowDraftPoint){
        drawArrowPath(
            svg,
            arrowDraftFrom,
            arrowDraftPoint,
            true,
            shouldDrawKnightArrow(arrowDraftFrom,arrowDraftPoint)
        );
    }
}
function clearMoveArrows(){
    drawnArrows=[];
    arrowDraftFrom=null;
    arrowDraftTo=null;
    arrowDraftPoint=null;
    arrowMouseDown=false;
    const svg=document.getElementById("moveArrowLayer");
    if(svg)svg.remove();
}
function beginBoardArrow(square,ev){
    if(!square||!ev||ev.button!==2)return false;

    // Chess.com-style: right-click hold/drag from ANY square, piece, or empty square.
    ev.preventDefault();
    ev.stopPropagation();

    arrowMouseDown=true;
    arrowDraftFrom=square;
    arrowDraftTo=square;
    arrowDraftPoint=pointFromClient(ev.clientX,ev.clientY)||squareCenter(square);
    return true;
}
function updateBoardArrow(ev){
    if(!arrowMouseDown||!arrowDraftFrom)return;

    const hoverSquare=squareOnlyFromClientPoint(ev.clientX,ev.clientY);
    const allowed=annotationTargetSet(arrowDraftFrom);

    if(!allowed){
        arrowDraftTo=hoverSquare||arrowDraftTo;
        arrowDraftPoint=pointFromClient(ev.clientX,ev.clientY)||arrowDraftPoint;
    }else if(hoverSquare&&allowed.has(hoverSquare)){
        arrowDraftTo=hoverSquare;
        arrowDraftPoint={square:hoverSquare};
    }else if(hoverSquare===arrowDraftFrom){
        arrowDraftTo=arrowDraftFrom;
        arrowDraftPoint={square:hoverSquare};
    }else{
        arrowDraftPoint=null;
    }

    renderUserArrows();
}
function finishBoardArrow(ev){
    if(!arrowMouseDown||!arrowDraftFrom)return false;

    if(ev){
        ev.preventDefault();
        ev.stopPropagation();
    }

    const from=arrowDraftFrom;
    const allowed=annotationTargetSet(from);
    const rawTo=squareOnlyFromClientPoint(ev.clientX,ev.clientY)||arrowDraftTo;
    const to=(allowed&&rawTo&&rawTo!==from&&!allowed.has(rawTo)) ? null : rawTo;
    const isKnight=to?shouldDrawKnightArrow(from,{square:to}):false;

    arrowMouseDown=false;
    arrowDraftFrom=null;
    arrowDraftTo=null;
    arrowDraftPoint=null;

    // Right-click tap on same square = red highlight toggle.
    if(!to||to===from){
        if(!rawTo || rawTo===from){
            toggleUserRedHighlight(from);
        }
        renderUserArrows();
        return true;
    }

    // Right-click drag to another square = green arrow toggle.
    const existingIndex=drawnArrows.findIndex(a=>a.from===from&&a.to===to);

    if(existingIndex>=0){
        drawnArrows.splice(existingIndex,1);
    }else{
        drawnArrows.push({from:from,to:to,knight:isKnight});
    }

    renderUserArrows();
    return true;
}
function applyUserRedHighlights(){
    document.querySelectorAll(".square").forEach(square=>{
        square.classList.toggle("user-red-highlight",userMarkedSquares.has(square.dataset.square));
    });
}
function toggleUserRedHighlight(square){
    if(!square)return;
    if(userMarkedSquares.has(square))userMarkedSquares.delete(square);
    else userMarkedSquares.add(square);
    applyUserRedHighlights();
}
function clearUserRedHighlights(){
    if(!userMarkedSquares||!userMarkedSquares.size)return;
    userMarkedSquares.clear();
    applyUserRedHighlights();
}
function clearBoardAnnotations(){
    clearUserRedHighlights();
    clearMoveArrows();
}
function clearHighlights(){document.querySelectorAll(".square").forEach(s=>s.classList.remove("selected","legal-empty","legal-capture"))}
function setPremoveStatusText(txt){const st=document.getElementById("premoveStatus");if(st)st.textContent=txt}
function highlightPremoveFrom(square){clearHighlights();const se=document.querySelector(`[data-square="${square}"]`);if(se)se.classList.add("selected");const map=currentPiecesForDisplay();premoveTargets(square).forEach(t=>{const te=document.querySelector(`[data-square="${t}"]`);if(!te)return;if(map[t])te.classList.add("legal-capture");else te.classList.add("legal-empty")});renderPremoveHighlights()}
function restoreHeldMoveDots(){
    if(!draggedFrom||roundEnded||!chess||chess.game_over())return;

    // While Stockfish is thinking, show premove dots from the held piece.
    if(engineThinking||isEngineTurn()){
        if(playerPieceAt(draggedFrom)){
            highlightPremoveFrom(draggedFrom);
        }
        return;
    }

    // After Stockfish replies, keep the dots visible but switch to true legal moves.
    // This makes the held move feel like Chess.com: dots stay under the piece
    // until the player releases it.
    if(isPlayerTurn()){
        if(realOwnPieceAt(draggedFrom)){
            highlightFrom(draggedFrom);
        }else if(playerPieceAt(draggedFrom)){
            highlightPremoveFrom(draggedFrom);
        }
    }
}
function renderPremoveHighlights(){document.querySelectorAll(".square").forEach(s=>{s.classList.remove("premove-from","premove-to","premove-chain");const b=s.querySelector(".badge");if(b)b.remove()});premoveQueue.forEach((uci,i)=>{const from=uci.slice(0,2),to=uci.slice(2,4),fe=document.querySelector(`[data-square="${from}"]`),te=document.querySelector(`[data-square="${to}"]`);if(fe)fe.classList.add(i===0?"premove-from":"premove-chain");if(te){te.classList.add("premove-to");const b=document.createElement("div");b.className="badge";b.textContent=(i+1).toString();te.appendChild(b)}});const st=document.getElementById("premoveStatus");if(st){if(premoveQueue.length)st.textContent="Premove queued ("+premoveQueue.length+"/14, -0.1s each): "+premoveQueue.join(" • ");else if(engineThinking||isEngineTurn())st.textContent="Engine thinking — premove now.";else st.textContent=""}}
function isRealPromotionMove(from,to){
    if(!chess)return false;
    for(const m of chess.moves({square:from,verbose:true})){
        if(m.to===to&&m.promotion)return true;
    }
    return false;
}
function isPremovePromotionMove(from,to){
    const map=currentPiecesForDisplay();
    const p=map[from];
    if(!p||p.colorChar!==playerChar||p.type!=="p")return false;
    const endRank=p.colorChar==="w"?"8":"1";
    return to[1]===endRank && premoveUci(from,to);
}
function setPromotionSymbols(){
    const white=playerChar==="w";
    const symbols={q:"♛",r:"♜",b:"♝",n:"♞"};
    document.querySelectorAll("[data-promotion-piece]").forEach(btn=>{
        const piece=btn.dataset.promotionPiece;
        btn.textContent=symbols[piece]||btn.textContent;
        btn.classList.toggle("black-choice",!white);
    });
}
function clearPromotionTarget(){
    document.querySelectorAll(".square.promotion-target").forEach(s=>s.classList.remove("promotion-target"));
}
function positionPromotionPanel(to){
    const panel=document.getElementById("promotionPanel");
    const board=document.getElementById("board");
    const square=document.querySelector(`[data-square="${to}"]`);
    if(!panel||!board||!square)return;

    const panelWidth=72;
    const panelHeight=(72*4)+48;
    const squareSize=square.offsetWidth||100;

    let left=board.offsetLeft+square.offsetLeft+((squareSize-panelWidth)/2);
    let top;

    if(to[1]==="8"){
        top=board.offsetTop+square.offsetTop;
    }else{
        top=board.offsetTop+square.offsetTop+squareSize-panelHeight;
    }

    const minLeft=board.offsetLeft;
    const maxLeft=board.offsetLeft+board.offsetWidth-panelWidth;
    const minTop=board.offsetTop;
    const maxTop=board.offsetTop+board.offsetHeight-panelHeight;

    left=Math.max(minLeft,Math.min(maxLeft,left));
    top=Math.max(minTop,Math.min(maxTop,top));

    panel.style.left=left+"px";
    panel.style.top=top+"px";
}
function showPromotionPicker(from,to,isPremove){
    pendingPromotion={from:from,to:to,isPremove:isPremove};
    setPromotionSymbols();
    clearPromotionTarget();
    const target=document.querySelector(`[data-square="${to}"]`);
    if(target)target.classList.add("promotion-target");
    positionPromotionPanel(to);
    const panel=document.getElementById("promotionPanel");
    if(panel)panel.classList.add("show");
    updateStatus(isPremove?"Choose promotion for premove.":"Choose promotion.");
}
function hidePromotionPicker(){
    pendingPromotion=null;
    clearPromotionTarget();
    const panel=document.getElementById("promotionPanel");
    if(panel)panel.classList.remove("show");
}
function pushPremoveUci(uci){
    premoveQueue.push(uci);
    deductPremovePenalty();

    // Rebuild from the whole queued path each time.
    // This allows square reuse, like promoting on d8 and then premoving the new queen
    // back to d4/d7 or any earlier square in the premove path.
    rebuildVisualPiecesFromQueue();
    buildBoard(false);
    renderPremoveHighlights();
    return true;
}
function queuePremoveWithPromotion(from,to,promotion){
    if(premoveQueue.length>=14){setPremoveStatusText("Premove limit reached: 14 moves.");return false}
    const uci=premoveUci(from,to,promotion);
    if(!uci){setPremoveStatusText("Premove blocked: that piece does not move in that direction.");return false}
    return pushPremoveUci(uci);
}
function completePromotion(promotion){
    if(!pendingPromotion)return;
    const job=pendingPromotion;
    hidePromotionPicker();

    if(job.isPremove){
        const queued=queuePremoveWithPromotion(job.from,job.to,promotion);
        selectedSquare=null;
        draggedFrom=null;
        clearHighlights();
        renderPremoveHighlights();

        // Important fix:
        // If the engine replied while the promotion picker was open,
        // it is already the player's turn again. In that case, execute
        // the queued promotion premove immediately instead of leaving it
        // sitting in the queue while the player's clock runs.
        if(queued && isPlayerTurn() && !engineThinking && !chess.game_over()){
            setTimeout(()=>tryExecutePremoveChain(),0);
        }
        return;
    }

    makePlayerMove(job.from,job.to,promotion);
}
function queuePremove(from,to){if(premoveQueue.length>=14){setPremoveStatusText("Premove limit reached: 14 moves.");return false}const uci=premoveUci(from,to);if(!uci){setPremoveStatusText("Premove blocked: that piece does not move in that direction.");return false}if(isPremovePromotionMove(from,to)){showPromotionPicker(from,to,true);return true}return pushPremoveUci(uci)}
function clearPremoves(){
    premoveQueue=[];
    visualPieces=null;
    selectedSquare=null;
    draggedFrom=null;
    lastDragHoverSquare=null;
    setDraggingCursor(false);
    clearDragHover();
    hidePromotionPicker();
    clearHighlights();
    buildBoard(false);
    const st=document.getElementById("premoveStatus");
    if(st)st.textContent="Premoves cleared.";
}
function highlightFrom(square){clearHighlights();const se=document.querySelector(`[data-square="${square}"]`);if(se)se.classList.add("selected");const map=pieceMapFromChess(chess);legalTargets(square).forEach(t=>{const te=document.querySelector(`[data-square="${t}"]`);if(!te)return;if(map[t])te.classList.add("legal-capture");else te.classList.add("legal-empty")});renderPremoveHighlights()}
function suspendPremoveQueue(message){
    premoveQueue=[];
    visualPieces=null;
    selectedSquare=null;
    draggedFrom=null;
    lastDragHoverSquare=null;
    pendingPromotion=null;
    setDraggingCursor(false);
    clearDragHover();
    hidePromotionPicker();
    clearHighlights();
    buildBoard(true);
    updateStatus((message||"Premove suspended.")+" Make any legal move.");
    if(chess&&!roundEnded&&!chess.game_over()&&chess.turn()!==playerChar){
        setTimeout(()=>startEngineMove(),60);
    }
}
function makePlayerMove(from,to,promotion="q"){const uci=legalUci(from,to,promotion);if(!uci)return false;const move=chess.move({from:from,to:to,promotion:promotion});if(!move)return false;setLastMove(from,to);playerHasMovedThisRound=true;recordTimeline();playMoveOrCheckSound();addMoveIncrement();premoveQueue=[];visualPieces=null;selectedSquare=null;draggedFrom=null;lastDragHoverSquare=null;buildBoard(true);updateStatus();checkRoundEnd();if(!roundEnded&&!chess.game_over()&&chess.turn()!==playerChar)startEngineMove();return true}
function tryMove(from,to){if(isRealPromotionMove(from,to)){showPromotionPicker(from,to,false);return true}return makePlayerMove(from,to,"q")}
function tryExecutePremoveChain(){
    if(!isPlayerTurn())return;

    while(premoveQueue.length&&isPlayerTurn()&&!chess.game_over()){
        const uci=premoveQueue.shift();
        const from=uci.slice(0,2);
        const to=uci.slice(2,4);
        const promo=uci.length>4?uci[4]:"q";

        const legal=legalUci(from,to,promo);
        if(!legal){
            suspendPremoveQueue("Premove suspended: "+uci+" was not legal after the engine reply.");
            return;
        }

        const move=chess.move({from:from,to:to,promotion:promo});
        if(!move){
            suspendPremoveQueue("Premove suspended: "+uci+" was not legal.");
            return;
        }

        setLastMove(from,to);
        playerHasMovedThisRound=true;
        recordTimeline();
        playMoveOrCheckSound();
        addMoveIncrement();
        updateStatus("");

        // Important for promotion chains:
        // after d7-d8=Q, rebuild the remaining queue from the real promoted queen,
        // so premoves like Qd8-d4 or Qd8-d7 can still be shown and fired correctly.
        rebuildVisualPiecesFromQueue();
        buildBoard(false);
        checkRoundEnd();

        if(roundEnded||chess.game_over())return;

        if(chess.turn()!==playerChar){
            startEngineMove();
            return;
        }
    }

    rebuildVisualPiecesFromQueue();
    buildBoard(true);
}
function setLastMove(from,to){
    lastMoveFrom=from||null;
    lastMoveTo=to||null;
}
function isPieceDraggableNow(piece){
    if(!piece||countdownActive||!chess||chess.game_over())return false;

    if(engineThinking||isEngineTurn()){
        return piece.colorChar===playerChar;
    }

    return piece.colorChar===chess.turn();
}
function updateCustomPieceGhost(ev){
    if(!customPieceDragGhost||!ev)return;

    customPieceDragGhost.style.left=ev.clientX+"px";
    customPieceDragGhost.style.top=ev.clientY+"px";
}
function createCustomPieceGhost(pieceEl,ev){
    removeCustomPieceGhost();

    if(!pieceEl||!ev)return;

    const ghost=pieceEl.cloneNode(true);
    ghost.classList.remove("source-held");
    ghost.classList.add("drag-follow-piece");
    ghost.style.cursor="grabbing";
    document.body.appendChild(ghost);
    customPieceDragGhost=ghost;
    updateCustomPieceGhost(ev);
}
function removeCustomPieceGhost(){
    if(customPieceDragGhost){
        try{customPieceDragGhost.remove()}catch(e){}
    }

    customPieceDragGhost=null;

    if(customPieceDragSourceEl){
        customPieceDragSourceEl.classList.remove("source-held","drag-held");
    }

    customPieceDragSourceEl=null;
}
function cleanupCustomPieceDrag(){
    customPieceDragActive=false;
    customPieceDragFrom=null;
    customPieceDragMoved=false;
    removeCustomPieceGhost();
    setDraggingCursor(false);
    clearDragHover();
}
function beginCustomPieceDrag(square,piece,pieceEl,ev){
    if(!ev||ev.button!==0)return false;
    if(!isPieceDraggableNow(piece))return false;

    ev.preventDefault();
    ev.stopPropagation();

    unlockAudio();
    prepareBoardForInteraction();

    customPieceDragActive=true;
    customPieceDragFrom=square;
    customPieceDragMoved=false;
    customPieceDragStartX=ev.clientX;
    customPieceDragStartY=ev.clientY;
    customPieceDragSourceEl=pieceEl;

    draggedFrom=square;
    selectedSquare=square;
    lastDragHoverSquare=square;

    setDraggingCursor(true);

    if(pieceEl){
        pieceEl.classList.add("source-held","drag-held");
    }

    createCustomPieceGhost(pieceEl,ev);

    if(engineThinking||isEngineTurn()){
        highlightPremoveFrom(square);
    }else{
        highlightFrom(square);
    }

    markDragHover(square);
    return true;
}
function updateCustomPieceDrag(ev){
    if(!customPieceDragActive)return;

    ev.preventDefault();

    const dx=ev.clientX-customPieceDragStartX;
    const dy=ev.clientY-customPieceDragStartY;

    if(Math.sqrt(dx*dx+dy*dy)>3){
        customPieceDragMoved=true;
    }

    rememberDragPoint(ev);
    updateCustomPieceGhost(ev);
    setDraggingCursor(true);

    const sq=squareOnlyFromClientPoint(ev.clientX,ev.clientY);

    if(sq){
        lastDragHoverSquare=sq;
        markDragHover(sq);
    }
}
function finishCustomPieceDrag(ev){
    if(!customPieceDragActive)return false;

    if(ev){
        ev.preventDefault();
        ev.stopPropagation();
        rememberDragPoint(ev);
    }

    const from=customPieceDragFrom||draggedFrom;
    const target=ev ? (squareOnlyFromClientPoint(ev.clientX,ev.clientY)||lastDragHoverSquare) : lastDragHoverSquare;

    removeCustomPieceGhost();

    suppressNextSquareClick=true;

    if(target&&from&&target!==from){
        handleDrop(target);
        customPieceDragActive=false;
        customPieceDragFrom=null;
        customPieceDragMoved=false;
        return true;
    }

    draggedFrom=null;
    selectedSquare=null;
    lastDragHoverSquare=null;
    customPieceDragActive=false;
    customPieceDragFrom=null;
    customPieceDragMoved=false;
    setDraggingCursor(false);
    clearDragHover();
    clearHighlights();
    renderPremoveHighlights();

    return true;
}
function setDraggingCursor(on){
    document.documentElement.classList.toggle("dragging-piece",on);
    document.body.classList.toggle("dragging-piece",on);

    if(on){
        document.documentElement.style.setProperty("cursor","grabbing","important");
        document.body.style.setProperty("cursor","grabbing","important");
    }else{
        document.documentElement.style.removeProperty("cursor");
        document.body.style.removeProperty("cursor");
        document.querySelectorAll(".piece.drag-held").forEach(p=>p.classList.remove("drag-held"));
        document.querySelectorAll(".piece.source-held").forEach(p=>p.classList.remove("source-held"));
    }

    const wrap=document.querySelector(".wrap");
    const board=document.getElementById("board");

    if(wrap){
        wrap.classList.toggle("dragging-piece",on);
        if(on)wrap.style.setProperty("cursor","grabbing","important");
        else wrap.style.removeProperty("cursor");
    }

    if(board){
        board.classList.toggle("dragging-piece",on);
        if(on)board.style.setProperty("cursor","grabbing","important");
        else board.style.removeProperty("cursor");
    }
}
function clearDragHover(){
    document.querySelectorAll(".square.drag-hover").forEach(el=>el.classList.remove("drag-hover"));
}
function markDragHover(square){
    clearDragHover();
    if(!square)return;
    const el=document.querySelector(`[data-square="${square}"]`);
    if(el)el.classList.add("drag-hover");
}
function setCustomDragImage(ev,pieceEl){
    if(!ev||!ev.dataTransfer||!pieceEl)return;
    const ghost=pieceEl.cloneNode(true);
    ghost.classList.add("drag-image-piece");
    ghost.style.cursor="grabbing";
    document.body.appendChild(ghost);
    try{ev.dataTransfer.setDragImage(ghost,36,36)}catch(e){}
    setTimeout(()=>{try{ghost.remove()}catch(e){}},0);
}
function squareFromClientPoint(x,y){
    if(x||y){
        const el=document.elementFromPoint(x,y);
        if(el){
            const sqEl=el.closest ? el.closest(".square") : null;
            if(sqEl && sqEl.dataset.square){
                lastDragHoverSquare=sqEl.dataset.square;
                markDragHover(lastDragHoverSquare);
                return sqEl.dataset.square;
            }
        }
    }
    markDragHover(lastDragHoverSquare);
    return lastDragHoverSquare;
}
function rememberDragPoint(ev){
    if(ev&&ev.clientX&&ev.clientY){
        lastDragClientX=ev.clientX;
        lastDragClientY=ev.clientY;
    }
}
function finishDragAtPoint(ev){
    if(!draggedFrom)return;
    rememberDragPoint(ev);
    const target=squareFromClientPoint(lastDragClientX,lastDragClientY);
    if(target){
        handleDrop(target);
        return;
    }
    draggedFrom=null;
    selectedSquare=null;
    lastDragHoverSquare=null;
    setDraggingCursor(false);
    clearDragHover();
    clearHighlights();
    renderPremoveHighlights();
}
function selectSquare(square){if(countdownActive)return;if(!chess||chess.game_over())return;if(!prepareBoardForInteraction())return;if(engineThinking||isEngineTurn()){if(!selectedSquare){if(playerPieceAt(square)){selectedSquare=square;highlightPremoveFrom(square)}return}if(selectedSquare===square){selectedSquare=null;clearHighlights();renderPremoveHighlights();return}if(queuePremove(selectedSquare,square)){selectedSquare=null;clearHighlights();renderPremoveHighlights();return}highlightPremoveFrom(selectedSquare);return}if(!selectedSquare){if(realOwnPieceAt(square)){selectedSquare=square;highlightFrom(square)}return}if(selectedSquare===square){selectedSquare=null;clearHighlights();renderPremoveHighlights();return}if(tryMove(selectedSquare,square))return;if(realOwnPieceAt(square)){selectedSquare=square;highlightFrom(square)}else{selectedSquare=null;clearHighlights();renderPremoveHighlights()}}
function handleDrop(toSquare){if(countdownActive){draggedFrom=null;selectedSquare=null;lastDragHoverSquare=null;setDraggingCursor(false);clearDragHover();clearMoveArrows();return}if(!draggedFrom)return;if(!prepareBoardForInteraction())return;if(engineThinking||isEngineTurn()){queuePremove(draggedFrom,toSquare);draggedFrom=null;selectedSquare=null;lastDragHoverSquare=null;setDraggingCursor(false);clearDragHover();clearMoveArrows();clearHighlights();renderPremoveHighlights();return}tryMove(draggedFrom,toSquare);draggedFrom=null;selectedSquare=null;lastDragHoverSquare=null;setDraggingCursor(false);clearDragHover();clearMoveArrows();clearHighlights();renderPremoveHighlights()}
function updateStatus(extra=""){
    const st=document.getElementById("gameStatus");
    if(!st||!chess)return;

    // Keep the board clean: no engine-thinking, premove-window, or constant "to move" text.
    if(engineThinking || countdownActive){
        st.textContent="";
        return;
    }

    let text="";

    // Only show the player their side at the beginning of each round.
    // After their first move/premove, this stays blank until the next round.
    if(!previewMode && !playerHasMovedThisRound && !roundEnded){
        text="You are "+(playerColor==="black"?"Black":"White");
    }else if(chess.in_checkmate()){
        text="Checkmate";
    }else if(chess.in_stalemate()){
        text="Stalemate";
    }else if(chess.in_draw()){
        text="Draw";
    }

    if(extra && !String(extra).includes("Premove now") && !String(extra).includes("engine replies") && !String(extra).includes("to move")){
        text = text ? text+" | "+extra : extra;
    }

    st.textContent=text;
}
function checkRoundEnd(){
    if(roundEnded||!chess)return;
    if(chess.in_checkmate()){
        const winner=chess.turn()==="w"?"b":"w";
        finishRound(winner===playerChar?"win":"loss",winner===playerChar?"You checkmated the engine.":"The engine checkmated you.");
        return;
    }
    if(chess.in_draw()||chess.in_stalemate()||chess.in_threefold_repetition()||chess.insufficient_material())finishRound("draw","The position ended in a draw.");
}
function showLossOverlay(detail){
    lossOverlayVisible=true;
    const overlay=document.getElementById("lossOverlay");
    const detailEl=document.getElementById("lossOverlayDetail");
    if(detailEl)detailEl.textContent=detail||"You lost the round.";
    if(overlay)overlay.classList.add("show");
}
function hideLossOverlay(){
    lossOverlayVisible=false;
    dismissedLossToken=currentToken;
    const overlay=document.getElementById("lossOverlay");
    if(overlay)overlay.classList.remove("show");
    updateStatus("Review mode — move pieces from here.");
}
function requestNewGame(mode){
    setComponentValue({
        action:"start_game",
        mode:mode,
        nonce:Date.now().toString()+"-"+Math.random().toString()
    });
}
function finishRound(result,detail){
    if(roundEnded)return;

    // In this game, a draw is a failed conversion, so it counts as a loss.
    if(result==="draw"){
        result="loss";
        detail=detail||"Game drawn. Draws count as losses.";
    }

    roundEnded=true;
    engineThinking=false;
    premoveQueue=[];
    visualPieces=null;
    selectedSquare=null;
    draggedFrom=null;
    if(timerInterval){clearInterval(timerInterval);timerInterval=null}
    hideStartCountdown();
    if(previewMode){
        updateStatus("Ready board — choose a mode or test moves.");
        buildBoard(true);
        return;
    }
    if(result==="loss")showLossOverlay(detail);
    setComponentValue({action:"round_result",result:result,detail:detail,fen:chess.fen(),history:chess.history(),nonce:Date.now().toString()+"-"+Math.random().toString()})
}
function fallbackEngineMove(){
    const moves=chess.moves({verbose:true});
    if(!moves.length)return null;

    const mates=[],caps=[],checks=[];
    for(const m of moves){
        const temp=new Chess(chess.fen());
        temp.move({from:m.from,to:m.to,promotion:m.promotion||"q"});
        if(temp.in_checkmate())mates.push(m);
        else if(m.captured)caps.push(m);
        else if(temp.in_check())checks.push(m);
    }

    const elo=Number(currentStockfishElo||800);

    if(elo<1000){
        return moves[Math.floor(Math.random()*moves.length)];
    }

    if(mates.length)return mates[Math.floor(Math.random()*mates.length)];

    if(elo<1400){
        const pool=[...moves,...caps,...checks];
        return pool[Math.floor(Math.random()*pool.length)];
    }

    if(elo<1900){
        if(caps.length&&Math.random()<.72)return caps[Math.floor(Math.random()*caps.length)];
        if(checks.length&&Math.random()<.55)return checks[Math.floor(Math.random()*checks.length)];
        return moves[Math.floor(Math.random()*moves.length)];
    }

    if(caps.length)return caps[Math.floor(Math.random()*caps.length)];
    if(checks.length)return checks[Math.floor(Math.random()*checks.length)];
    return moves[Math.floor(Math.random()*moves.length)];
}
function applyEngineMoveUci(uci){
    if(!uci||uci==="(none)"){
        checkRoundEnd();
        return;
    }

    const from=uci.slice(0,2),to=uci.slice(2,4);
    const move=chess.move({from:from,to:to,promotion:uci.length>4?uci[4]:"q"});
    engineThinking=false;

    if(move){
        setLastMove(from,to);
        recordTimeline();
        playMoveOrCheckSound();
    }

    // If a browser drag got stale during a redraw, do not let that stale held state
    // block queued premoves from firing.
    if(draggedFrom){
        const held=currentPiecesForDisplay()[draggedFrom];
        if(!held||held.colorChar!==playerChar){
            draggedFrom=null;
            selectedSquare=null;
            lastDragHoverSquare=null;
            setDraggingCursor(false);
            clearDragHover();
        }
    }

    const keepHeldPieceDropAlive=!!draggedFrom;
    const hasQueuedPremoves=premoveQueue.length>0;

    updateStatus(
        keepHeldPieceDropAlive
            ? (hasQueuedPremoves ? "Queued premove firing. Release only when you want to add/drop another move." : "Release to drop your held move.")
            : (pendingPromotion ? "Choose promotion to fire your premove." : "")
    );

    buildBoard(!keepHeldPieceDropAlive);
    checkRoundEnd();

    if(chess.game_over())return;

    // Manual-release fix should only stop an unqueued hovered move from auto-dropping.
    // It should NOT stop premoves that are already queued, especially promotion chains
    // like a2-a1=Q then Qa1-a3 or back to the previous file/rank.
    if(hasQueuedPremoves){
        setTimeout(()=>tryExecutePremoveChain(),35);
        return;
    }

    if(keepHeldPieceDropAlive){
        return;
    }

    setTimeout(()=>tryExecutePremoveChain(),35);
}
function startEngineMove(){if(countdownActive||roundEnded||!isEngineTurn()||chess.game_over())return;engineThinking=true;updateStatus("Premove now — engine replies in " + (engineMoveTimeMs/1000).toFixed(1) + "s");buildBoard(false);if(engineWorker&&engineReady&&!engineFallback){configureStockfishStrength();reportEngineStatus("Stockfish connected","Using Stockfish at Gauntlet Elo "+currentStockfishElo,true);engineWorker.postMessage("position fen "+chess.fen());engineWorker.postMessage("go movetime "+engineMoveTimeMs.toString());return}reportEngineStatus("Fallback bot","Stockfish did not load in the browser. This is NOT real Stockfish.",false);setTimeout(()=>{const move=fallbackEngineMove();if(!move){engineThinking=false;checkRoundEnd();return}applyEngineMoveUci(move.from+move.to+(move.promotion||""))},engineMoveTimeMs)}
function initStockfishWorker(){
    const es=document.getElementById("engineStatus");

    // Older asm.js Stockfish builds are much more reliable in a Streamlit iframe
    // than newer WASM builds because they do not need separate .wasm files.
    const urls=[
        "https://cdnjs.cloudflare.com/ajax/libs/stockfish.js/10.0.2/stockfish.js",
        "https://cdn.jsdelivr.net/gh/nmrugg/stockfish.js/stockfish.js",
        "https://cdn.jsdelivr.net/gh/nmrugg/stockfish.js@master/stockfish.js",
        "https://cdn.jsdelivr.net/npm/stockfish@16.0.0/src/stockfish.js",
        "https://cdn.jsdelivr.net/npm/stockfish/src/stockfish.js",
        "https://unpkg.com/stockfish/src/stockfish.js"
    ];

    function tryUrl(i){
        if(i>=urls.length){
            engineFallback=true;
            engineReady=false;
            if(es)es.textContent="Fallback bot";
            reportEngineStatus(
                "Fallback bot",
                "Stockfish did not load. Check browser console/CDN access. This is NOT real Stockfish.",
                false
            );
            return;
        }

        const url=urls[i];
        if(es)es.textContent="Trying Stockfish "+(i+1)+"/"+urls.length;
        reportEngineStatus("Trying Stockfish","Loading engine source "+(i+1)+" of "+urls.length,false);

        try{
            const workerCode=[
                "self.onerror=function(e){postMessage('worker_error '+(e.message||e));};",
                "try{importScripts('"+url+"');}catch(e){postMessage('worker_error '+(e.message||e));}"
            ].join("\n");

            const blob=new Blob([workerCode],{type:"application/javascript"});
            const worker=new Worker(URL.createObjectURL(blob));

            let readyTimer=setTimeout(()=>{
                try{worker.terminate()}catch(e){}
                tryUrl(i+1);
            },6500);

            worker.onmessage=e=>{
                const line=String(e.data||"").trim();

                if(line.startsWith("worker_error")){
                    clearTimeout(readyTimer);
                    try{worker.terminate()}catch(err){}
                    tryUrl(i+1);
                    return;
                }

                if(line.includes("uciok")){
                    clearTimeout(readyTimer);
                    engineWorker=worker;
                    engineReady=true;
                    engineFallback=false;

                    if(es)es.textContent="Stockfish • Elo "+currentStockfishElo;
                    configureStockfishStrength();
                    reportEngineStatus(
                        "Stockfish connected",
                        "Using browser Stockfish at Gauntlet Elo "+currentStockfishElo,
                        true
                    );
                    worker.postMessage("isready");
                    return;
                }

                if(line.startsWith("bestmove")){
                    const parts=line.split(/\s+/);
                    applyEngineMoveUci(parts[1]);
                }
            };

            worker.onerror=()=>{
                clearTimeout(readyTimer);
                try{worker.terminate()}catch(e){}
                tryUrl(i+1);
            };

            worker.postMessage("uci");
        }catch(e){
            tryUrl(i+1);
        }
    }

    tryUrl(0);
}
function pieceValue(type){
    return ({p:1,n:3,b:3,r:5,q:9,k:0})[String(type||"").toLowerCase()]||0;
}
function materialBalanceForPlayer(game=chess){
    let white=0,black=0;
    Object.values(pieceMapFromChess(game)).forEach(p=>{
        if(p.colorChar==="w")white+=pieceValue(p.type);
        else if(p.colorChar==="b")black+=pieceValue(p.type);
    });
    return playerChar==="b" ? (black-white) : (white-black);
}
function updateMaterialScore(game=chess){
    const el=document.getElementById("materialScore");
    if(!el)return;
    const balance=materialBalanceForPlayer(game);
    el.classList.remove("up","down","even");
    if(balance===0){
        el.textContent="0";
        el.classList.add("even");
        return;
    }
    el.textContent=(balance>0?"+":"")+balance.toString();
    el.classList.add(balance>0?"up":"down");
}
function renderCaptured(){
    const game=getDisplayChess();
    const start={P:8,N:2,B:2,R:2,Q:1,p:8,n:2,b:2,r:2,q:1},cur={};
    Object.values(pieceMapFromChess(game)).forEach(p=>{
        const c=p.color==="white"?p.type.toUpperCase():p.type.toLowerCase();
        cur[c]=(cur[c]||0)+1;
    });
    const top=document.getElementById("capturedTop"),bot=document.getElementById("capturedBottom");
    if(top)top.innerHTML="";
    if(bot)bot.innerHTML="";
    ["P","N","B","R","Q"].forEach(s=>{
        for(let i=0;i<Math.max(0,start[s]-(cur[s]||0));i++){
            const el=document.createElement("div");
            el.className="cap white";
            el.textContent=PIECES[s];
            top&&top.appendChild(el);
        }
    });
    ["p","n","b","r","q"].forEach(s=>{
        for(let i=0;i<Math.max(0,start[s]-(cur[s]||0));i++){
            const el=document.createElement("div");
            el.className="cap black";
            el.textContent=PIECES[s];
            bot&&bot.appendChild(el);
        }
    });
    updateMaterialScore(game);
}
function findKingSquare(color,game=chess){const map=pieceMapFromChess(game);for(const [sq,p] of Object.entries(map)){if(p.type==="k"&&p.colorChar===color)return sq}return null}
function buildBoard(resetSelection=true){
    const boardEl=document.getElementById("board");
    boardEl.oncontextmenu=(ev)=>{
        ev.preventDefault();
        return false;
    };
    boardEl.innerHTML="";const displayGame=getDisplayChess();const map=currentPiecesForDisplay();displayRanks().forEach((rank,ri)=>{displayFiles().forEach((file,fi)=>{const sq=file+rank;const square=document.createElement("div");square.className="square";square.dataset.square=sq;square.classList.add((ri+fi)%2===1?"dark":"light");if(userMarkedSquares.has(sq))square.classList.add("user-red-highlight");if(sq===lastMoveFrom||sq===lastMoveTo)square.classList.add("last-move");if(file===displayFiles()[0]){const l=document.createElement("div");l.className="rank-label";l.textContent=rank;square.appendChild(l)}if(rank===displayRanks()[7]){const l=document.createElement("div");l.className="file-label";l.textContent=file;square.appendChild(l)}const king=displayGame.in_check()?findKingSquare(displayGame.turn(),displayGame):null;if(king===sq)square.classList.add("in-check");const piece=map[sq];if(piece){const pe=document.createElement("div");pe.className="piece "+piece.color;if(showPlayerStartGlow&&piece.colorChar===playerChar)pe.classList.add("player-start-glow");pe.textContent=piece.symbol;pe.draggable=false;pe.addEventListener("contextmenu",ev=>{ev.preventDefault();ev.stopPropagation();return false});pe.addEventListener("mousedown",ev=>{unlockAudio();if(ev.button===0){beginCustomPieceDrag(sq,piece,pe,ev);return}beginBoardArrow(sq,ev)});square.appendChild(pe)}square.addEventListener("contextmenu",ev=>{ev.preventDefault();ev.stopPropagation();return false});square.addEventListener("mousedown",ev=>{beginBoardArrow(sq,ev)});square.addEventListener("click",()=>{if(suppressNextSquareClick){suppressNextSquareClick=false;return}clearBoardAnnotations();selectSquare(sq)});square.addEventListener("mouseover",()=>{if(customPieceDragActive){lastDragHoverSquare=sq;markDragHover(sq)}});square.addEventListener("dragover",ev=>{ev.preventDefault();lastDragHoverSquare=sq;markDragHover(sq);rememberDragPoint(ev)});square.addEventListener("drop",ev=>{ev.preventDefault();handleDrop(sq)});boardEl.appendChild(square)})});renderPremoveHighlights();renderCaptured();renderUserArrows();if(resetSelection){selectedSquare=null;draggedFrom=null}else{restoreHeldMoveDots()}const test=document.getElementById("soundTestButton");if(test)test.onclick=()=>playMoveSound();const clear=document.getElementById("clearPremoveButton");if(clear)clear.onclick=()=>clearPremoves();
const reviewButton=document.getElementById("reviewBoardButton");if(reviewButton)reviewButton.onclick=(ev)=>{ev.preventDefault();hideLossOverlay()};
const lossTenRoundButton=document.getElementById("lossTenRoundButton");if(lossTenRoundButton)lossTenRoundButton.onclick=(ev)=>{ev.preventDefault();requestNewGame("ten_round")};
const lossUnlimitedButton=document.getElementById("lossUnlimitedButton");if(lossUnlimitedButton)lossUnlimitedButton.onclick=(ev)=>{ev.preventDefault();requestNewGame("unlimited")};
const lossMasterTournamentButton=document.getElementById("lossMasterTournamentButton");if(lossMasterTournamentButton)lossMasterTournamentButton.onclick=(ev)=>{ev.preventDefault();requestNewGame("master_tournament")};
const lossOverlay=document.getElementById("lossOverlay");if(lossOverlay)lossOverlay.onclick=(ev)=>{if(ev.target===lossOverlay)hideLossOverlay()};
const prevButton=document.getElementById("prevMoveButton");if(prevButton)prevButton.onclick=(ev)=>{ev.preventDefault();navigateMove(-1)};
const nextButton=document.getElementById("nextMoveButton");if(nextButton)nextButton.onclick=(ev)=>{ev.preventDefault();navigateMove(1)};
document.querySelectorAll("[data-promotion-piece]").forEach(btn=>{btn.onclick=(ev)=>{ev.preventDefault();completePromotion(btn.dataset.promotionPiece)}});
const cancelPromotionButton=document.getElementById("cancelPromotionButton");if(cancelPromotionButton)cancelPromotionButton.onclick=(ev)=>{ev.preventDefault();hidePromotionPicker();selectedSquare=null;draggedFrom=null;lastDragHoverSquare=null;clearHighlights();renderPremoveHighlights()};
if(pendingPromotion){positionPromotionPanel(pendingPromotion.to);}
updateMoveNavStatus();
setFrameHeight(790);restoreParentScroll()}
function initPosition(args){if(typeof Chess==="undefined"){const st=document.getElementById("gameStatus");if(st)st.textContent="Could not load chess.js. Check internet/CDN access.";return}currentToken=args.round_token;currentFen=args.fen;currentRoundNumber=args.round_number||1;currentTotalRounds=args.total_rounds||10;previewMode=args.preview_mode===true;playerColor=args.player_color||"white";const rb=document.getElementById("roundBadge");if(rb)rb.textContent=previewMode?("Ready Board — "+(playerColor==="black"?"Black":"White")):("Round "+currentRoundNumber+" / "+currentTotalRounds+" — "+(playerColor==="black"?"Black":"White"));playerChar=nameToColorChar(playerColor);soundEnabled=args.sound_enabled!==false;engineMoveTimeMs=args.engine_move_time_ms||1500;currentStockfishElo=Math.max(800,Math.min(3200,Number(args.stockfish_elo||800)));currentStockfishSkill=Math.max(0,Math.min(20,Number(args.stockfish_skill||0)));configureStockfishStrength();chess=new Chess(currentFen);positionTimeline=[chess.fen()];timelineIndex=0;browsingTimeline=false;premoveQueue=[];visualPieces=null;selectedSquare=null;draggedFrom=null;lastDragHoverSquare=null;lastMoveFrom=null;lastMoveTo=null;setDraggingCursor(false);clearDragHover();clearMoveArrows();userMarkedSquares.clear();drawnArrows=[];arrowDraftFrom=null;arrowDraftTo=null;engineThinking=false;playerHasMovedThisRound=false;roundEnded=false;lossOverlayVisible=false;dismissedLossToken=null;pendingPromotion=null;hideStartCountdown();const overlay=document.getElementById("lossOverlay");if(overlay)overlay.classList.remove("show");const promotionPanel=document.getElementById("promotionPanel");if(promotionPanel)promotionPanel.classList.remove("show");clearPromotionTarget();showPlayerStartGlow=true;if(playerGlowTimer)clearTimeout(playerGlowTimer);playerGlowTimer=setTimeout(()=>{showPlayerStartGlow=false;buildBoard(false)},1000);currentTimerInitialSeconds=Math.max(1,Number(args.timer_initial_seconds||10));currentTimerIncrementSeconds=Math.max(0,Number(args.timer_increment_seconds||0));timerIncrementMs=currentTimerIncrementSeconds*1000;remainingMs=currentTimerInitialSeconds*1000;timerTimeoutSent=false;if(timerInterval){clearInterval(timerInterval);timerInterval=null}updateTimerDisplay();buildBoard(true);if(previewMode){updateStatus("Ready board — choose 10-round or unlimited.");return}
const shouldCountdown=currentRoundNumber===1;
if(shouldCountdown){
    startRoundCountdown(()=>{startTimer(currentTimerInitialSeconds);updateStatus();if(isEngineTurn())setTimeout(()=>startEngineMove(),250)});
}else{
    hideStartCountdown();
    startTimer(currentTimerInitialSeconds);
    updateStatus();
    if(isEngineTurn())setTimeout(()=>startEngineMove(),250);
}
}
window.addEventListener("message",event=>{
    if(event.data.type!=="streamlit:render")return;
    const args=event.data.args;
    if(currentToken!==args.round_token||currentFen!==args.fen)initPosition(args);
    else {
        soundEnabled=args.sound_enabled!==false;
        const nextElo=Math.max(800,Math.min(3200,Number(args.stockfish_elo||800)));
        const nextSkill=Math.max(0,Math.min(20,Number(args.stockfish_skill||0)));
        if(nextElo!==currentStockfishElo||nextSkill!==currentStockfishSkill){
            currentStockfishElo=nextElo;
            currentStockfishSkill=nextSkill;
            configureStockfishStrength();
            if(engineReady&&!engineFallback)reportEngineStatus("Stockfish connected","Using Stockfish at Gauntlet Elo "+currentStockfishElo,true);
        }
        const nextTimer=Math.max(1,Number(args.timer_initial_seconds||10));
        const nextIncrement=Math.max(0,Number(args.timer_increment_seconds||0));
        if(nextIncrement!==currentTimerIncrementSeconds){
            currentTimerIncrementSeconds=nextIncrement;
            timerIncrementMs=currentTimerIncrementSeconds*1000;
        }
        if(nextTimer!==currentTimerInitialSeconds){
            currentTimerInitialSeconds=nextTimer;
            remainingMs=currentTimerInitialSeconds*1000;
            timerTimeoutSent=false;
            lastTickMs=Date.now();
            updateTimerDisplay();
        }
    }
    if(args.round_result==="loss"&&dismissedLossToken!==args.round_token&&!lossOverlayVisible){
        showLossOverlay(args.round_result_detail||"You lost the round.");
    }
});
document.addEventListener("pointerdown",unlockAudio);document.addEventListener("click",unlockAudio);
document.addEventListener("contextmenu",ev=>{
    if(ev.target.closest("#board")){
        ev.preventDefault();
        ev.stopPropagation();
        return false;
    }
});
document.addEventListener("mousemove",ev=>{updateBoardArrow(ev);updateCustomPieceDrag(ev)});
document.addEventListener("mousedown",ev=>{
    if(ev.button===0&&!ev.target.closest("#board")){
        clearBoardAnnotations();
    }
});
document.addEventListener("mouseup",ev=>{
    if(ev.button===2){
        finishBoardArrow(ev);
    }
    if(ev.button===0){
        if(customPieceDragActive){
            finishCustomPieceDrag(ev);
        }else if(!draggedFrom){
            setDraggingCursor(false);
            clearDragHover();
        }
    }
});
document.addEventListener("dragover",ev=>{rememberDragPoint(ev);squareFromClientPoint(lastDragClientX,lastDragClientY)});
document.addEventListener("drop",ev=>{rememberDragPoint(ev);finishDragAtPoint(ev)});
document.addEventListener("dragend",ev=>finishDragAtPoint(ev));
document.addEventListener("keydown",ev=>{
    if(ev.key==="ArrowLeft"){ev.preventDefault();navigateMove(-1)}
    if(ev.key==="ArrowRight"){ev.preventDefault();navigateMove(1)}
});
initStockfishWorker();setComponentReady();setFrameHeight(790);
</script>
</body>
</html>
"""


def create_component():
    COMPONENT_DIR.mkdir(exist_ok=True)
    COMPONENT_FILE.write_text(COMPONENT_HTML, encoding="utf-8")


def create_time_input_component():
    TIME_INPUT_DIR.mkdir(exist_ok=True)
    TIME_INPUT_FILE.write_text(TIME_INPUT_HTML, encoding="utf-8")


create_component()
create_time_input_component()

browser_board = components.declare_component("browser_chess_component", path=str(COMPONENT_DIR))
instant_time_input = components.declare_component("instant_time_component", path=str(TIME_INPUT_DIR))


def ensure_positions_file():
    if not POSITIONS_FILE.exists():
        POSITIONS_FILE.write_text(json.dumps(DEFAULT_POSITIONS, indent=4), encoding="utf-8")


def normalize_positions(data):
    if not isinstance(data, list):
        return []

    valid = []

    for item in data:
        if not isinstance(item, dict):
            continue

        fen = item.get("fen")

        if not fen:
            continue

        try:
            board = chess.Board(fen)
        except ValueError:
            continue

        item = item.copy()
        item.setdefault("id", f"position_{len(valid)+1}")
        item.setdefault("title", item["id"])
        item.setdefault("opponent", item.get("master_name", "Unknown Opponent"))
        item.setdefault("year", "")
        item.setdefault("player_color", "white" if board.turn == chess.WHITE else "black")
        item.setdefault("difficulty", 1)
        item.setdefault("goal", "win")
        item.setdefault("intro", "")
        item.setdefault("source", "")

        valid.append(item)

    return valid


def load_positions():
    ensure_positions_file()

    try:
        data = json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
    except Exception as error:
        st.error(f"Could not read positions.json: {error}")
        return []

    if not isinstance(data, list):
        st.error("positions.json must contain a list of positions.")
        return []

    return normalize_positions(data)



def load_master_tournament_positions():
    if not MASTER_TOURNAMENT_FILE.exists():
        return []

    try:
        data = json.loads(MASTER_TOURNAMENT_FILE.read_text(encoding="utf-8"))
    except Exception as error:
        st.error(f"Could not read master_tournament_positions.json: {error}")
        return []

    if not isinstance(data, list):
        st.error("master_tournament_positions.json must contain a list of positions.")
        return []

    positions = normalize_positions(data)

    # Shuffle immediately so the app never treats the JSON file order as the tournament order.
    random.SystemRandom().shuffle(positions)

    return positions


def is_master_tournament_mode():
    return st.session_state.get("game_mode") == "master_tournament"


def mode_label():
    if is_unlimited_mode():
        return "Unlimited"

    if is_master_tournament_mode():
        return "Master Tournament"

    return "10-Round"


def master_position_key(position):
    # What matters visually is the board, so use FEN first.
    return position.get("fen") or position.get("id") or position.get("title", "")


def unique_master_positions(master_positions):
    seen = set()
    unique = []

    for position in master_positions:
        key = master_position_key(position)

        if not key or key in seen:
            continue

        seen.add(key)
        unique.append(position)

    return unique


def load_recent_master_openers():
    recent = list(st.session_state.get("master_tournament_recent_openers", []))

    if MASTER_RECENT_OPENERS_FILE.exists():
        try:
            data = json.loads(MASTER_RECENT_OPENERS_FILE.read_text(encoding="utf-8"))

            if isinstance(data, list):
                for item in data:
                    if item and item not in recent:
                        recent.append(str(item))
        except Exception:
            pass

    return recent[-75:]


def save_recent_master_openers(recent_openers):
    cleaned = [str(item) for item in recent_openers if item][-75:]
    st.session_state.master_tournament_recent_openers = cleaned

    try:
        MASTER_RECENT_OPENERS_FILE.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    except Exception:
        pass


def make_master_tournament_batch(master_positions):
    """
    Master Tournament should feel like the other modes:
    grab a random position from the whole collection every time.

    No bucket-first logic. No round-1-first logic.
    Just thousands of Lichess positions -> random opening board -> 9 more random boards.
    """
    unique_positions = unique_master_positions(master_positions)

    if not unique_positions:
        return []

    rng = random.SystemRandom()
    recent_openers = load_recent_master_openers()
    recent_set = set(recent_openers)

    fresh_openers = [
        position for position in unique_positions
        if master_position_key(position) not in recent_set
    ]

    if not fresh_openers:
        recent_openers = []
        fresh_openers = unique_positions.copy()

    opener = rng.choice(fresh_openers)
    opener_key = master_position_key(opener)

    remaining = [
        position for position in unique_positions
        if master_position_key(position) != opener_key
    ]

    rng.shuffle(remaining)

    selected = [opener] + remaining[:9]

    while len(selected) < 10 and unique_positions:
        selected.append(rng.choice(unique_positions))

    if opener_key:
        recent_openers.append(opener_key)
        save_recent_master_openers(recent_openers[-75:])
        st.session_state.master_tournament_last_first_id = opener_key

    return selected[:10]


def master_tournament_unique_count(master_positions):
    return len(unique_master_positions(master_positions))


def master_tournament_opening_pool_message(master_positions):
    unique_count = master_tournament_unique_count(master_positions)

    if unique_count <= 1:
        return "Only 1 unique starting board found. Rebuild the puzzle file."

    return f"{unique_count} unique boards. Start is picked from the full pool."


def format_time_limit_label(seconds):
    seconds = max(1, int(seconds))
    minutes = seconds // 60
    remainder = seconds % 60
    return f"{minutes}:{remainder:02d}.0"


def init_state():
    defaults = {
        "game_active": False,
        "game_completed": False,
        "game_positions": [],
        "current_round_index": 0,
        "score": 0.0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "round_result": None,
        "round_result_detail": "",
        "round_history": [],
        "round_fen": "",
        "round_token": 0,
        "sound_enabled": True,
        "engine_move_time_ms": 2100,
        "time_limit_seconds": 10,
        "increment_seconds": 0.0,
        "last_nonce": None,
        "game_mode": "ten_round",
        "position_bank": [],
        "preview_position": None,

        # Rating ladder state
        "player_rating": 800,
        "best_rating": 800,
        "highest_title_key": "none",
        "current_streak": 0,
        "best_streak": 0,
        "total_ladder_rounds": 0,
        "current_challenge": None,
        "last_rating_change": None,
        "pending_title_popup": None,

        # Engine visibility/strength state
        "engine_status": "Checking Stockfish...",
        "engine_detail": "Waiting for browser engine.",
        "engine_is_stockfish": False,
        "last_engine_elo": 800,
        "last_engine_skill": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



TITLE_LADDER = [
    {
        "key": "amateur",
        "short": "Amateur",
        "full": "Amateur",
        "rating": 1000,
        "message": "The ladder begins now.",
    },
    {
        "key": "cm",
        "short": "CM",
        "full": "Candidate Master",
        "rating": 1400,
        "message": "You are no longer surviving the gauntlet. You are climbing it.",
    },
    {
        "key": "fm",
        "short": "FM",
        "full": "FIDE Master",
        "rating": 1750,
        "message": "The odds are getting thinner. The clock is getting crueler.",
    },
    {
        "key": "im",
        "short": "IM",
        "full": "International Master",
        "rating": 2100,
        "message": "Every premove matters now.",
    },
    {
        "key": "gm",
        "short": "GM",
        "full": "Grandmaster",
        "rating": 2450,
        "message": "Only the final ladder remains.",
    },
    {
        "key": "super_gm",
        "short": "SUPER GM",
        "full": "Super Grandmaster",
        "rating": 2800,
        "message": "You have beaten the gauntlet. Now chase the highest rating possible.",
    },
]

TITLE_RANKS = {"none": 0}
for index, title in enumerate(TITLE_LADDER, start=1):
    TITLE_RANKS[title["key"]] = index


def title_for_rating(rating):
    unlocked = None

    for title in TITLE_LADDER:
        if rating >= title["rating"]:
            unlocked = title

    return unlocked


def current_title_info():
    key = st.session_state.get("highest_title_key", "none")

    for title in TITLE_LADDER:
        if title["key"] == key:
            return title

    return {
        "key": "none",
        "short": "Unrated",
        "full": "Unrated",
        "rating": 800,
        "message": "",
    }


def next_title_info():
    current_rank = TITLE_RANKS.get(st.session_state.get("highest_title_key", "none"), 0)

    for title in TITLE_LADDER:
        if TITLE_RANKS[title["key"]] > current_rank:
            return title

    return None


def overall_ladder_progress_percent():
    rating = int(st.session_state.player_rating)
    return max(0, min(100, int(((rating - 800) / (2800 - 800)) * 100)))


def left_ladder_tick_html():
    rating = int(st.session_state.player_rating)
    ticks = [{"short": "Start", "rating": 800}] + [
        {"short": title["short"], "rating": title["rating"]}
        for title in TITLE_LADDER
    ]
    html_parts = []

    for tick in ticks:
        pct = max(0, min(100, ((tick["rating"] - 800) / (2800 - 800)) * 100))
        unlocked = " unlocked" if rating >= tick["rating"] else ""
        label = f"{tick['short']} {tick['rating']}"
        html_parts.append(
            f'<div class="left-ladder-tick{unlocked}" '
            f'data-label="{label}" style="bottom:{pct:.2f}%"></div>'
        )

    return "\n".join(html_parts)


def rating_progress_percent():
    rating = int(st.session_state.player_rating)
    current = current_title_info()
    next_title = next_title_info()

    if not next_title:
        return 100

    start = current["rating"] if current["key"] != "none" else 800
    end = next_title["rating"]

    if end <= start:
        return 100

    return max(0, min(100, int(((rating - start) / (end - start)) * 100)))


def tier_from_rating(rating):
    if rating < 1000:
        return "Amateur Climb"

    if rating < 1400:
        return "Candidate Master Climb"

    if rating < 1750:
        return "FIDE Master Climb"

    if rating < 2100:
        return "International Master Climb"

    if rating < 2450:
        return "Grandmaster Climb"

    if rating < 2800:
        return "Super GM Climb"

    return "Endless Legend"


def base_time_for_rating(rating, boss=False):
    if rating < 1000:
        seconds = 10
    elif rating < 1400:
        seconds = 9
    elif rating < 1750:
        seconds = 8
    elif rating < 2100:
        seconds = 7
    elif rating < 2450:
        seconds = 6
    elif rating < 2800:
        seconds = 5
    else:
        seconds = 4

    if boss:
        seconds = max(3, seconds - 2)

    return seconds


def choose_round_type(rating, boss=False):
    if boss:
        return random.choice([
            "Boss Round: Cruel Conversion",
            "Boss Round: Mate Rush",
            "Boss Round: Premove Sprint",
        ])

    if rating < 1000:
        return random.choice([
            "Big Material Conversion",
            "Mate in Low Time",
            "Passed Pawn Sprint",
        ])

    if rating < 1400:
        return random.choice([
            "Rook-Up Conversion",
            "Mate Rush",
            "Promotion Race",
            "Premove Sprint",
        ])

    if rating < 1750:
        return random.choice([
            "Small Material Edge",
            "Mate Net",
            "Queen vs Defense",
            "Premove Sprint",
        ])

    if rating < 2100:
        return random.choice([
            "Precise Endgame",
            "Hard Mate Rush",
            "Tiny Time Conversion",
            "Rook Endgame Pressure",
        ])

    if rating < 2450:
        return random.choice([
            "GM Precision Test",
            "Mate in Chaos",
            "Minimal Odds",
            "Low-Time Conversion",
        ])

    return random.choice([
        "Super GM Survival",
        "Almost No Odds",
        "Brutal Premove Sprint",
        "Final Boss Conversion",
    ])


def challenge_description(round_type):
    if "Mate" in round_type:
        return "Find the forcing idea before the clock disappears."

    if "Premove" in round_type:
        return "Win with speed. Clean premoves matter more than calculation."

    if "Promotion" in round_type:
        return "Race the pawn, queen cleanly, and finish the job."

    if "Boss" in round_type:
        return "A checkpoint round. Bigger reward, tougher odds."

    if "Rook" in round_type:
        return "Convert the edge while Stockfish tries to stall everything."

    if "Minimal" in round_type or "Almost" in round_type:
        return "Tiny odds, brutal clock, no wasted moves."

    return "Convert the odds against Stockfish before time runs out."


def generate_challenge(round_number=None):
    rating = int(st.session_state.player_rating)
    round_number = int(round_number or current_round_number())
    boss = round_number % 9 == 0

    if boss:
        offset = random.choice([120, 160, 200, 240])
    else:
        offset = random.choice([-90, -50, -20, 0, 40, 70, 100, 130])

    # Let the ladder naturally get harder over long runs, but keep it sane.
    long_run_pressure = min(160, max(0, (round_number - 1) // 12 * 20))
    challenge_rating = max(700, int(rating + offset + long_run_pressure))
    round_type = choose_round_type(rating, boss=boss)
    seconds = base_time_for_rating(rating, boss=boss)

    return {
        "round": round_number,
        "challenge_rating": challenge_rating,
        "round_type": round_type,
        "description": challenge_description(round_type),
        "time_seconds": seconds,  # suggested/generated odds time; user timer overrides clock
        "boss": boss,
        "tier": tier_from_rating(rating),
    }


def current_round_time_seconds():
    # User-controlled time applies to every mode, including Master Tournament.
    # Master Tournament starts at 60 by default, but players can change it anytime.
    return max(1, int(st.session_state.time_limit_seconds))


def current_round_increment_seconds():
    return max(0.0, min(60.0, float(st.session_state.increment_seconds)))


def apply_time_input_value(value):
    if not value or not isinstance(value, dict):
        return False

    action = value.get("action")

    if action == "set_time_limit":
        try:
            seconds = int(float(value.get("seconds", value.get("value", st.session_state.time_limit_seconds))))
        except (TypeError, ValueError):
            return False

        seconds = max(1, min(999, seconds))

        if seconds == int(st.session_state.time_limit_seconds):
            return False

        st.session_state.time_limit_seconds = seconds
        return True

    if action == "set_increment":
        try:
            increment = float(value.get("increment", value.get("value", st.session_state.increment_seconds)))
        except (TypeError, ValueError):
            return False

        increment = round(max(0.0, min(60.0, increment)), 1)

        if abs(increment - float(st.session_state.increment_seconds)) < 0.0001:
            return False

        st.session_state.increment_seconds = increment
        return True

    return False



def stockfish_elo_for_current_round():
    """Gauntlet-facing engine strength. Starts near 800 and climbs gradually."""
    if is_master_tournament_mode() and current_position():
        try:
            return max(800, min(3200, int(current_position().get("engine_elo", 1600))))
        except (TypeError, ValueError):
            return 1600

    rating = int(st.session_state.player_rating)
    challenge = st.session_state.current_challenge or {}
    challenge_rating = int(challenge.get("challenge_rating", rating))
    boss_bonus = 75 if challenge.get("boss") else 0
    round_pressure = min(220, max(0, (current_round_number() - 1) // 9 * 25))

    # Blend player rating and challenge rating so the engine climbs slowly but consistently.
    elo = int((rating * 0.65) + (challenge_rating * 0.35) + boss_bonus + round_pressure)
    return max(800, min(3200, elo))


def stockfish_skill_for_elo(elo):
    """Map the visible 800-3200 ladder to Stockfish Skill Level 0-20."""
    elo = max(800, min(3200, int(elo)))
    return max(0, min(20, round((elo - 800) / (3200 - 800) * 20)))


def expected_score_against(player_rating, challenge_rating):
    return 1 / (1 + 10 ** ((challenge_rating - player_rating) / 400))


def calculate_rating_delta(result, challenge):
    player_rating = int(st.session_state.player_rating)
    challenge_rating = int(challenge.get("challenge_rating", player_rating))
    expected = expected_score_against(player_rating, challenge_rating)
    boss = bool(challenge.get("boss"))
    k = 44 + (10 if boss else 0)

    if result == "win":
        base = round(k * (1 - expected))
        streak_bonus = min(25, max(0, (st.session_state.current_streak - 1) * 2))
        boss_bonus = 8 if boss else 0
        return max(8, min(55, base + streak_bonus + boss_bonus))

    if result == "draw":
        # A draw is usually not the goal, but against brutal odds it should not feel useless.
        delta = round(k * (0.5 - expected) * 0.55)
        return max(-8, min(14, delta))

    # Losing hard/equal rounds is not punished too brutally.
    loss = round(k * expected * 0.70)
    return -max(6, min(22, loss))


def update_rating_after_round(result, challenge):
    old_rating = int(st.session_state.player_rating)

    if result == "win":
        st.session_state.current_streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.current_streak)
    else:
        st.session_state.current_streak = 0

    delta = calculate_rating_delta(result, challenge)
    new_rating = max(100, old_rating + delta)

    st.session_state.player_rating = new_rating
    st.session_state.best_rating = max(int(st.session_state.best_rating), new_rating)
    st.session_state.total_ladder_rounds += 1

    st.session_state.last_rating_change = {
        "old_rating": old_rating,
        "new_rating": new_rating,
        "delta": delta,
        "result": result,
        "challenge": challenge.copy() if isinstance(challenge, dict) else {},
    }

    newly_unlocked = title_for_rating(new_rating)

    if newly_unlocked:
        current_rank = TITLE_RANKS.get(st.session_state.highest_title_key, 0)
        new_rank = TITLE_RANKS.get(newly_unlocked["key"], 0)

        if new_rank > current_rank:
            st.session_state.highest_title_key = newly_unlocked["key"]
            st.session_state.pending_title_popup = newly_unlocked.copy()

    return delta


def win_points_preview(challenge):
    old_streak = st.session_state.current_streak
    st.session_state.current_streak += 1
    try:
        delta = calculate_rating_delta("win", challenge)
    finally:
        st.session_state.current_streak = old_streak
    return delta


def loss_points_preview(challenge):
    return calculate_rating_delta("loss", challenge)


def make_position_batch(positions, count):
    if not positions:
        return []

    if len(positions) >= count:
        return random.sample(positions, count)

    selected = positions.copy()

    while len(selected) < count:
        selected.append(random.choice(positions))

    random.shuffle(selected)
    return selected


def get_preview_position(positions):
    if not positions:
        return None

    preview = st.session_state.get("preview_position")

    if isinstance(preview, dict) and preview.get("fen"):
        return preview

    st.session_state.preview_position = random.choice(positions)
    return st.session_state.preview_position


def is_unlimited_mode():
    return st.session_state.get("game_mode") == "unlimited"


def refill_unlimited_positions_if_needed():
    if not is_unlimited_mode():
        return

    if not st.session_state.game_active:
        return

    bank = st.session_state.get("position_bank", [])

    if not bank:
        return

    # Keep extra rounds loaded so the game never reaches a hard end.
    if len(st.session_state.game_positions) - st.session_state.current_round_index <= 5:
        st.session_state.game_positions.extend(make_position_batch(bank, 50))


def current_position():
    refill_unlimited_positions_if_needed()

    if st.session_state.game_active and st.session_state.game_positions:
        if st.session_state.current_round_index >= len(st.session_state.game_positions):
            refill_unlimited_positions_if_needed()

        if st.session_state.current_round_index < len(st.session_state.game_positions):
            return st.session_state.game_positions[st.session_state.current_round_index]

    return None


def current_round_number():
    return st.session_state.current_round_index + 1


def total_rounds():
    if is_unlimited_mode():
        return "∞"

    return len(st.session_state.game_positions) if st.session_state.game_positions else 10


def player_rank_title():
    score = st.session_state.score

    if score >= 25:
        return "Endless Legend"

    if score >= 15:
        return "Premove Machine"

    if score >= 10:
        return "Legend Killer"

    if score >= 8:
        return "Master Survivor"

    if score >= 6:
        return "Endgame Specialist"

    if score >= 3:
        return "Club Fighter"

    return "Pawn Recruit"


def reset_run_stats(mode, positions):
    st.session_state.current_round_index = 0
    st.session_state.score = 0.0
    st.session_state.wins = 0
    st.session_state.draws = 0
    st.session_state.losses = 0
    st.session_state.round_result = None
    st.session_state.round_result_detail = ""
    st.session_state.round_history = []
    st.session_state.round_fen = ""
    st.session_state.round_token += 1
    st.session_state.game_active = True
    st.session_state.game_completed = False
    st.session_state.game_mode = mode
    st.session_state.position_bank = positions.copy()
    st.session_state.current_challenge = generate_challenge(1)
    st.session_state.last_rating_change = None


def start_game(positions, mode="ten_round"):
    if not positions:
        st.warning("No positions found. Add positions to positions.json first.")
        return

    if mode == "unlimited":
        # Start with enough loaded rounds, then refill forever as the player advances.
        selected = make_position_batch(positions, 50)
    else:
        selected = make_position_batch(positions, 10)

    st.session_state.game_positions = selected
    reset_run_stats(mode, positions)


def start_master_tournament(master_positions=None):
    # Reload from disk every time and throw away the current game before building a new one.
    master_positions = load_master_tournament_positions()

    if not master_positions:
        st.warning("No Master Tournament positions found. Run build_master_tournament_positions.py first.")
        return

    unique_count = master_tournament_unique_count(master_positions)

    if unique_count <= 1:
        st.warning(
            "Only one unique Master Tournament starting board exists in master_tournament_positions.json. "
            "Rebuild it with more positions to get true variety."
        )

    selected = make_master_tournament_batch(master_positions)
    st.session_state.master_tournament_first_position_key = master_position_key(selected[0]) if selected else ""

    if len(selected) < 10:
        st.warning("Master Tournament needs more unique positions. Run the builder again with a larger pool.")
        return

    # Force the old board/game state out before the new randomized tournament starts.
    st.session_state.game_positions = []
    st.session_state.current_round_index = 0
    st.session_state.round_result = None
    st.session_state.round_result_detail = ""
    st.session_state.round_history = []
    st.session_state.round_fen = ""

    # Standard tournament clock is 60 seconds, but the Time Control box can adjust it.
    st.session_state.time_limit_seconds = 60
    st.session_state.increment_seconds = 0.0
    st.session_state.game_positions = selected
    reset_run_stats("master_tournament", master_positions)


def abandon_game():
    st.session_state.game_active = False
    st.session_state.game_completed = False
    st.session_state.game_positions = []
    st.session_state.position_bank = []
    st.session_state.current_round_index = 0
    st.session_state.round_result = None
    st.session_state.round_result_detail = ""
    st.session_state.round_history = []
    st.session_state.round_fen = ""
    st.session_state.current_challenge = None
    st.session_state.round_token += 1


def advance_to_next_round():
    if not st.session_state.game_active:
        return

    if is_unlimited_mode():
        refill_unlimited_positions_if_needed()

        if st.session_state.current_round_index + 1 >= len(st.session_state.game_positions):
            bank = st.session_state.get("position_bank", [])
            st.session_state.game_positions.extend(make_position_batch(bank, 50))

        st.session_state.current_round_index += 1
    else:
        if st.session_state.current_round_index + 1 >= len(st.session_state.game_positions):
            st.session_state.game_active = False
            st.session_state.game_completed = True
            st.session_state.current_challenge = None
            return

        st.session_state.current_round_index += 1

    st.session_state.round_result = None
    st.session_state.round_result_detail = ""
    st.session_state.round_history = []
    st.session_state.round_fen = ""
    st.session_state.current_challenge = generate_challenge(st.session_state.current_round_index + 1)
    st.session_state.round_token += 1


def next_round():
    if not st.session_state.game_active:
        return

    if st.session_state.round_result is None:
        st.warning("Finish the current round before moving to the next one.")
        return

    advance_to_next_round()


def apply_component_value(value):
    if not value or not isinstance(value, dict):
        return False

    nonce = value.get("nonce")

    if not nonce or nonce == st.session_state.last_nonce:
        return False

    st.session_state.last_nonce = nonce

    action = value.get("action")

    if action == "engine_status":
        previous = (
            st.session_state.engine_status,
            st.session_state.engine_detail,
            st.session_state.engine_is_stockfish,
            st.session_state.last_engine_elo,
            st.session_state.last_engine_skill,
        )

        st.session_state.engine_status = value.get("status", st.session_state.engine_status)
        st.session_state.engine_detail = value.get("detail", st.session_state.engine_detail)
        st.session_state.engine_is_stockfish = bool(value.get("stockfish", False))

        try:
            st.session_state.last_engine_elo = int(value.get("elo", st.session_state.last_engine_elo))
            st.session_state.last_engine_skill = int(value.get("skill", st.session_state.last_engine_skill))
        except (TypeError, ValueError):
            pass

        current = (
            st.session_state.engine_status,
            st.session_state.engine_detail,
            st.session_state.engine_is_stockfish,
            st.session_state.last_engine_elo,
            st.session_state.last_engine_skill,
        )
        return current != previous

    if action == "start_game":
        mode = value.get("mode", "ten_round")

        if mode == "master_tournament":
            master_positions = globals().get("master_tournament_positions") or load_master_tournament_positions()
            start_master_tournament(master_positions)
            return True

        if mode not in {"ten_round", "unlimited"}:
            mode = "ten_round"

        start_positions = globals().get("positions") or st.session_state.get("position_bank") or load_positions()
        start_game(start_positions, mode=mode)
        return True

    if action != "round_result":
        return False

    # The ready board is always visible, but it should not count as a real run.
    if not st.session_state.game_active:
        return False

    if st.session_state.round_result is not None:
        return False

    result = value.get("result", "loss")
    detail = value.get("detail", "")

    if result == "draw":
        result = "loss"
        detail = detail or "Game drawn. Draws count as losses."

    st.session_state.round_result = result
    st.session_state.round_result_detail = detail
    st.session_state.round_history = value.get("history", [])
    st.session_state.round_fen = value.get("fen", "")

    challenge = st.session_state.current_challenge or generate_challenge(current_round_number())
    update_rating_after_round(result, challenge)

    if result == "win":
        st.session_state.score += 1
        st.session_state.wins += 1
    elif result == "draw":
        st.session_state.score += 0.5
        st.session_state.draws += 1
    else:
        st.session_state.losses += 1

    # Wins immediately move the player to the next round.
    # In unlimited mode, this keeps going forever.
    # Losses/draws stay on the result screen so the player can see what happened.
    if result == "win" and st.session_state.game_active:
        advance_to_next_round()

    return True


init_state()

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        scroll-behavior: auto !important;
        overflow-anchor: none !important;
    }

    .stApp {
        background:
            radial-gradient(circle at 16% 0%, rgba(176,190,212,.18), transparent 32%),
            radial-gradient(circle at 92% 10%, rgba(126,158,190,.14), transparent 30%),
            linear-gradient(135deg, #334255 0%, #26364a 42%, #1b2940 100%);
        color: #eef2ff;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            linear-gradient(145deg, rgba(255,255,255,.085) 0 1px, transparent 1px 100%),
            linear-gradient(145deg, transparent 0 13%, rgba(255,255,255,.055) 13% 13.2%, transparent 13.2% 100%),
            linear-gradient(325deg, transparent 0 72%, rgba(255,255,255,.050) 72% 72.2%, transparent 72.2% 100%);
        opacity: .75;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 16% 0%, rgba(176,190,212,.18), transparent 32%),
            radial-gradient(circle at 92% 10%, rgba(126,158,190,.14), transparent 30%),
            linear-gradient(135deg, #334255 0%, #26364a 42%, #1b2940 100%);
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: min(1520px, calc(100vw - 36px)) !important;
        padding-top: 3.25rem !important;
        padding-bottom: 2rem !important;
        position: relative;
        z-index: 1;
    }

    .gauntlet-hero {
        position: relative;
        min-height: 176px;
        display: flex;
        align-items: center;
        gap: 28px;
        margin: 0 auto 24px auto;
        padding: 26px 44px;
        overflow: hidden;
        border-radius: 6px;
        border: 1px solid rgba(210, 170, 122, .55);
        background:
            radial-gradient(circle at 18% 50%, rgba(129, 72, 255, .18), transparent 22%),
            radial-gradient(circle at 74% 42%, rgba(147, 90, 255, .18), transparent 30%),
            linear-gradient(90deg, rgba(8, 17, 36, .97) 0%, rgba(17, 25, 49, .96) 42%, rgba(30, 32, 70, .94) 72%, rgba(10, 19, 38, .98) 100%);
        box-shadow:
            0 24px 65px rgba(0,0,0,.32),
            inset 0 1px 0 rgba(255,255,255,.06),
            inset 0 0 0 2px rgba(255,220,180,.03);
    }
    .gauntlet-hero::before {
        content: "";
        position: absolute;
        inset: 11px;
        border: 1px solid rgba(216, 180, 136, .42);
        border-radius: 3px;
        pointer-events: none;
        box-shadow:
            inset 0 0 0 1px rgba(115, 87, 156, .24),
            0 0 34px rgba(151, 99, 255, .10);
    }
    .gauntlet-hero::after {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(180deg, rgba(255,255,255,.04), transparent 35%, rgba(255,255,255,.02) 100%),
            radial-gradient(circle at 68% 47%, rgba(255, 196, 109, .11), transparent 15%),
            radial-gradient(circle at 57% 38%, rgba(124, 85, 255, .16), transparent 26%);
        opacity: .9;
        pointer-events: none;
    }
    .hero-inner-frame {
        position: absolute;
        inset: 20px;
        border: 1px solid rgba(173, 136, 97, .22);
        border-radius: 2px;
        pointer-events: none;
        z-index: 1;
    }
    .hero-ornament {
        position: absolute;
        width: 66px;
        height: 66px;
        pointer-events: none;
        z-index: 2;
        opacity: .95;
    }
    .hero-ornament::before,
    .hero-ornament::after {
        content: "";
        position: absolute;
        border-color: rgba(202, 165, 120, .72);
        filter: drop-shadow(0 0 8px rgba(221, 176, 108, .18));
    }
    .hero-ornament.tl { top: 6px; left: 6px; }
    .hero-ornament.tr { top: 6px; right: 6px; }
    .hero-ornament.bl { bottom: 6px; left: 6px; }
    .hero-ornament.br { bottom: 6px; right: 6px; }
    .hero-ornament.tl::before,
    .hero-ornament.bl::before {
        left: 0; top: 0; width: 48px; height: 26px;
        border-top: 2px solid rgba(202, 165, 120, .78);
        border-left: 2px solid rgba(202, 165, 120, .78);
        border-top-left-radius: 24px;
    }
    .hero-ornament.tl::after,
    .hero-ornament.bl::after {
        left: 0; top: 0; width: 22px; height: 48px;
        border-top: 1px solid rgba(202, 165, 120, .68);
        border-left: 1px solid rgba(202, 165, 120, .68);
        border-top-left-radius: 18px;
    }
    .hero-ornament.tr::before,
    .hero-ornament.br::before {
        right: 0; top: 0; width: 48px; height: 26px;
        border-top: 2px solid rgba(202, 165, 120, .78);
        border-right: 2px solid rgba(202, 165, 120, .78);
        border-top-right-radius: 24px;
    }
    .hero-ornament.tr::after,
    .hero-ornament.br::after {
        right: 0; top: 0; width: 22px; height: 48px;
        border-top: 1px solid rgba(202, 165, 120, .68);
        border-right: 1px solid rgba(202, 165, 120, .68);
        border-top-right-radius: 18px;
    }
    .hero-ornament.bl::before { top: auto; bottom: 0; border-top: none; border-bottom: 2px solid rgba(202,165,120,.78); border-top-left-radius: 0; border-bottom-left-radius: 24px; }
    .hero-ornament.bl::after { top: auto; bottom: 0; border-top: none; border-bottom: 1px solid rgba(202,165,120,.68); border-top-left-radius: 0; border-bottom-left-radius: 18px; }
    .hero-ornament.br::before { top: auto; bottom: 0; border-top: none; border-bottom: 2px solid rgba(202,165,120,.78); border-top-right-radius: 0; border-bottom-right-radius: 24px; }
    .hero-ornament.br::after { top: auto; bottom: 0; border-top: none; border-bottom: 1px solid rgba(202,165,120,.68); border-top-right-radius: 0; border-bottom-right-radius: 18px; }
    .gauntlet-icon {
        position: relative;
        z-index: 3;
        width: 118px;
        height: 118px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 86px;
        color: #c093ff;
        background:
            radial-gradient(circle at 50% 46%, rgba(188, 130, 255, .34), transparent 34%),
            radial-gradient(circle at 50% 50%, rgba(9, 14, 33, .92), rgba(11, 18, 40, .62) 56%, transparent 57%),
            conic-gradient(from 0deg, rgba(217,176,145,.12), rgba(154,101,255,.38), rgba(217,176,145,.12), rgba(154,101,255,.24), rgba(217,176,145,.12));
        border: 1px solid rgba(222, 178, 142, .38);
        text-shadow:
            0 0 18px rgba(182, 121, 255, .92),
            0 12px 26px rgba(0,0,0,.36);
        box-shadow:
            0 18px 38px rgba(0,0,0,.38),
            inset 0 1px 0 rgba(255,255,255,.10),
            0 0 48px rgba(124, 71, 255, .24);
    }
    .gauntlet-icon::before {
        content: "";
        position: absolute;
        inset: -14px;
        border-radius: 50%;
        border: 1px solid rgba(222, 178, 142, .20);
        box-shadow: inset 0 0 22px rgba(151,99,255,.18);
    }
    .gauntlet-copy {
        position: relative;
        z-index: 3;
        min-width: 520px;
    }
    .gauntlet-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 4.25rem;
        line-height: 1.0;
        font-weight: 700;
        letter-spacing: -0.035em;
        margin: 0;
        color: #f4ead4;
        text-shadow:
            0 2px 0 rgba(44, 31, 19, .75),
            0 5px 18px rgba(0,0,0,.45),
            0 0 24px rgba(255, 232, 180, .12);
    }
    .gauntlet-subtitle {
        margin-top: 14px;
        color: #eadfc7;
        font-size: 1.15rem;
        line-height: 1.35;
        text-shadow: 0 2px 10px rgba(0,0,0,.36);
    }
    .hero-glow {
        position: absolute;
        right: 80px;
        top: -18px;
        width: 420px;
        height: 220px;
        border-radius: 999px;
        background:
            radial-gradient(circle at 35% 50%, rgba(255, 198, 120, .10), transparent 18%),
            radial-gradient(circle at 55% 50%, rgba(137, 88, 255, .18), rgba(137, 88, 255, .08) 32%, transparent 62%),
            radial-gradient(circle at 76% 52%, rgba(96, 63, 196, .18), transparent 28%);
        filter: blur(4px);
        z-index: 0;
        pointer-events: none;
        opacity: .9;
    }

    .hero-major-pieces {
        position: absolute;
        right: 28px;
        top: 18px;
        bottom: 18px;
        width: 41%;
        display: flex;
        align-items: flex-end;
        justify-content: space-evenly;
        gap: 10px;
        padding: 0 18px 6px 18px;
        z-index: 1;
        pointer-events: none;
        opacity: .88;
    }
    .hero-major-pieces::before {
        content: "";
        position: absolute;
        inset: 6px 2px 10px 2px;
        background:
            radial-gradient(circle at 42% 46%, rgba(173, 105, 255, .18), transparent 24%),
            linear-gradient(135deg, rgba(255,255,255,.06), transparent 30%),
            linear-gradient(90deg, rgba(7, 13, 28, 0), rgba(7, 13, 28, .10) 18%, rgba(7, 13, 28, .02) 55%, rgba(7, 13, 28, .28) 100%);
        border-radius: 18px;
        z-index: 0;
    }
    .hero-major-pieces .piece {
        position: relative;
        z-index: 1;
        display: block;
        line-height: .8;
        font-family: Georgia, "Times New Roman", serif;
        color: rgba(18, 15, 40, .78);
        text-shadow:
            0 0 18px rgba(125, 82, 255, .14),
            0 0 2px rgba(255, 224, 176, .10);
        filter: drop-shadow(0 10px 18px rgba(0,0,0,.22));
        user-select: none;
    }
    .hero-major-pieces .piece.knight { font-size: 7rem; transform: translateY(6px); }
    .hero-major-pieces .piece.queen  { font-size: 8.35rem; transform: translateY(2px); }
    .hero-major-pieces .piece.rook   { font-size: 6.7rem; transform: translateY(4px); }
    .hero-major-pieces .piece.bishop { font-size: 6.8rem; transform: translateY(6px); }
    .hero-major-pieces .piece.king   { font-size: 8.6rem; transform: translateY(0); }

    @media (max-width: 1100px) {
        .gauntlet-hero {
            min-height: 142px;
            padding: 18px 24px;
        }
        .gauntlet-icon {
            width: 86px;
            height: 86px;
            font-size: 62px;
        }
        .gauntlet-title {
            font-size: 3rem;
        }
        .gauntlet-copy {
            min-width: 0;
        }
        .hero-ornament {
            transform: scale(.82);
            transform-origin: center;
        }
        .hero-major-pieces {
            width: 38%;
            right: 18px;
            gap: 4px;
            opacity: .72;
        }
        .hero-major-pieces .piece.knight { font-size: 5.2rem; }
        .hero-major-pieces .piece.queen  { font-size: 6rem; }
        .hero-major-pieces .piece.rook   { font-size: 5rem; }
        .hero-major-pieces .piece.bishop { font-size: 5rem; }
        .hero-major-pieces .piece.king   { font-size: 6.15rem; }
    }

    [data-testid="stHorizontalBlock"] > div:has(> [data-testid="stToggle"]) ,
    [data-testid="stHorizontalBlock"] > div:has(> [data-testid="stSlider"]) {
        background: linear-gradient(180deg, rgba(58,72,92,.80), rgba(36,50,70,.86));
        border: 1px solid rgba(255,255,255,.10);
        border-radius: 18px;
        padding: 14px 18px 12px 18px;
        box-shadow: 0 18px 36px rgba(2,8,22,.30), inset 0 1px 0 rgba(255,255,255,.05);
        backdrop-filter: blur(10px);
    }

    [data-testid="stToggle"] label,
    [data-testid="stSlider"] label,
    .stSelectbox label,
    .stCaption,
    .stText,
    p,
    li,
    label {
        color: #e8edff !important;
    }

    .stButton > button {
        border-radius: 16px !important;
        min-height: 3.25rem !important;
        font-weight: 700 !important;
        transition: transform .12s ease, border-color .12s ease, filter .12s ease;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8f69ff 0%, #7657e9 100%) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,.18) !important;
        box-shadow: 0 14px 30px rgba(92, 65, 190, .34), inset 0 1px 0 rgba(255,255,255,.16) !important;
    }

    .stButton > button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        background: linear-gradient(180deg, rgba(55,65,78,.95), rgba(30,39,53,.96)) !important;
        color: #f2f5ff !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        box-shadow: 0 12px 28px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.05) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        border-color: rgba(181, 152, 255, .55) !important;
        color: white !important;
    }

    .stButton > button:disabled {
        opacity: .45 !important;
        transform: none !important;
    }

    [data-testid="stExpander"] {
        background: linear-gradient(180deg, rgba(58,72,92,.74), rgba(36,50,70,.82));
        border: 1px solid rgba(255,255,255,.11);
        border-radius: 18px;
        box-shadow: 0 16px 34px rgba(2,8,22,.24), inset 0 1px 0 rgba(255,255,255,.04);
    }
    [data-testid="stExpander"] details summary p {
        color: #eef2ff !important;
        font-weight: 600;
    }

    .stCode pre {
        background: rgba(7, 13, 26, .85) !important;
        color: #eaf0ff !important;
        border: 1px solid rgba(255,255,255,.08) !important;
    }

    .stSelectbox [data-baseweb="select"] > div,
    [data-testid="stTextInputRootElement"] {
        background: rgba(12, 18, 34, .78) !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        color: #eef2ff !important;
    }

    .stSuccess {
        background: linear-gradient(180deg, rgba(22,72,50,.50), rgba(18,59,42,.56)) !important;
        border: 1px solid rgba(89, 214, 142, .22) !important;
        color: #dcffe7 !important;
        border-radius: 16px !important;
    }

    .stInfo {
        background: linear-gradient(180deg, rgba(58,72,92,.72), rgba(36,50,70,.80)) !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        color: #eaf0ff !important;
        border-radius: 16px !important;
    }

    .stSlider [data-baseweb="slider"] > div div {
        color: #b88dff !important;
    }

    .stSlider [role="slider"] {
        box-shadow: 0 0 0 4px rgba(184, 141, 255, .18);
    }

    .st-emotion-cache-16txtl3, .st-emotion-cache-1r6slb0 {
        color: #eef2ff !important;
    }
    
    .ladder-card {
        background:
            radial-gradient(circle at top right, rgba(143,105,255,.20), transparent 28%),
            linear-gradient(180deg, rgba(255,255,255,.18), rgba(234,240,252,.10));
        border:1px solid rgba(255,255,255,.24);
    }
    .rating-big {
        font-size:34px;
        font-weight:950;
        line-height:1;
        color:#ffffff;
        letter-spacing:-.02em;
        text-shadow:0 4px 18px rgba(0,0,0,.22);
    }
    .rating-title {
        font-size:14px;
        color:#e9efff;
        margin-top:6px;
        font-weight:800;
    }
    .rating-progress {
        height:10px;
        border-radius:999px;
        background:rgba(5,11,24,.36);
        overflow:hidden;
        margin:12px 0 8px;
        border:1px solid rgba(255,255,255,.12);
    }
    .rating-progress-fill {
        height:100%;
        border-radius:999px;
        background:linear-gradient(90deg,#8f69ff,#ffe0a3);
        box-shadow:0 0 14px rgba(143,105,255,.45);
    }
    .rating-small {
        color:#d8e2ff;
        font-size:13px;
        line-height:1.45;
    }
    .challenge-badge {
        display:inline-block;
        padding:4px 8px;
        border-radius:999px;
        background:rgba(143,105,255,.24);
        border:1px solid rgba(255,255,255,.16);
        color:#fff;
        font-size:12px;
        font-weight:900;
        margin-bottom:8px;
    }
    .boss-badge {
        background:rgba(255,196,109,.22);
        border-color:rgba(255,196,109,.36);
        color:#ffe9bd;
    }
    .promotion-modal {
        position:fixed;
        inset:0;
        display:flex;
        justify-content:center;
        align-items:center;
        z-index:999999;
        pointer-events:none;
        background:rgba(4,8,18,.46);
        animation:promotionFade 4.3s ease forwards;
    }
    .promotion-modal-card {
        width:440px;
        max-width:calc(100vw - 40px);
        text-align:center;
        color:#fff;
        border-radius:28px;
        padding:34px 30px;
        background:
            radial-gradient(circle at top, rgba(255,224,163,.24), transparent 34%),
            linear-gradient(180deg, rgba(36,45,70,.96), rgba(14,22,39,.98));
        border:1px solid rgba(255,224,163,.42);
        box-shadow:0 28px 90px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.10);
    }
    .promotion-modal-title {
        font-size:18px;
        letter-spacing:.18em;
        color:#ffe0a3;
        font-weight:950;
        margin-bottom:10px;
    }
    .promotion-modal-rank {
        font-size:48px;
        font-weight:1000;
        line-height:1;
        color:#ffffff;
        text-shadow:0 0 22px rgba(255,224,163,.18);
    }
    .promotion-modal-full {
        margin-top:8px;
        font-size:18px;
        color:#e9efff;
        font-weight:800;
    }
    .promotion-modal-message {
        margin-top:16px;
        color:#d8e2ff;
        font-size:14px;
        line-height:1.45;
    }
    @keyframes promotionFade {
        0% { opacity:0; transform:scale(.98); }
        8% { opacity:1; transform:scale(1); }
        82% { opacity:1; transform:scale(1); }
        100% { opacity:0; transform:scale(.99); }
    }

</style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="gauntlet-hero">
        <div class="hero-glow"></div>
        <div class="hero-major-pieces" aria-hidden="true">
            <span class="piece knight">♞</span>
            <span class="piece queen">♛</span>
            <span class="piece rook">♜</span>
            <span class="piece bishop">♝</span>
            <span class="piece king">♚</span>
        </div>
        <div class="hero-inner-frame"></div>
        <div class="hero-ornament tl"></div>
        <div class="hero-ornament tr"></div>
        <div class="hero-ornament bl"></div>
        <div class="hero-ornament br"></div>
        <div class="gauntlet-icon">♟</div>
        <div class="gauntlet-copy">
            <div class="gauntlet-title">Endgame Gauntlet</div>
            <div class="gauntlet-subtitle">Browser-owned chessboard: set the premove window higher if the engine replies too fast.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

positions = load_positions()
master_tournament_positions = load_master_tournament_positions()

# Board + control panel sit side-by-side so players never have to scroll up for round controls.
pos = current_position() or get_preview_position(positions)
is_preview_board = not st.session_state.game_active

left_deco_col, board_col, side_col = st.columns([0.52, 2.65, 1.10], gap="small")

with left_deco_col:
    ladder_fill = overall_ladder_progress_percent()
    ladder_title = current_title_info()
    ladder_next = next_title_info()
    ladder_next_text = (
        f"Next: {ladder_next['short']} {ladder_next['rating']}"
        if ladder_next
        else "Top title unlocked"
    )
    ladder_ticks = left_ladder_tick_html()
    promoted = st.session_state.pending_title_popup

    title_toast_html = ""
    if promoted:
        toast_next = (
            f"Next: {ladder_next['short']} at {ladder_next['rating']}"
            if ladder_next
            else "Top title unlocked"
        )
        title_toast_html = (
            '<div class="left-title-toast">'
            '<div class="toast-small">Promoted</div>'
            f'<div class="toast-title">You made {promoted["short"]}</div>'
            f'<div class="toast-full">{promoted["full"]}</div>'
            f'<div class="toast-next">Rating {st.session_state.player_rating}<br>{toast_next}</div>'
            '</div>'
        )

    # Build this as one clean HTML string so Markdown cannot treat the indented
    # HTML as a literal code block.
    left_ladder_html = (
        '<div class="premove-side-wrap">'
        '<div class="premove-side-card">'
        '<div class="word-stack" aria-label="premoves takes takes takes">'
        '<span class="stack-line line-premoves">PREMOVES</span>'
        '<span class="stack-line line-takes-1">TAKES</span>'
        '<span class="stack-line line-takes-2">TAKES</span>'
        '<span class="stack-line line-takes-3">TAKES</span>'
        '</div>'
        f'<div class="left-ladder-card" style="--fill-height:{ladder_fill}%">'
        '<div class="left-ladder-title">Master Ladder</div>'
        f'<div class="left-ladder-rating">{st.session_state.player_rating}</div>'
        '<div class="left-ladder-track">'
        f'<div class="left-ladder-fill" style="height:{ladder_fill}%"></div>'
        '<div class="left-ladder-glow"></div>'
        f'{ladder_ticks}'
        '</div>'
        f'<div class="left-ladder-current-title"><b>{ladder_title["short"]}</b><br>{ladder_next_text}</div>'
        '</div>'
        f'{title_toast_html}'
        '</div>'
        '</div>'
    )

    st.markdown(left_ladder_html, unsafe_allow_html=True)

    # Clear after rendering so it flashes beside the ladder but does not keep reappearing.
    if promoted:
        st.session_state.pending_title_popup = None

with board_col:
    # Hidden fixed gameplay settings.
    # Keep sound on, and keep the premove/engine delay locked at 2100ms.
    st.session_state.sound_enabled = True
    st.session_state.engine_move_time_ms = 2100

    if pos:
        value = browser_board(
            fen=pos["fen"],
            position_id=pos.get("id", "position"),
            player_color=pos.get("player_color", "white"),
            round_token=st.session_state.round_token,
            sound_enabled=st.session_state.sound_enabled,
            timer_initial_seconds=current_round_time_seconds(),
            timer_increment_seconds=current_round_increment_seconds(),
            engine_move_time_ms=st.session_state.engine_move_time_ms,
            stockfish_elo=stockfish_elo_for_current_round() if not is_preview_board else 800,
            stockfish_skill=stockfish_skill_for_elo(stockfish_elo_for_current_round() if not is_preview_board else 800),
            round_number=current_round_number() if not is_preview_board else 1,
            total_rounds=total_rounds() if not is_preview_board else "Ready",
            preview_mode=is_preview_board,
            round_result=st.session_state.round_result if not is_preview_board else None,
            round_result_detail=st.session_state.round_result_detail if not is_preview_board else "",
            key="browser_chess_component",
            default=None,
        )
        if apply_component_value(value):
            st.rerun()
    else:
        st.info("Add positions to positions.json to show the board.")

with side_col:
    st.markdown(
        """
        <div class="side-card">
            <h3>♛&nbsp;&nbsp;Gauntlet Controls</h3>
            <div class="sub">Keep playing without scrolling.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("▶   Start 10-Round Game", width="stretch", type="primary"):
        start_game(positions, mode="ten_round")
        st.rerun()

    if st.button("▶   Start Unlimited Game", width="stretch", type="primary"):
        start_game(positions, mode="unlimited")
        st.rerun()

    if st.button("♛   Start Master Tournament", width="stretch", type="primary"):
        start_master_tournament(master_tournament_positions)
        st.rerun()

    if st.button(
        "▷|   Next Round",
        width="stretch",
        disabled=not st.session_state.game_active or st.session_state.round_result is None,
    ):
        next_round()
        st.rerun()

    if st.button("⚐   Abandon Run", width="stretch", disabled=not st.session_state.game_active):
        abandon_game()
        st.rerun()

    current_title = current_title_info()
    next_title = next_title_info()
    progress = rating_progress_percent()

    if next_title:
        next_text = f"Next: <b>{next_title['short']}</b> at <b>{next_title['rating']}</b>"
    else:
        next_text = "Top title unlocked. Chase rating."

    st.markdown(
        f"""
        <div class="side-card ladder-card">
            <div class="rating-big">{st.session_state.player_rating}</div>
            <div class="rating-title">Premove Rating · {current_title['short']}</div>
            <div class="rating-progress">
                <div class="rating-progress-fill" style="width:{progress}%"></div>
            </div>
            <div class="rating-small">
                Highest Title: <b>{current_title['full']}</b><br>
                Best Rating: <b>{st.session_state.best_rating}</b><br>
                Streak: <b>{st.session_state.current_streak}</b> · Best: <b>{st.session_state.best_streak}</b><br>
                {next_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.last_rating_change:
        change = st.session_state.last_rating_change
        sign = "+" if change["delta"] >= 0 else ""
        st.markdown(
            f"""
            <div class="side-card">
                <b>Last Round:</b> {change['result'].title()}<br>
                Rating: <b>{change['old_rating']}</b> → <b>{change['new_rating']}</b>
                (<b>{sign}{change['delta']}</b>)<br>
                Challenge: <b>{change['challenge'].get('challenge_rating', '?')}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.game_active and current_position():
        side_pos = current_position()
        result_text = "In Progress" if st.session_state.round_result is None else st.session_state.round_result.title()

        st.markdown(
            f"""
            <div class="side-card side-card-light">
                <div style="font-size:24px;font-weight:900;margin-bottom:8px;">
                    Round {current_round_number()} / {total_rounds()}
                </div>
                <div style="font-weight:800;margin-bottom:6px;">
                    {side_pos.get('title','Untitled Position')}
                </div>
                <div>Color: <b>{side_pos.get('player_color','white').title()}</b></div>
                <div>Goal: <b>{side_pos.get('goal','win').title()}</b></div>
                <div>Difficulty: <b>{side_pos.get('difficulty','?')}</b></div>
                <div>Puzzle: <b>{side_pos.get('id','?')}</b></div>
                <div>Status: <b>{result_text}</b></div>
                <div>Score: <b>{st.session_state.score:g}{"" if is_unlimited_mode() else " / 10"}</b></div>
                <div>Mode: <b>{mode_label()}</b></div>
                <div>Time: <b>{format_time_limit_label(current_round_time_seconds())}</b> + <b>{current_round_increment_seconds():g}</b></div>
                <br>
                <div class="challenge-badge {'boss-badge' if st.session_state.current_challenge and st.session_state.current_challenge.get('boss') else ''}">
                    {st.session_state.current_challenge.get('round_type','Challenge') if st.session_state.current_challenge else 'Challenge'}
                </div>
                <div>Challenge Rating: <b>{st.session_state.current_challenge.get('challenge_rating','?') if st.session_state.current_challenge else '?'}</b></div>
                <div>Engine Strength: <b>{stockfish_elo_for_current_round()}</b> · Skill <b>{stockfish_skill_for_elo(stockfish_elo_for_current_round())}/20</b></div>
                <div>Engine: <b>{st.session_state.engine_status}</b></div>
                <div>Win: <b>+{win_points_preview(st.session_state.current_challenge) if st.session_state.current_challenge else '?'}</b> · Loss: <b>{loss_points_preview(st.session_state.current_challenge) if st.session_state.current_challenge else '?'}</b></div>
                <div style="font-size:12px;color:#d8e2ff;margin-top:6px;">
                    {st.session_state.current_challenge.get('description','') if st.session_state.current_challenge else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.round_result:
            st.success(
                f"{st.session_state.round_result.title()}: "
                f"{st.session_state.round_result_detail}"
            )

    elif st.session_state.game_completed:
        st.markdown(
            f"""
            <div class="side-card" style="text-align:center;">
                <div style="font-size:32px;font-weight:900;margin-bottom:8px;">
                    {st.session_state.score:g} / 10
                </div>
                <div style="font-size:20px;font-weight:900;margin-bottom:10px;">
                    {player_rank_title()}
                </div>
                <div>Wins: {st.session_state.wins}</div>
                <div>Draws: {st.session_state.draws}</div>
                <div>Losses: {st.session_state.losses}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            f"""
            <div class="side-card">
                <b>Ready</b><br>
                Board is ready. Start a 10-round run or play unlimited.<br>
                Positions loaded: <b>{len(positions)}</b><br>Master Tournament positions: <b>{len(master_tournament_positions)}</b><br>
                Unique Master boards: <b>{master_tournament_unique_count(master_tournament_positions)}</b><br>
                Opening pool: <b>{master_tournament_opening_pool_message(master_tournament_positions)}</b><br>
                Engine: <b>{st.session_state.engine_status}</b><br>
                Timer: <b>{format_time_limit_label(st.session_state.time_limit_seconds)}</b> + <b>{current_round_increment_seconds():g}</b><br>
                Right-click board to clear premoves. Promotion choice enabled. Hope premoves allowed. Use ← → to review moves.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Round Move History", expanded=False):
        if st.session_state.round_history:
            st.write(" ".join(st.session_state.round_history))
        else:
            st.write("No completed round history yet.")

        if st.session_state.round_fen:
            st.caption("Final FEN")
            st.code(st.session_state.round_fen)

    st.markdown(
        """
        <div class="side-card">
            <h3>⏱️&nbsp;&nbsp;Time Control</h3>
            <div class="sub">Set starting seconds and increment for all modes. Master Tournament defaults to 60.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    time_value = instant_time_input(
        label="Seconds per round",
        help_text="Starting clock for 10-Round, Unlimited, and Master Tournament.",
        action="set_time_limit",
        value=int(st.session_state.time_limit_seconds),
        min_value=1,
        max_value=999,
        step=1,
        decimals=0,
        key="instant_time_input_seconds",
        default=None,
    )
    if apply_time_input_value(time_value):
        st.rerun()

    increment_value = instant_time_input(
        label="Increment per move",
        help_text="Extra seconds added after each move you make. Use 0 for no increment.",
        action="set_increment",
        value=current_round_increment_seconds(),
        min_value=0,
        max_value=60,
        step=0.1,
        decimals=1,
        key="instant_time_input_increment",
        default=None,
    )
    if apply_time_input_value(increment_value):
        st.rerun()

    with st.expander("Reset Ladder", expanded=False):
        st.write("This clears rating, title, streaks, and best rating.")
        if st.button("Reset Rating to 800", width="stretch"):
            st.session_state.player_rating = 800
            st.session_state.best_rating = 800
            st.session_state.highest_title_key = "none"
            st.session_state.current_streak = 0
            st.session_state.best_streak = 0
            st.session_state.total_ladder_rounds = 0
            st.session_state.last_rating_change = None
            st.session_state.pending_title_popup = None
            st.rerun()

