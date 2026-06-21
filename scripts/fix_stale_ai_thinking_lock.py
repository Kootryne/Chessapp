from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Helper to cancel stale AI/worker state when changing modes or resetting interaction.
helper = r'''
  function cancelAIThinking(){
    aiJob++;
    aiThinking=false;
    if(aiWorker){ try{ aiWorker.terminate(); }catch(e){} aiWorker=null; }
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
  }

'''
s = s.replace('  function setBotsPaused(on){', helper + '  function setBotsPaused(on){')

# 2-player/editor input must never be blocked by a stale aiThinking flag.
s = s.replace("""    if(aiThinking || game.result) return;
    if(mode==='bot') return;
    if(mode==='ai' && game.turn!==humanColor) return;""", """    if(game.result) return;
    if(mode==='bot') return;
    if(mode==='ai' && aiThinking) return;
    if(mode==='ai' && game.turn!==humanColor) return;""")

# Mode changes should cancel any pending AI job and any stale animation lock.
s = s.replace("""modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); mode=modeSelect.value; if(mode!=='editor'){ document.body.classList.remove('editor-mode'); const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } } if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""", """modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); cancelAIThinking(); mode=modeSelect.value; if(mode!=='editor'){ document.body.classList.remove('editor-mode'); const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } } if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""")

# Reset should cancel stale workers too.
s = s.replace("""    clearMoveFX();
    isAnimatingMove=false; visualMove=null;""", """    clearMoveFX();
    isAnimatingMove=false; visualMove=null;
    cancelAIThinking();""")

# If AI thinking is true but we are no longer in an AI mode, clear it before maybeAIMove returns.
s = s.replace("""  function maybeAIMove(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(aiThinking) return;""", """  function maybeAIMove(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(mode!=='ai' && mode!=='bot') aiThinking=false;
    if(aiThinking) return;""")

# Add a worker timeout failsafe so bots don't freeze forever if worker never replies.
s = s.replace("""      worker.postMessage({type:'search', job:++aiJob, state:deepClone(game), time:turnTime, avoidKeys:recentPositionKeys(14)});
      return;""", """      const postedJob=++aiJob;
      worker.postMessage({type:'search', job:postedJob, state:deepClone(game), time:turnTime, avoidKeys:recentPositionKeys(14)});
      setTimeout(()=>{ if(aiThinking && aiJob===postedJob){ aiThinking=false; if(aiWorker){ try{aiWorker.terminate();}catch(e){} aiWorker=null; } maybeAIMove(); } }, Math.max(1200, turnTime+1200));
      return;""")

p.write_text(s, encoding='utf-8')
print('Fixed stale aiThinking lock and worker timeout freezes.')
