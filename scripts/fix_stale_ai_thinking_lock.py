from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

helper = r'''
  function cancelAIThinking(){
    aiJob++;
    aiThinking=false;
    if(aiWorker){ try{ aiWorker.terminate(); }catch(e){} aiWorker=null; }
    isAnimatingMove=false;
    visualMove=null;
    try{ clearMoveFX(); }catch(e){}
  }

'''
s = s.replace('  function setBotsPaused(on){', helper + '  function setBotsPaused(on){')

s = s.replace("""    if(aiThinking || game.result) return;
    if(mode==='bot') return;
    if(mode==='ai' && game.turn!==humanColor) return;""", """    if(game.result) return;
    if(mode==='bot') return;
    if(mode==='ai' && aiThinking) return;
    if(mode==='ai' && game.turn!==humanColor) return;""")

s = s.replace("""function onSquareClick(r,c){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(isAnimatingMove) return;""", """function onSquareClick(r,c){
    if(isAnimatingMove) cancelAIThinking();""")

s = s.replace("""  function doMove(move){
    if(isAnimatingMove) return;""", """  function doMove(move){
    if(isAnimatingMove) cancelAIThinking();""")

s = s.replace("""modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); mode=modeSelect.value; if(mode!=='editor'){ document.body.classList.remove('editor-mode'); const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } } if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""", """modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); cancelAIThinking(); mode=modeSelect.value; if(mode!=='editor'){ document.body.classList.remove('editor-mode'); const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } } if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""")

s = s.replace("""    clearMoveFX();
    isAnimatingMove=false; visualMove=null;""", """    clearMoveFX();
    isAnimatingMove=false; visualMove=null;
    cancelAIThinking();""")

s = s.replace("""  function maybeAIMove(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(aiThinking) return;""", """  function maybeAIMove(){
    if(isAnimatingMove) cancelAIThinking();
    if(mode!=='ai' && mode!=='bot') aiThinking=false;
    if(aiThinking) return;""")

s = s.replace("""  function draw(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    keepBoardSquare();""", """  function draw(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; try{ clearMoveFX(); }catch(e){} }
    keepBoardSquare();""")

s = s.replace("""      worker.postMessage({type:'search', job:++aiJob, state:deepClone(game), time:turnTime, avoidKeys:recentPositionKeys(14)});
      return;""", """      const postedJob=++aiJob;
      worker.postMessage({type:'search', job:postedJob, state:deepClone(game), time:turnTime, avoidKeys:recentPositionKeys(14)});
      setTimeout(()=>{ if(aiThinking && aiJob===postedJob){ aiThinking=false; if(aiWorker){ try{aiWorker.terminate();}catch(e){} aiWorker=null; } maybeAIMove(); } }, Math.max(1200, turnTime+1200));
      return;""")

p.write_text(s, encoding='utf-8')
print('Fixed stale animation and thinking locks.')
