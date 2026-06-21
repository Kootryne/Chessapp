from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Replace the old ghost/streak system with a real delayed-commit cinematic system.
s = s.replace("let botsPaused=false, whiteBotTime=120, blackBotTime=120;", "let botsPaused=false, whiteBotTime=120, blackBotTime=120;\n  let isAnimatingMove=false, visualMove=null;")

# Better cinematic CSS. Hide old streak style by replacing/overriding it.
s = s.replace('</style>', '''
/* cinematic real-piece move system */
.board.animating{pointer-events:none}
.moving-ghost{position:fixed;z-index:9999;pointer-events:none;display:grid;place-items:center;will-change:transform,opacity;line-height:1;filter:drop-shadow(0 20px 24px rgba(0,0,0,.5)) drop-shadow(0 0 18px rgba(255,255,255,.18));font-size:clamp(2.4rem,8.5vw,4.6rem)}
.moving-ghost.white{color:#fffaf0;text-shadow:0 2px 0 #7c5b3d,0 0 14px rgba(255,255,255,.24)}
.moving-ghost.black{color:#111827;text-shadow:0 2px 0 rgba(255,255,255,.28),0 0 15px rgba(0,0,0,.28)}
.trail-piece{position:fixed;z-index:9996;pointer-events:none;display:grid;place-items:center;line-height:1;will-change:transform,opacity;filter:blur(1.5px) drop-shadow(0 0 10px rgba(255,255,255,.25));animation:trailFade .32s ease-out forwards}
.trail-piece.white{color:rgba(255,250,240,.55)}
.trail-piece.black{color:rgba(17,24,39,.45)}
@keyframes trailFade{from{opacity:.75;transform:scale(.96)}to{opacity:0;transform:scale(.72)}}
.motion-target{box-shadow:inset 0 0 0 5px rgba(34,211,238,.52), inset 0 0 38px rgba(34,211,238,.22)!important}
.piece.capture-victim{animation:victimVanish .34s cubic-bezier(.2,.8,.2,1) forwards!important}
@keyframes victimVanish{0%{opacity:1;transform:scale(1) rotate(0deg);filter:none}55%{opacity:.65;transform:scale(.82) rotate(5deg);filter:blur(.4px)}100%{opacity:0;transform:scale(.25) rotate(-12deg);filter:blur(3px)}}
.board.capture-shake{animation:boardHit .18s ease-out}
@keyframes boardHit{0%{transform:translateX(0)}30%{transform:translateX(-2px)}65%{transform:translateX(2px)}100%{transform:translateX(0)}}
.piece-wrap.hidden-moving{visibility:hidden}
</style>''')

# Make draw hide the moving source piece and fade captured victim while old board is still shown.
s = s.replace("""        const p=game.board[r][c];
        sq.className=`square ${((r+c)%2===0)?'light':'dark'} ${p?(pieceColor(p)==='w'?'white':'black'):''}`;""", """        let p=game.board[r][c];
        const movingFrom = visualMove && visualMove.from[0]===r && visualMove.from[1]===c;
        const victimHere = visualMove && visualMove.capture && visualMove.to[0]===r && visualMove.to[1]===c;
        if(movingFrom) p=null;
        sq.className=`square ${((r+c)%2===0)?'light':'dark'} ${p?(pieceColor(p)==='w'?'white':'black'):''}`;""")

s = s.replace("""          const wrap=document.createElement('div'); wrap.className='piece-wrap';
          const span=document.createElement('span'); span.className='piece'; span.textContent=PIECE_ICON[pieceColor(p)][pieceType(p)];""", """          const wrap=document.createElement('div'); wrap.className='piece-wrap';
          const span=document.createElement('span'); span.className='piece' + (victimHere?' capture-victim':''); span.textContent=PIECE_ICON[pieceColor(p)][pieceType(p)];""")

# Replace the old animation function with a cinematic callback-based one.
start = s.find('  function squareElAt(r,c){')
end = s.find('  function showPromotionPicker(moves){')
if start == -1 or end == -1:
    raise SystemExit('could not find animation block')
new_anim = r'''  function squareElAt(r,c){ return boardEl.querySelector(`[data-r="${r}"][data-c="${c}"]`); }
  function clearMoveFX(){
    document.querySelectorAll('.moving-ghost,.trail-piece').forEach(e=>e.remove());
    boardEl.classList.remove('animating','capture-shake');
    document.querySelectorAll('.motion-target').forEach(e=>e.classList.remove('motion-target'));
  }
  function animateMoveVisual(before, move, done){
    try{
      const piece = before.board[move.from[0]][move.from[1]];
      const fromEl=squareElAt(move.from[0],move.from[1]);
      const toEl=squareElAt(move.to[0],move.to[1]);
      if(!piece || !fromEl || !toEl){ done&&done(); return; }
      const fr=fromEl.getBoundingClientRect(), tr=toEl.getBoundingClientRect();
      const size=Math.min(fr.width,fr.height);
      const dx=(tr.left+tr.width/2)-(fr.left+fr.width/2);
      const dy=(tr.top+tr.height/2)-(fr.top+fr.height/2);
      const ghost=document.createElement('div');
      ghost.className=`moving-ghost ${pieceColor(piece)==='w'?'white':'black'}`;
      ghost.textContent=PIECE_ICON[pieceColor(piece)][pieceType(piece)];
      ghost.style.left=(fr.left+fr.width/2-size/2)+'px';
      ghost.style.top=(fr.top+fr.height/2-size/2)+'px';
      ghost.style.width=size+'px'; ghost.style.height=size+'px'; ghost.style.fontSize=(size*.72)+'px';
      document.body.appendChild(ghost);
      boardEl.classList.add('animating');
      if(move.capture || move.enPassantCapture) boardEl.classList.add('capture-shake');
      toEl.classList.add('motion-target');

      const trailColor=pieceColor(piece)==='w'?'white':'black';
      const trailTimers=[];
      for(let i=1;i<=5;i++){
        trailTimers.push(setTimeout(()=>{
          const f=Math.max(.08,(i-1)/6);
          const t=document.createElement('div');
          t.className=`trail-piece ${trailColor}`;
          t.textContent=PIECE_ICON[pieceColor(piece)][pieceType(piece)];
          const left=fr.left+fr.width/2-size/2+dx*f;
          const top=fr.top+fr.height/2-size/2+dy*f;
          t.style.left=left+'px'; t.style.top=top+'px'; t.style.width=size+'px'; t.style.height=size+'px';
          t.style.fontSize=(size*(.66-i*.045))+'px';
          document.body.appendChild(t);
          setTimeout(()=>t.remove(),380);
        }, i*58));
      }

      const duration = (move.capture || move.enPassantCapture) ? 430 : 360;
      const lift = Math.min(28, Math.max(14, size*.22));
      let finished=false;
      function finish(){
        if(finished) return; finished=true;
        trailTimers.forEach(clearTimeout);
        ghost.remove();
        toEl.classList.remove('motion-target');
        boardEl.classList.remove('animating','capture-shake');
        done&&done();
      }
      if(ghost.animate){
        const anim=ghost.animate([
          {transform:'translate3d(0,0,0) scale(1)', offset:0},
          {transform:`translate3d(${dx*.18}px,${dy*.18-lift}px,0) scale(1.15)`, offset:.20},
          {transform:`translate3d(${dx*.82}px,${dy*.82-lift*.35}px,0) scale(1.08)`, offset:.78},
          {transform:`translate3d(${dx}px,${dy}px,0) scale(1)`, offset:1}
        ], {duration, easing:'cubic-bezier(.16,.88,.17,1)', fill:'forwards'});
        anim.onfinish=finish;
      } else {
        ghost.style.transition=`transform ${duration}ms cubic-bezier(.16,.88,.17,1)`;
        requestAnimationFrame(()=>ghost.style.transform=`translate3d(${dx}px,${dy}px,0) scale(1)`);
        setTimeout(finish,duration+40);
      }
    }catch(e){ done&&done(); }
  }

'''
s = s[:start] + new_anim + s[end:]

# Block clicks during animation.
s = s.replace("function onSquareClick(r,c){", "function onSquareClick(r,c){\n    if(isAnimatingMove) return;")

# Reset should clear effects.
s = s.replace("""    game = startPosition();
    selected = null; legalTargets=[]; history=[]; moveTexts=[]; aiThinking=false;""", """    clearMoveFX();
    isAnimatingMove=false; visualMove=null;
    game = startPosition();
    selected = null; legalTargets=[]; history=[]; moveTexts=[]; aiThinking=false;""")

# Replace doMove with delayed visual commit.
old = """  function doMove(move){
    const before=deepClone(game);
    history.push({game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime});
    game = applyMove(game, move);
    const moveText = moveToText(before, move, game);
    moveTexts.push(moveText);
    annotateResult(game);
    applyRepetitionDraw();
    selected=null; legalTargets=[];
    draw();
    animateMoveVisual(before, move);
    maybeAIMove();
  }
"""
new = """  function doMove(move){
    if(isAnimatingMove) return;
    const before=deepClone(game);
    const after=applyMove(before, move);
    const moveText = moveToText(before, move, after);
    const hist={game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime};
    isAnimatingMove=true;
    visualMove={from:move.from, to:move.to, capture:!!(move.capture||move.enPassantCapture), piece:before.board[move.from[0]][move.from[1]]};
    selected=null; legalTargets=[];
    draw();
    animateMoveVisual(before, move, ()=>{
      history.push(hist);
      game=after;
      moveTexts.push(moveText);
      annotateResult(game);
      applyRepetitionDraw();
      visualMove=null;
      isAnimatingMove=false;
      draw();
      maybeAIMove();
    });
  }
"""
if old not in s:
    raise SystemExit('old doMove not found')
s = s.replace(old,new)

# Undo should not happen during an animation.
s = s.replace("undoBtn.addEventListener('click', ()=>{", "undoBtn.addEventListener('click', ()=>{ if(isAnimatingMove) return;")

p.write_text(s, encoding='utf-8')
print('Applied cinematic delayed-commit move system.')
