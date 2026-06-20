from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Mode + button UI
s = s.replace('<option value="ai">Play vs AI</option>', '<option value="ai">Play vs AI</option>\n          <option value="bot">Bot vs bot</option>')
s = s.replace('<button id="flipBtn">Flip board</button>', '<button id="flipBtn">Flip board</button>\n      <button id="fullscreenBtn">Fullscreen board</button>')
s = s.replace('<div id="board" class="board"></div>', '<div id="board" class="board"></div>\n        <div id="resultOverlay" class="result-overlay hidden"></div>')

# Board-only fullscreen + winner overlay styling.
s = s.replace('</style>', '''
.board-wrap{position:relative}
.result-overlay{position:absolute;inset:0;display:grid;place-items:center;text-align:center;font-weight:1000;font-size:clamp(2rem,10vw,5.5rem);line-height:1.02;color:white;background:rgba(2,6,23,.72);text-shadow:0 6px 30px rgba(0,0,0,.8);padding:24px;z-index:10;backdrop-filter:blur(5px)}
.result-overlay.hidden{display:none}
body.board-only{padding:0;background:#050816;overflow:hidden}
body.board-only .hero,body.board-only .side,body.board-only .bar{display:none!important}
body.board-only .app{max-width:none;margin:0;width:100vw;height:100vh;display:grid;place-items:center}
body.board-only .layout{display:block;width:100vw;height:100vh}
body.board-only .board-card{border-radius:0;border:0;box-shadow:none;background:#050816;padding:0;width:100vw;height:100vh;display:grid;place-items:center}
body.board-only .board-wrap{width:min(100vw,100vh);height:min(100vw,100vh);max-width:none;margin:0}
body.board-only .board{width:100%;height:100%;border-radius:0;border-width:0}
body.board-only .piece{font-size:clamp(1.7rem,9.8vmin,5.1rem)}
</style>''')

# Extra elements / state.
s = s.replace("const modeTip=$('modeTip'), aiTip=$('aiTip');", "const modeTip=$('modeTip'), aiTip=$('aiTip');\n  const fullscreenBtn=$('fullscreenBtn'), resultOverlay=$('resultOverlay');")
s = s.replace("let aiWorker=null, aiJob=0;", "let aiWorker=null, aiJob=0;\n  let boardOnly=false, lastBoardTap=0;")

# Bot-vs-bot aware mode UI.
old_set_mode = """  function setModeUI(){
    const ai = mode==='ai';
    sideField.classList.toggle('hidden', !ai);
    thinkField.classList.toggle('hidden', !ai);
    modeTip.textContent = ai ? 'Mode: play vs AI' : 'Mode: 2 players';
    aiTip.textContent = ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${thinkSelect.options[thinkSelect.selectedIndex].text}` : 'AI: off';
  }
"""
new_set_mode = """  function setModeUI(){
    const ai = mode==='ai';
    const bot = mode==='bot';
    const usesAI = ai || bot;
    sideField.classList.toggle('hidden', !ai);
    thinkField.classList.toggle('hidden', !usesAI);
    modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';
    aiTip.textContent = bot ? `AI: both sides • ${thinkSelect.options[thinkSelect.selectedIndex].text}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${thinkSelect.options[thinkSelect.selectedIndex].text}` : 'AI: off';
  }
"""
if old_set_mode not in s:
    raise SystemExit('setModeUI block not found')
s = s.replace(old_set_mode, new_set_mode)

# Result overlay helpers.
insert_after_keep = """  window.addEventListener('orientationchange', ()=>setTimeout(keepBoardSquare, 120));

"""
result_helpers = """  function resultText(){
    if(game.result?.type==='checkmate') return `${game.result.winner==='w'?'White':'Black'} wins!\\nCheckmate`;
    if(game.result?.type==='stalemate') return 'Draw!\\nStalemate';
    if(game.result?.type==='draw50') return 'Draw!\\n50-move rule';
    return '';
  }
  function updateResultOverlay(){
    const txt=resultText();
    if(!txt){ resultOverlay.classList.add('hidden'); resultOverlay.textContent=''; return; }
    resultOverlay.textContent=txt;
    resultOverlay.classList.remove('hidden');
  }
  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', on);
    setTimeout(()=>{ keepBoardSquare(); draw(); }, 40);
  }

"""
if insert_after_keep in s:
    s = s.replace(insert_after_keep, insert_after_keep + result_helpers)
else:
    raise SystemExit('Could not insert result helpers')

s = s.replace("""    moveListEl.innerHTML = moveTexts.map((txt, idx) => `<li>${Math.floor(idx/2)+1}. ${txt}</li>`).join('');
    setModeUI();
  }
""", """    moveListEl.innerHTML = moveTexts.map((txt, idx) => `<li>${Math.floor(idx/2)+1}. ${txt}</li>`).join('');
    updateResultOverlay();
    setModeUI();
  }
""")

# Humans should not move in bot-vs-bot mode.
s = s.replace("function humanCanPlay(color){ return mode==='human' || color===humanColor; }", "function humanCanPlay(color){ return mode==='human' || (mode==='ai' && color===humanColor); }")
s = s.replace("if(mode==='ai' && game.turn!==humanColor) return;", "if(mode==='bot') return;\n    if(mode==='ai' && game.turn!==humanColor) return;")

# Make the worker AI handle both sides in bot-vs-bot mode.
s = s.replace(
    "if(mode!=='ai' || game.result || game.turn!==aiColor) return;",
    "if((mode!=='ai' && mode!=='bot') || game.result) return;\n    if(mode==='ai' && game.turn!==aiColor) return;\n    if(mode==='bot') aiColor=game.turn;"
)

# Changing mode should not reset. Bot-vs-bot starts continuing from current position.
s = s.replace(
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; aiColor = other(humanColor); setModeUI(); draw(); maybeAIMove(); });",
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });"
)

# Fullscreen controls: button enters board-only mode; double-tap/two quick taps exits.
s = s.replace("$('flipBtn').addEventListener('click', ()=>{flipped=!flipped; draw();});", "$('flipBtn').addEventListener('click', ()=>{flipped=!flipped; draw();});\n  fullscreenBtn.addEventListener('click', ()=>setBoardOnly(true));\n  boardEl.addEventListener('dblclick', ()=>{ if(boardOnly) setBoardOnly(false); });\n  boardEl.addEventListener('touchend', ()=>{ const now=Date.now(); if(boardOnly && now-lastBoardTap<360) setBoardOnly(false); lastBoardTap=now; }, {passive:true});")

p.write_text(s, encoding='utf-8')
print('Added bot-vs-bot, board-only fullscreen, and result overlay.')
