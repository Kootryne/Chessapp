from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# UX: full-square selected highlight, no rounded corners.
s = s.replace('</style>', '''
/* multiking/editor final fixes */
.square.selected::after{inset:0!important;border-radius:0!important;border:5px solid var(--select)!important;box-shadow:inset 0 0 0 2px rgba(255,255,255,.28),0 0 22px rgba(253,224,71,.65)!important}
#floatingEditorDock{display:none;position:fixed;left:8px;right:8px;bottom:calc(205px + env(safe-area-inset-bottom));z-index:250;padding:8px;border-radius:16px;background:rgba(8,13,30,.90);border:1px solid rgba(255,255,255,.16);box-shadow:0 18px 50px rgba(0,0,0,.50);backdrop-filter:blur(18px);gap:6px;align-items:center;overflow-x:auto;scrollbar-width:none}
body.editor-mode #floatingEditorDock{display:flex!important}.floating-editor-piece{flex:0 0 40px;width:40px;height:40px;border-radius:10px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.12);display:grid;place-items:center;font-size:1.35rem;color:white}.floating-editor-piece.active{outline:3px solid rgba(34,211,238,.9);background:rgba(34,211,238,.22)}
.floating-editor-action{flex:0 0 auto;height:40px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.10);color:white;font-size:.74rem;padding:0 10px}
body.editor-mode.board-only .board-card{padding-bottom:calc(310px + env(safe-area-inset-bottom))!important}
</style>''')

helpers = r'''
  function kingCount(state,color){
    let n=0;
    for(let r=0;r<8;r++) for(let c=0;c<8;c++) if(state.board[r][c]===color+'K') n++;
    return n;
  }
  function customMultiKingMode(state){
    return kingCount(state,'w')!==1 || kingCount(state,'b')!==1;
  }
  function hasAnyKing(state,color){ return kingCount(state,color)>0; }
  function customWinnerByKings(state){
    const wk=hasAnyKing(state,'w'), bk=hasAnyKing(state,'b');
    if(wk && !bk) return 'w';
    if(bk && !wk) return 'b';
    return null;
  }

'''
s = s.replace('  function removeKings(color){', helpers + '  function removeKings(color){')

s = s.replace("""  function removeKings(color){
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
  }""", """  function removeKings(color){}
  function normalizeKingsOnBoard(board){}
  function saveCustomStartFromEditor(){
    customStart=deepClone(game);
    customStart.result=null;
    customStart.turn=game.turn || 'w';
    usingCustomStart=true;
  }""")

s = s.replace("""    if(editorPiece && editorPiece!=='erase'){
      if(pieceType(editorPiece)==='K') removeKings(pieceColor(editorPiece));
      game.board[r][c]=editorPiece;
    } else game.board[r][c]=null;""", """    if(editorPiece && editorPiece!=='erase') game.board[r][c]=editorPiece;
    else game.board[r][c]=null;""")

s = s.replace("""  function legalMovesFor(state, color){
    const out=[];
    for(let r=0;r<8;r++) for(let c=0;c<8;c++){
      const p=state.board[r][c]; if(!p || pieceColor(p)!==color) continue;
      for(const m of generatePseudoMoves(state,r,c)){
        if(m.capture && pieceType(m.capture)==='K') continue;
        const ns=applyMove(state,m);
        if(!isInCheck(ns,color)) out.push(m);
      }
    }
    return out;
  }""", """  function legalMovesFor(state, color){
    const out=[];
    const multi=customMultiKingMode(state);
    for(let r=0;r<8;r++) for(let c=0;c<8;c++){
      const p=state.board[r][c]; if(!p || pieceColor(p)!==color) continue;
      for(const m of generatePseudoMoves(state,r,c)){
        if(multi){ out.push(m); continue; }
        if(m.capture && pieceType(m.capture)==='K') continue;
        const ns=applyMove(state,m);
        if(!isInCheck(ns,color)) out.push(m);
      }
    }
    return out;
  }""")

s = s.replace("""  function annotateResult(state){
    const moves=legalMovesFor(state,state.turn);
    if(moves.length===0){
      state.result = isInCheck(state,state.turn)
        ? {type:'checkmate', winner:other(state.turn)}
        : {type:'stalemate'};
    } else if(state.halfmove>=100){
      state.result = {type:'draw50'};
    } else {
      state.result = null;
    }
    return state.result;
  }""", """  function annotateResult(state){
    if(customMultiKingMode(state)){
      const kingWinner=customWinnerByKings(state);
      if(kingWinner){ state.result={type:'kingCapture', winner:kingWinner}; return state.result; }
      const moves=legalMovesFor(state,state.turn);
      state.result = moves.length===0 ? {type:'stalemate'} : null;
      return state.result;
    }
    const moves=legalMovesFor(state,state.turn);
    if(moves.length===0){
      state.result = isInCheck(state,state.turn)
        ? {type:'checkmate', winner:other(state.turn)}
        : {type:'stalemate'};
    } else if(state.halfmove>=100){
      state.result = {type:'draw50'};
    } else {
      state.result = null;
    }
    return state.result;
  }""")

s = s.replace("game.result.type==='checkmate'", "(game.result.type==='checkmate'||game.result.type==='kingCapture')")
s = s.replace('Checkmate', 'Win')

# Boost king value so bots understand taking kings in multiking custom games.
s = s.replace('const VALUES={P:100,N:320,B:330,R:500,Q:900,K:0};', 'const VALUES={P:100,N:320,B:330,R:500,Q:900,K:20000};')
s = s.replace('const VALUES = {P:100,N:320,B:330,R:500,Q:900,K:0};', 'const VALUES = {P:100,N:320,B:330,R:500,Q:900,K:20000};')
s = s.replace('K:0', 'K:20000')

floating = r'''
  function ensureFloatingEditorDock(){
    let dock=document.getElementById('floatingEditorDock');
    if(dock) return dock;
    dock=document.createElement('div');
    dock.id='floatingEditorDock';
    const pieces=['wK','wQ','wR','wB','wN','wP','bK','bQ','bR','bB','bN','bP','erase'];
    for(const code of pieces){
      const b=document.createElement('button');
      b.type='button'; b.className='floating-editor-piece'; b.dataset.piece=code;
      b.textContent=code==='erase'?'✕':PIECE_ICON[pieceColor(code)][pieceType(code)];
      b.addEventListener('click',()=>{
        editorPiece=code;
        dock.querySelectorAll('.floating-editor-piece').forEach(x=>x.classList.toggle('active',x===b));
        if(editorPalette) [...editorPalette.children].forEach(x=>x.classList.toggle('active',x.dataset.piece===code));
        haptic('edit');
      });
      dock.appendChild(b);
    }
    const clear=document.createElement('button'); clear.type='button'; clear.className='floating-editor-action'; clear.textContent='Clear'; clear.addEventListener('click',clearEditorBoard); dock.appendChild(clear);
    const start=document.createElement('button'); start.type='button'; start.className='floating-editor-action'; start.textContent='Start'; start.addEventListener('click',()=>{game=startPosition(); game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[]; saveCustomStartFromEditor(); haptic('edit'); draw();}); dock.appendChild(start);
    document.body.appendChild(dock);
    return dock;
  }

'''
s = s.replace('  function setupEditorPalette(){', floating + '  function setupEditorPalette(){')
s = s.replace("""    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();""", """    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();
    if(editor) ensureFloatingEditorDock();""")
s = s.replace('setupEditorPalette();', 'setupEditorPalette(); ensureFloatingEditorDock();', 1)
s = s.replace('Only one king per side. New game resets to this setup.', 'Multiple kings allowed. New game resets to this setup.')

p.write_text(s, encoding='utf-8')
print('Added multiking custom-game rules and floating editor palette.')
