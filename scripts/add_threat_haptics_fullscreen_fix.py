from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Styling for threat highlights and safer fullscreen controls.
s = s.replace('</style>', '''
/* threat highlights + safe fullscreen controls */
.square.threatened-by-last::before{content:'';position:absolute;inset:9%;border-radius:14px;border:2px solid rgba(255,70,110,.85);background:radial-gradient(circle,rgba(255,60,120,.26),rgba(255,60,120,.07) 55%,transparent 72%);box-shadow:0 0 18px rgba(255,58,110,.75), inset 0 0 18px rgba(255,58,110,.22);z-index:1;pointer-events:none;animation:threatPulse 1.25s ease-in-out infinite}
.square.threatened-by-last .piece{filter:drop-shadow(0 0 12px rgba(255,60,110,.85)) drop-shadow(0 5px 7px rgba(0,0,0,.38))!important}
@keyframes threatPulse{0%,100%{opacity:.55;transform:scale(.96)}50%{opacity:1;transform:scale(1.035)}}
body.board-only #fullscreenBtn{display:inline-flex!important}
body.board-only #fullscreenBtn::after{content:''}
body.board-only .board-exit{display:none!important}
body.board-only .hero{bottom:max(14px,env(safe-area-inset-bottom))!important;left:8px!important;right:8px!important;z-index:80!important;max-height:112px!important;min-height:54px!important;overflow-x:auto!important;overflow-y:visible!important;padding:10px!important}
body.board-only .hero .controls{padding-bottom:2px!important;min-height:42px!important}
body.board-only .hero select,body.board-only .hero button{min-height:40px!important;padding:9px 10px!important;font-size:.8rem!important}
body.board-only .board-card{padding-bottom:calc(126px + env(safe-area-inset-bottom))!important}
body.board-only .board-wrap{width:min(100vw,calc(100vh - 144px - env(safe-area-inset-bottom)))!important;height:min(100vw,calc(100vh - 144px - env(safe-area-inset-bottom)))!important}
</style>''')

# Add functions before draw().
helpers = r'''
  function haptic(kind){
    if(mode==='bot') return;
    if(!navigator.vibrate) return;
    try{
      if(kind==='mate') navigator.vibrate([45,28,75]);
      else if(kind==='capture') navigator.vibrate(28);
      else if(kind==='check') navigator.vibrate(34);
      else navigator.vibrate(10);
    }catch(e){}
  }
  function hapticForMove(before, move, after){
    if(after.result?.type==='checkmate') return haptic('mate');
    if(move.capture || move.enPassantCapture) return haptic('capture');
    if(isInCheck(after, after.turn)) return haptic('check');
    haptic('move');
  }
  function threatenedSquaresFromLastMove(){
    const last=history[history.length-1]?.move;
    if(!last) return new Set();
    const p=game.board[last.to[0]][last.to[1]];
    if(!p) return new Set();
    const color=pieceColor(p);
    const out=new Set();
    try{
      for(const m of legalMovesFor(game,color)){
        if(m.from[0]===last.to[0] && m.from[1]===last.to[1]){
          const target=game.board[m.to[0]][m.to[1]];
          if(target && pieceColor(target)!==color) out.add(`${m.to[0]},${m.to[1]}`);
        }
      }
    }catch(e){}
    return out;
  }

'''
s = s.replace('  function draw(){', helpers + '  function draw(){')

# Compute threat set once per draw.
s = s.replace("""    keepBoardSquare();
    boardEl.innerHTML='';""", """    keepBoardSquare();
    boardEl.innerHTML='';
    const threatenedByLast=threatenedSquaresFromLastMove();""")

# Mark threatened squares.
s = s.replace("""        if(last && last.from[0]===r && last.from[1]===c) sq.classList.add('last-from');
        if(last && last.to[0]===r && last.to[1]===c) sq.classList.add('last-to');""", """        if(last && last.from[0]===r && last.from[1]===c) sq.classList.add('last-from');
        if(last && last.to[0]===r && last.to[1]===c) sq.classList.add('last-to');
        if(threatenedByLast.has(`${r},${c}`)) sq.classList.add('threatened-by-last');""")

# Vibrate after the board state has committed.
s = s.replace("""      annotateResult(game);
      applyRepetitionDraw();""", """      annotateResult(game);
      applyRepetitionDraw();
      hapticForMove(before, move, game);""")

# Make fullscreen button toggle, and show Exit text while fullscreen.
s = s.replace("fullscreenBtn.addEventListener('click', ()=>setBoardOnly(true));", "fullscreenBtn.addEventListener('click', ()=>setBoardOnly(!boardOnly));")
s = s.replace("""    modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';""", """    fullscreenBtn.textContent = boardOnly ? 'Exit' : 'Fullscreen board';
    modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';""")

# Do not allow double-tap/double-click exit.
s = s.replace("boardEl.addEventListener('dblclick', ()=>{ if(boardOnly) setBoardOnly(false); });", "boardEl.addEventListener('dblclick', ()=>{});")
s = s.replace("boardEl.addEventListener('touchend', ()=>{ const now=Date.now(); if(boardOnly && now-lastBoardTap<360) setBoardOnly(false); lastBoardTap=now; }, {passive:true});", "boardEl.addEventListener('touchend', ()=>{ lastBoardTap=Date.now(); }, {passive:true});")

p.write_text(s, encoding='utf-8')
print('Applied threat highlights, haptics, and fullscreen fixes.')
