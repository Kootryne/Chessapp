from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace('</style>', '''
.board{position:relative!important;overflow:visible!important;isolation:isolate!important}
.piece-wrap{position:relative;z-index:6!important}
.attack-beam{position:absolute;left:0;top:0;transform-origin:0 50%;pointer-events:none;z-index:3;border-radius:10px;mix-blend-mode:screen;background:linear-gradient(90deg,transparent,rgba(255,45,80,.42) 12%,rgba(255,75,105,.58) 50%,rgba(255,45,80,.42) 88%,transparent);box-shadow:0 0 24px rgba(255,35,70,.70),0 0 60px rgba(255,35,70,.38),inset 0 0 18px rgba(255,255,255,.12);border-top:1px solid rgba(255,210,220,.7);border-bottom:1px solid rgba(255,40,80,.8);opacity:.94}
.attack-beam::before{content:"";position:absolute;inset:-10px 0;border-radius:14px;background:linear-gradient(90deg,transparent,rgba(255,35,70,.26),transparent);filter:blur(10px);z-index:-1}
.attack-beam::after{content:"";position:absolute;left:2%;right:2%;top:50%;height:3px;transform:translateY(-50%);border-radius:999px;background:rgba(255,235,240,.70);box-shadow:0 0 10px rgba(255,235,240,.85)}
.square.threatened-by-last::before{content:"";position:absolute;inset:-2px;border-radius:0!important;border:2px solid rgba(255,75,115,.88)!important;background:rgba(255,35,70,.10)!important;box-shadow:0 0 16px rgba(255,55,90,.70),inset 0 0 18px rgba(255,55,90,.22)!important;z-index:4;pointer-events:none;animation:none!important}
.square.attack-source::after{content:"";position:absolute;inset:-4px;border-radius:0;pointer-events:none;z-index:4;background:radial-gradient(circle,rgba(255,55,90,.42),rgba(255,35,70,.16) 58%,transparent 75%);box-shadow:0 0 22px rgba(255,45,80,.50)}
.attack-svg,.attack-debug-badge{display:none!important}
</style>''')

start = s.index('  function drawAttackLines(info){')
end = s.index('\n\n  function kingCount', start)
new = r'''  function drawAttackLines(info){
    boardEl.querySelectorAll('.attack-beam,.attack-svg,.attack-debug-badge').forEach(e=>e.remove());
    boardEl.querySelectorAll('.attack-source,.attack-path-h,.attack-path-v,.attack-path-d1,.attack-path-d2').forEach(e=>e.classList.remove('attack-source','attack-path-h','attack-path-v','attack-path-d1','attack-path-d2'));
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    from.classList.add('attack-source');
    const bs=boardEl.getBoundingClientRect();
    const fs=from.getBoundingClientRect();
    const sx=fs.left-bs.left+fs.width/2;
    const sy=fs.top-bs.top+fs.height/2;
    const thickness=Math.max(36, fs.width*.84);
    for(const key of info.squares){
      const rc=key.split(',').map(Number);
      const to=squareElAt(rc[0],rc[1]); if(!to) continue;
      const ts=to.getBoundingClientRect();
      const tx=ts.left-bs.left+ts.width/2;
      const ty=ts.top-bs.top+ts.height/2;
      const dx=tx-sx, dy=ty-sy;
      const len=Math.hypot(dx,dy);
      const angle=Math.atan2(dy,dx);
      const beam=document.createElement('div');
      beam.className='attack-beam';
      beam.style.left=sx+'px';
      beam.style.top=sy+'px';
      beam.style.width=len+'px';
      beam.style.height=thickness+'px';
      beam.style.transform=`translateY(-50%) rotate(${angle}rad)`;
      boardEl.appendChild(beam);
    }
  }
'''
s = s[:start] + new + s[end:]
s = s.replace('    updateLabels();\n    keepBoardSquare();', '    drawAttackLines(threatenedInfo);\n    updateLabels();\n    keepBoardSquare();')

p.write_text(s, encoding='utf-8')
print('wide beam attacks')
