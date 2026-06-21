from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Final visual fix: move source/target glow should use the moved piece color, and attack paths must render above the board.
s = s.replace('</style>', '''
/* final move-color + attack-overlay fix */
.power-source,.power-target{box-shadow:inset 0 0 0 4px var(--move-color,#facc15), inset 0 0 34px var(--move-soft,rgba(250,204,21,.24))!important}
.power-target{box-shadow:inset 0 0 0 5px var(--move-color,#facc15), inset 0 0 44px var(--move-soft,rgba(250,204,21,.32))!important}
.attack-overlay{position:absolute;inset:0;z-index:999;pointer-events:none;overflow:visible!important}
.attack-line{position:absolute!important;height:var(--beam-h,70px)!important;transform-origin:0 50%!important;z-index:1000!important;pointer-events:none!important;border-radius:0!important;background:linear-gradient(90deg,rgba(255,35,70,0),rgba(255,35,70,.45),rgba(255,35,70,.92),rgba(255,255,255,.62),rgba(255,35,70,.82),rgba(255,35,70,0))!important;box-shadow:0 0 22px rgba(255,35,70,.98),0 0 58px rgba(255,35,70,.52)!important;mix-blend-mode:screen!important;opacity:.96!important}
.attack-line::after{content:'';position:absolute;left:2%;right:2%;top:50%;height:3px;transform:translateY(-50%);background:rgba(255,255,255,.92);box-shadow:0 0 12px rgba(255,255,255,.95)}
.board{position:relative!important;isolation:isolate!important;overflow:visible!important}
.square{z-index:1}.piece-wrap{z-index:4}.square.threatened-by-last::before{z-index:20!important}
</style>''')

# Make source and target squares use the moved piece color variables.
s = s.replace("""      fromEl.style.setProperty('--threat-color', fx.main);
      toEl.style.setProperty('--threat-color', fx.main);""", """      fromEl.style.setProperty('--threat-color', fx.main);
      toEl.style.setProperty('--threat-color', fx.main);
      fromEl.style.setProperty('--move-color', fx.main);
      toEl.style.setProperty('--move-color', fx.main);
      fromEl.style.setProperty('--move-soft', fx.soft);
      toEl.style.setProperty('--move-soft', fx.soft);""")

# Replace attack line renderer to use an overlay layer above all squares/pieces.
start = s.find('  function drawAttackLines(info){')
end = s.find('  function ensureFloatingEditorDock(){')
if start != -1 and end != -1:
    new_fn = r'''  function drawAttackLines(info){
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    let overlay=boardEl.querySelector('.attack-overlay');
    if(!overlay){ overlay=document.createElement('div'); overlay.className='attack-overlay'; boardEl.appendChild(overlay); }
    const bs=boardEl.getBoundingClientRect();
    const fs=from.getBoundingClientRect();
    const sx=fs.left-bs.left+fs.width/2, sy=fs.top-bs.top+fs.height/2;
    const h=Math.max(22, fs.width*.88);
    for(const key of info.squares){
      const [r,c]=key.split(',').map(Number);
      const to=squareElAt(r,c); if(!to) continue;
      const ts=to.getBoundingClientRect();
      const tx=ts.left-bs.left+ts.width/2, ty=ts.top-bs.top+ts.height/2;
      const dx=tx-sx, dy=ty-sy, len=Math.hypot(dx,dy), angle=Math.atan2(dy,dx)*180/Math.PI;
      const line=document.createElement('div');
      line.className='attack-line';
      line.style.left=sx+'px';
      line.style.top=(sy-h/2)+'px';
      line.style.width=len+'px';
      line.style.setProperty('--beam-h', h+'px');
      line.style.transform=`rotate(${angle}deg)`;
      overlay.appendChild(line);
    }
  }

'''
    s = s[:start] + new_fn + s[end:]

p.write_text(s, encoding='utf-8')
print('Fixed moved-piece color glows and attack overlay path rendering.')
