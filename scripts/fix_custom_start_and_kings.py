from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Track the saved custom setup made in editor mode.
s = s.replace('let editorPiece=null;', 'let editorPiece=null;\n  let customStart=null, usingCustomStart=false;')

helpers = r'''
  function removeKings(color){
    for(let r=0;r<8;r++) for(let c=0;c<8;c++) if(game.board[r][c]===color+'K') game.board[r][c]=null;
  }
  function normalizeKingsOnBoard(board){
    for(const color of ['w','b']){
      let seen=false;
      for(let r=0;r<8;r++) for(let c=0;c<8;c++){
        if(board[r][c]===color+'K'){
          if(!seen) seen=true;
          else board[r][c]=null;
        }
      }
    }
  }
  function saveCustomStartFromEditor(){
    normalizeKingsOnBoard(game.board);
    customStart=deepClone(game);
    customStart.result=null;
    customStart.turn=game.turn || 'w';
    usingCustomStart=true;
  }

'''
s = s.replace('  function setupEditorPalette(){', helpers + '  function setupEditorPalette(){')

# Editor placement: only allow one king of each color, and auto-save custom setup after edits.
s = s.replace("""    if(editorPiece && editorPiece!=='erase') game.board[r][c]=editorPiece;
    else game.board[r][c]=null;
    haptic('edit');
    draw();""", """    if(editorPiece && editorPiece!=='erase'){
      if(pieceType(editorPiece)==='K') removeKings(pieceColor(editorPiece));
      game.board[r][c]=editorPiece;
    } else game.board[r][c]=null;
    saveCustomStartFromEditor();
    haptic('edit');
    draw();""")

# Clear editor board also becomes the custom setup.
s = s.replace("""    game.board=Array.from({length:8},()=>Array(8).fill(null));
    game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[];
    haptic('edit'); draw();""", """    game.board=Array.from({length:8},()=>Array(8).fill(null));
    game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[];
    saveCustomStartFromEditor();
    haptic('edit'); draw();""")

# Reset to saved custom start when one exists.
s = s.replace("""    game = startPosition();
    selected = null; legalTargets=[]; history=[]; moveTexts=[]; aiThinking=false;""", """    game = (usingCustomStart && customStart) ? deepClone(customStart) : startPosition();
    normalizeKingsOnBoard(game.board);
    game.result=null;
    selected = null; legalTargets=[]; history=[]; moveTexts=[]; aiThinking=false;""")

# Save setup when leaving editor mode, so New game restores that exact setup later.
s = s.replace("""modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""", """modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); mode=modeSelect.value; if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""")

# Start position button in editor saves normal start as the custom reset setup.
s = s.replace("""if(editorStartBtn) editorStartBtn.addEventListener('click', ()=>{game=startPosition(); game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[]; haptic('edit'); draw();});""", """if(editorStartBtn) editorStartBtn.addEventListener('click', ()=>{game=startPosition(); game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[]; saveCustomStartFromEditor(); haptic('edit'); draw();});""")

# Legal move generation should never capture a king. That breaks custom/edited positions.
s = s.replace("""      for(const m of generatePseudoMoves(state,r,c)){
        const ns=applyMove(state,m);
        if(!isInCheck(ns,color)) out.push(m);""", """      for(const m of generatePseudoMoves(state,r,c)){
        if(m.capture && pieceType(m.capture)==='K') continue;
        const ns=applyMove(state,m);
        if(!isInCheck(ns,color)) out.push(m);""")

# Update editor text to say only one king per side is allowed.
s = s.replace('Editor: tap a piece, then tap a square. Tap a piece on the board to remove it.', 'Editor: tap a piece, then tap a square. Only one king per side. New game resets to this setup.')

p.write_text(s, encoding='utf-8')
print('Fixed custom setup reset and editor king validation.')
