from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Cleaner fullscreen and premium motion styling. Override earlier styles at the end.
s = s.replace('</style>', '''
/* polished movement and cleaner fullscreen */
.piece{animation:none!important;transition:transform .16s ease,filter .16s ease!important}
.square:hover .piece{transform:scale(1.035)}
.square.last-from::after,.square.last-to::after{background:rgba(250,204,21,.18)!important}
.square.last-to::after{box-shadow:inset 0 0 0 3px rgba(250,204,21,.42)!important}
.moving-ghost{position:fixed;z-index:9999;pointer-events:none;display:grid;place-items:center;will-change:transform,opacity;transition:transform .22s cubic-bezier(.18,.86,.23,1),opacity .12s ease;font-size:clamp(2.2rem,8vw,4.2rem);line-height:1;filter:drop-shadow(0 14px 18px rgba(0,0,0,.42)) drop-shadow(0 0 16px rgba(255,255,255,.18))}
.moving-ghost.white{color:#fffaf0;text-shadow:0 2px 0 #7c5b3d,0 0 14px rgba(255,255,255,.22)}
.moving-ghost.black{color:#111827;text-shadow:0 2px 0 rgba(255,255,255,.25),0 0 15px rgba(0,0,0,.25)}
.move-streak{position:fixed;z-index:9998;pointer-events:none;height:16px;border-radius:999px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.48),rgba(255,255,255,0));filter:blur(4px);opacity:0;transform-origin:left center;will-change:transform,opacity;transition:transform .22s cubic-bezier(.18,.86,.23,1),opacity .2s ease}
.capture-pulse{position:absolute;inset:10%;border-radius:18px;border:3px solid rgba(239,68,68,.75);animation:capturePulse .26s ease forwards;pointer-events:none}
@keyframes capturePulse{from{transform:scale(.75);opacity:.9}to{transform:scale(1.25);opacity:0}}

body.board-only .hero{display:block!important;position:fixed;left:10px;right:10px;bottom:10px;z-index:35;padding:8px;border-radius:18px;background:rgba(8,13,30,.76);border:1px solid rgba(255,255,255,.14);box-shadow:0 20px 70px rgba(0,0,0,.45);backdrop-filter:blur(20px);max-height:92px;overflow-x:auto;overflow-y:hidden}
body.board-only .hero .eyebrow,body.board-only .hero h1,body.board-only .hero .sub{display:none!important}
body.board-only .hero .controls{display:flex!important;gap:6px;align-items:center;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;padding:0}
body.board-only .hero .field{min-width:0!important;display:block!important}
body.board-only .hero .field.hidden{display:none!important}
body.board-only .hero .field label{display:none!important}
body.board-only .hero select,body.board-only .hero button{font-size:.78rem;padding:8px 9px;border-radius:12px;white-space:nowrap;min-height:36px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.08)}
body.board-only .hero select{max-width:116px}
body.board-only #fullscreenBtn{display:none!important}
body.board-only .board-pause{display:none!important}
body.board-only .board-exit{top:10px;right:10px;padding:9px 12px;border-radius:13px;background:rgba(8,13,30,.72)}
body.board-only .board-card{padding:0 0 108px 0!important;background:radial-gradient(circle at 50% 25%,rgba(6,182,212,.12),transparent 30rem),#050816!important}
body.board-only .board-wrap{width:min(100vw,calc(100vh - 118px))!important;height:min(100vw,calc(100vh - 118px))!important;filter:drop-shadow(0 28px 55px rgba(0,0,0,.55))}
body.board-only .board{border-radius:14px!important;border:4px solid rgba(255,255,255,.13)!important}
</style>''')

# Add data attributes so animation can find exact squares.
s = s.replace("sq.className=`square ${((r+c)%2===0)?'light':'dark'} ${p?(pieceColor(p)==='w'?'white':'black'):''}`;", "sq.className=`square ${((r+c)%2===0)?'light':'dark'} ${p?(pieceColor(p)==='w'?'white':'black'):''}`;\n        sq.dataset.r=r; sq.dataset.c=c;")

# Smooth move animation functions.
anim = r'''
  function squareElAt(r,c){ return boardEl.querySelector(`[data-r="${r}"][data-c="${c}"]`); }
  function animateMoveVisual(before, move){
    try{
      const piece = before.board[move.from[0]][move.from[1]];
      if(!piece) return;
      const fromEl=squareElAt(move.from[0],move.from[1]);
      const toEl=squareElAt(move.to[0],move.to[1]);
      if(!fromEl || !toEl) return;
      const fr=fromEl.getBoundingClientRect(), tr=toEl.getBoundingClientRect();
      const size=Math.min(fr.width,fr.height);
      const dx=(tr.left+tr.width/2)-(fr.left+fr.width/2);
      const dy=(tr.top+tr.height/2)-(fr.top+fr.height/2);
      const ghost=document.createElement('div');
      ghost.className=`moving-ghost ${pieceColor(piece)==='w'?'white':'black'}`;
      ghost.textContent=PIECE_ICON[pieceColor(piece)][pieceType(piece)];
      ghost.style.left=(fr.left+fr.width/2-size/2)+'px';
      ghost.style.top=(fr.top+fr.height/2-size/2)+'px';
      ghost.style.width=size+'px'; ghost.style.height=size+'px';
      document.body.appendChild(ghost);
      const len=Math.hypot(dx,dy);
      const angle=Math.atan2(dy,dx)*180/Math.PI;
      const streak=document.createElement('div');
      streak.className='move-streak';
      streak.style.left=(fr.left+fr.width/2)+'px';
      streak.style.top=(fr.top+fr.height/2-8)+'px';
      streak.style.width=Math.max(28,len*.72)+'px';
      streak.style.transform=`rotate(${angle}deg) scaleX(.05)`;
      document.body.appendChild(streak);
      if(move.capture || move.enPassantCapture){
        const pulse=document.createElement('div'); pulse.className='capture-pulse'; toEl.appendChild(pulse); setTimeout(()=>pulse.remove(),320);
      }
      requestAnimationFrame(()=>{
        ghost.style.transform=`translate(${dx}px,${dy}px) scale(1.04)`;
        streak.style.opacity='.86';
        streak.style.transform=`rotate(${angle}deg) scaleX(1)`;
      });
      setTimeout(()=>{ ghost.style.opacity='0'; streak.style.opacity='0'; },210);
      setTimeout(()=>{ ghost.remove(); streak.remove(); },360);
    }catch(e){}
  }

'''
s = s.replace('  function showPromotionPicker(moves){', anim + '  function showPromotionPicker(moves){')

# Trigger animation after the board updates, using the previous board position.
s = s.replace("""    draw();
    maybeAIMove();
""", """    draw();
    animateMoveVisual(before, move);
    maybeAIMove();
""", 1)

p.write_text(s, encoding='utf-8')
print('Applied polished move animation and cleaner fullscreen UI.')
