from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

speed_options = '''<option value="120">Super fast (~150 ms)</option>
          <option value="500">Fast</option>
          <option value="1500">Smart</option>
          <option value="7000" selected>Really smart</option>
          <option value="15000">Max brain</option>'''
bot_speed_options = '''<option value="120" selected>Super fast (~150 ms)</option>
          <option value="500">Fast</option>
          <option value="1500">Smart</option>
          <option value="7000">Really smart</option>
          <option value="15000">Max brain</option>'''

s = s.replace('''<option value="1500">Fast</option>
          <option value="3500">Smart</option>
          <option value="7000" selected>Really smart</option>
          <option value="15000">Max brain</option>''', speed_options)

# Separate bot speed controls for White and Black in bot-vs-bot.
s = s.replace('''      <button class="primary" id="newBtn">New game</button>''', f'''      <div class="field hidden" id="whiteBotField">
        <label for="whiteBotThinkSelect">White bot speed</label>
        <select id="whiteBotThinkSelect">
          {bot_speed_options}
        </select>
      </div>
      <div class="field hidden" id="blackBotField">
        <label for="blackBotThinkSelect">Black bot speed</label>
        <select id="blackBotThinkSelect">
          {bot_speed_options}
        </select>
      </div>
      <button class="primary" id="newBtn">New game</button>''')
s = s.replace('<button id="fullscreenBtn">Fullscreen board</button>', '<button id="fullscreenBtn">Fullscreen board</button>\n      <button id="pauseBotsBtn" class="hidden">Pause bots</button>')
s = s.replace('<div id="resultOverlay" class="result-overlay hidden"></div>', '<div id="resultOverlay" class="result-overlay hidden"></div>\n        <button id="exitBoardOnlyBtn" class="board-float board-exit">Exit</button>\n        <button id="pauseBoardBotsBtn" class="board-float board-pause">Pause</button>')

# Floating buttons inside board-only mode so fullscreen can always be exited.
s = s.replace('</style>', '''
.board-float{display:none}
body.board-only .board-float{display:block;position:fixed;z-index:30;border:1px solid rgba(255,255,255,.28);background:rgba(15,23,42,.74);color:white;backdrop-filter:blur(10px);padding:10px 13px;border-radius:14px;font-weight:900;box-shadow:0 10px 30px rgba(0,0,0,.35)}
body.board-only .board-exit{right:12px;top:12px}
body.board-only .board-pause{left:12px;top:12px}
body:not(.board-only) .board-float{display:none!important}
</style>''')

s = s.replace("const fullscreenBtn=$('fullscreenBtn'), resultOverlay=$('resultOverlay');", "const fullscreenBtn=$('fullscreenBtn'), resultOverlay=$('resultOverlay');\n  const pauseBotsBtn=$('pauseBotsBtn'), whiteBotThinkSelect=$('whiteBotThinkSelect'), blackBotThinkSelect=$('blackBotThinkSelect');\n  const whiteBotField=$('whiteBotField'), blackBotField=$('blackBotField'), exitBoardOnlyBtn=$('exitBoardOnlyBtn'), pauseBoardBotsBtn=$('pauseBoardBotsBtn');")
s = s.replace("let boardOnly=false, lastBoardTap=0;", "let boardOnly=false, lastBoardTap=0;\n  let botsPaused=false, whiteBotTime=120, blackBotTime=120;")

old_set_mode = """  function setModeUI(){
    const ai = mode==='ai';
    const bot = mode==='bot';
    const usesAI = ai || bot;
    sideField.classList.toggle('hidden', !ai);
    thinkField.classList.toggle('hidden', !usesAI);
    modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';
    aiTip.textContent = bot ? `AI: both sides • ${thinkSelect.options[thinkSelect.selectedIndex].text}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${thinkSelect.options[thinkSelect.selectedIndex].text}` : 'AI: off';
  }
"""
new_set_mode = """  function labelOf(select){ return select.options[select.selectedIndex]?.text || ''; }
  function setModeUI(){
    const ai = mode==='ai';
    const bot = mode==='bot';
    const usesAI = ai || bot;
    sideField.classList.toggle('hidden', !ai);
    thinkField.classList.toggle('hidden', !ai);
    whiteBotField.classList.toggle('hidden', !bot);
    blackBotField.classList.toggle('hidden', !bot);
    pauseBotsBtn.classList.toggle('hidden', !bot);
    pauseBoardBotsBtn.style.display = (boardOnly && bot) ? 'block' : 'none';
    pauseBotsBtn.textContent = botsPaused ? 'Resume bots' : 'Pause bots';
    pauseBoardBotsBtn.textContent = botsPaused ? 'Resume' : 'Pause';
    modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';
    aiTip.textContent = bot ? `AI: White ${labelOf(whiteBotThinkSelect)} • Black ${labelOf(blackBotThinkSelect)}${botsPaused?' • paused':''}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${labelOf(thinkSelect)}` : 'AI: off';
  }
"""
if old_set_mode not in s:
    raise SystemExit('setModeUI block not found')
s = s.replace(old_set_mode, new_set_mode)

# Pause/resume and fullscreen control helpers.
s = s.replace("""  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', on);
    setTimeout(()=>{ keepBoardSquare(); draw(); }, 40);
  }

""", """  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', on);
    setTimeout(()=>{ keepBoardSquare(); draw(); setModeUI(); }, 40);
  }
  function setBotsPaused(on){
    botsPaused=on;
    if(on){
      aiJob++;
      aiThinking=false;
      if(aiWorker){ try{ aiWorker.terminate(); }catch(e){} aiWorker=null; }
    }
    setModeUI();
    draw();
    if(!on) maybeAIMove();
  }

""")

# Show paused status before thinking status.
s = s.replace("else if(aiThinking) statusText.textContent = 'AI is thinking ahead...';", "else if(mode==='bot' && botsPaused) statusText.textContent = 'Bots are paused.';\n    else if(aiThinking) statusText.textContent = 'AI is thinking ahead...';")

# Bot-vs-bot should respect per-side speed and pause.
s = s.replace("if((mode!=='ai' && mode!=='bot') || game.result) return;", "if((mode!=='ai' && mode!=='bot') || game.result || (mode==='bot' && botsPaused)) return;")
s = s.replace("if(mode==='bot') aiColor=game.turn;", "if(mode==='bot') aiColor=game.turn;\n    const turnTime = mode==='bot' ? (game.turn==='w' ? whiteBotTime : blackBotTime) : aiTime;")
s = s.replace("time:aiTime", "time:turnTime")
s = s.replace("Math.min(aiTime, 2500)", "Math.min(turnTime, 2500)")
s = s.replace("aiTip.textContent='AI thinking in background...';", "aiTip.textContent = mode==='bot' ? `${game.turn==='w'?'White':'Black'} bot thinking...` : 'AI thinking in background...';")

# Mode switching: reset pause only when leaving bot mode.
s = s.replace(
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });",
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });"
)

# Add control event listeners.
s = s.replace("""fullscreenBtn.addEventListener('click', ()=>setBoardOnly(true));
  boardEl.addEventListener('dblclick', ()=>{ if(boardOnly) setBoardOnly(false); });""", """fullscreenBtn.addEventListener('click', ()=>setBoardOnly(true));
  exitBoardOnlyBtn.addEventListener('click', ()=>setBoardOnly(false));
  pauseBotsBtn.addEventListener('click', ()=>setBotsPaused(!botsPaused));
  pauseBoardBotsBtn.addEventListener('click', ()=>setBotsPaused(!botsPaused));
  boardEl.addEventListener('dblclick', ()=>{ if(boardOnly) setBoardOnly(false); });""")
s = s.replace("""thinkSelect.addEventListener('change', ()=>{ aiTime=Number(thinkSelect.value)||2800; setModeUI(); });""", """thinkSelect.addEventListener('change', ()=>{ aiTime=Number(thinkSelect.value)||120; setModeUI(); });
  whiteBotThinkSelect.addEventListener('change', ()=>{ whiteBotTime=Number(whiteBotThinkSelect.value)||120; setModeUI(); maybeAIMove(); });
  blackBotThinkSelect.addEventListener('change', ()=>{ blackBotTime=Number(blackBotThinkSelect.value)||120; setModeUI(); maybeAIMove(); });""")
s = s.replace("mode = modeSelect.value; humanColor = sideSelect.value; aiColor = other(humanColor); aiTime = Number(thinkSelect.value)||7000;", "mode = modeSelect.value; humanColor = sideSelect.value; aiColor = other(humanColor); aiTime = Number(thinkSelect.value)||7000; whiteBotTime=Number(whiteBotThinkSelect.value)||120; blackBotTime=Number(blackBotThinkSelect.value)||120;")

p.write_text(s, encoding='utf-8')
print('Added bot pause, visible fullscreen exit, per-bot speeds, and super-fast mode.')
