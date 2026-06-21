from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Smooth TikTok-edit style power move: one GPU beam, one moving piece, no laggy trail clones.
s = s.replace('</style>', '''
/* smooth power-move FX: no laggy ghost trails */
.trail-piece,.move-streak{display:none!important}
.power-beam{position:fixed;z-index:9997;pointer-events:none;height:32px;border-radius:999px;transform-origin:0 50%;will-change:transform,opacity;mix-blend-mode:screen;background:linear-gradient(90deg,rgba(255,39,90,0),rgba(255,39,90,.28),rgba(255,90,145,.92),rgba(255,255,255,.75),rgba(255,90,145,.62),rgba(255,39,90,0));box-shadow:0 0 16px rgba(255,43,110,.75),0 0 42px rgba(255,43,110,.34);filter:blur(.15px)}
.power-beam::after{content:'';position:absolute;left:4%;right:4%;top:50%;height:3px;transform:translateY(-50%);border-radius:999px;background:rgba(255,255,255,.9);box-shadow:0 0 12px rgba(255,255,255,.9)}
.power-source,.power-target{box-shadow:inset 0 0 0 4px rgba(255,54,112,.55), inset 0 0 34px rgba(255,54,112,.24)!important}
.power-target{box-shadow:inset 0 0 0 5px rgba(255,54,112,.72), inset 0 0 44px rgba(255,54,112,.32)!important}
.moving-ghost{filter:drop-shadow(0 22px 20px rgba(0,0,0,.58)) drop-shadow(0 0 18px rgba(255,80,140,.42))!important;will-change:transform,opacity!important;backface-visibility:hidden;transform:translateZ(0)}
.board.power-hit{animation:powerHit .16s ease-out}
@keyframes powerHit{0%{transform:translate3d(0,0,0)}35%{transform:translate3d(-1.5px,0,0)}70%{transform:translate3d(1.5px,0,0)}100%{transform:translate3d(0,0,0)}}
</style>''')

start = s.find('  function squareElAt(r,c){')
end = s.find('  function showPromotionPicker(moves){')
if start == -1 or end == -1:
    raise SystemExit('animation block not found')

new_anim = r'''  function squareElAt(r,c){ return boardEl.querySelector(`[data-r="${r}"][data-c="${c}"]`); }
  function clearMoveFX(){
    document.querySelectorAll('.moving-ghost,.trail-piece,.move-streak,.power-beam').forEach(e=>e.remove());
    boardEl.classList.remove('animating','capture-shake','power-hit');
    document.querySelectorAll('.motion-target,.power-source,.power-target').forEach(e=>e.classList.remove('motion-target','power-source','power-target'));
  }
  function animateMoveVisual(before, move, done){
    try{
      const piece = before.board[move.from[0]][move.from[1]];
      const fromEl=squareElAt(move.from[0],move.from[1]);
      const toEl=squareElAt(move.to[0],move.to[1]);
      if(!piece || !fromEl || !toEl){ done&&done(); return; }
      const fr=fromEl.getBoundingClientRect(), tr=toEl.getBoundingClientRect();
      const size=Math.min(fr.width,fr.height);
      const sx=fr.left+fr.width/2, sy=fr.top+fr.height/2;
      const tx=tr.left+tr.width/2, ty=tr.top+tr.height/2;
      const dx=tx-sx, dy=ty-sy;
      const len=Math.max(24,Math.hypot(dx,dy));
      const angle=Math.atan2(dy,dx)*180/Math.PI;
      const strong=!!(move.capture || move.enPassantCapture || move.promotion || move.castle);
      const duration=strong?355:285;

      boardEl.classList.add('animating');
      fromEl.classList.add('power-source');
      toEl.classList.add('power-target');
      if(move.capture || move.enPassantCapture) boardEl.classList.add('power-hit');

      const beam=document.createElement('div');
      beam.className='power-beam';
      beam.style.left=sx+'px';
      beam.style.top=(sy-16)+'px';
      beam.style.width=len+'px';
      beam.style.transform=`rotate(${angle}deg) scaleX(.001)`;
      beam.style.opacity='0';
      document.body.appendChild(beam);

      const ghost=document.createElement('div');
      ghost.className=`moving-ghost ${pieceColor(piece)==='w'?'white':'black'}`;
      ghost.textContent=PIECE_ICON[pieceColor(piece)][pieceType(piece)];
      ghost.style.left=(sx-size/2)+'px';
      ghost.style.top=(sy-size/2)+'px';
      ghost.style.width=size+'px'; ghost.style.height=size+'px'; ghost.style.fontSize=(size*.74)+'px';
      document.body.appendChild(ghost);

      let finished=false;
      function finish(){
        if(finished) return; finished=true;
        ghost.remove(); beam.remove();
        fromEl.classList.remove('power-source'); toEl.classList.remove('power-target');
        boardEl.classList.remove('animating','power-hit');
        done&&done();
      }

      const beamAnim = beam.animate ? beam.animate([
        {opacity:0, transform:`rotate(${angle}deg) scaleX(.001)`, offset:0},
        {opacity:1, transform:`rotate(${angle}deg) scaleX(1)`, offset:.24},
        {opacity:.9, transform:`rotate(${angle}deg) scaleX(1)`, offset:.62},
        {opacity:0, transform:`rotate(${angle}deg) scaleX(1)`, offset:1}
      ], {duration:duration+95, easing:'cubic-bezier(.18,.86,.16,1)', fill:'forwards'}) : null;

      if(ghost.animate){
        const lift=Math.min(18,Math.max(8,size*.14));
        const anim=ghost.animate([
          {transform:'translate3d(0,0,0) scale(1)', opacity:1, offset:0},
          {transform:`translate3d(${dx*.18}px,${dy*.18-lift}px,0) scale(1.1)`, opacity:1, offset:.18},
          {transform:`translate3d(${dx*.72}px,${dy*.72-lift*.35}px,0) scale(1.05)`, opacity:1, offset:.72},
          {transform:`translate3d(${dx}px,${dy}px,0) scale(1)`, opacity:1, offset:1}
        ], {duration, easing:'cubic-bezier(.14,.9,.14,1)', fill:'forwards'});
        anim.onfinish=finish;
      } else {
        requestAnimationFrame(()=>{
          beam.style.opacity='1'; beam.style.transform=`rotate(${angle}deg) scaleX(1)`;
          ghost.style.transition=`transform ${duration}ms cubic-bezier(.14,.9,.14,1)`;
          ghost.style.transform=`translate3d(${dx}px,${dy}px,0)`;
        });
        setTimeout(finish,duration+120);
      }
    }catch(e){ done&&done(); }
  }

'''
s = s[:start] + new_anim + s[end:]

p.write_text(s, encoding='utf-8')
print('Applied smooth power move FX.')
