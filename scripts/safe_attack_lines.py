from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace('</style>', '''
.board{position:relative!important;overflow:visible!important;isolation:isolate!important}
.attack-svg{position:absolute;left:0;top:0;width:100%;height:100%;z-index:9999!important;pointer-events:none;overflow:visible!important}
.attack-debug-badge{position:absolute;left:6px;top:6px;z-index:10000;background:rgba(220,38,38,.92);color:white;border-radius:999px;padding:3px 8px;font:700 11px system-ui;pointer-events:none;box-shadow:0 0 14px rgba(220,38,38,.65)}
.square.threatened-by-last::before{border:2px solid rgba(255,35,70,.7)!important;background:rgba(255,35,70,.06)!important;box-shadow:0 0 10px rgba(255,35,70,.35)!important}
.square.last-from::after,.square.last-to::after{background:rgba(255,255,255,.04)!important;box-shadow:none!important}
</style>''')

start = s.index('  function drawAttackLines(info){')
end = s.index('\n\n  function kingCount', start)
new = r'''  function drawAttackLines(info){
    boardEl.querySelectorAll('.attack-svg,.attack-debug-badge').forEach(e=>e.remove());
    const count = info && info.squares ? info.squares.size : 0;
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    const bs=boardEl.getBoundingClientRect();
    const fs=from.getBoundingClientRect();
    const sx=fs.left-bs.left+fs.width/2, sy=fs.top-bs.top+fs.height/2;
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('class','attack-svg');
    svg.setAttribute('viewBox',`0 0 ${bs.width} ${bs.height}`);
    svg.setAttribute('preserveAspectRatio','none');
    const badge=document.createElement('div');
    badge.className='attack-debug-badge';
    badge.textContent='lines: '+count;
    boardEl.appendChild(svg);
    boardEl.appendChild(badge);
    for(const key of info.squares){
      const [r,c]=key.split(',').map(Number);
      const to=squareElAt(r,c); if(!to) continue;
      const ts=to.getBoundingClientRect();
      const tx=ts.left-bs.left+ts.width/2, ty=ts.top-bs.top+ts.height/2;
      const glow=document.createElementNS('http://www.w3.org/2000/svg','line');
      glow.setAttribute('x1',sx); glow.setAttribute('y1',sy); glow.setAttribute('x2',tx); glow.setAttribute('y2',ty);
      glow.setAttribute('stroke','rgba(255,0,60,.38)');
      glow.setAttribute('stroke-width',Math.max(22,fs.width*.30));
      glow.setAttribute('stroke-linecap','round');
      svg.appendChild(glow);
      const line=document.createElementNS('http://www.w3.org/2000/svg','line');
      line.setAttribute('x1',sx); line.setAttribute('y1',sy); line.setAttribute('x2',tx); line.setAttribute('y2',ty);
      line.setAttribute('stroke','#ff003c');
      line.setAttribute('stroke-width',Math.max(8,fs.width*.11));
      line.setAttribute('stroke-linecap','round');
      svg.appendChild(line);
      const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');
      dot.setAttribute('cx',tx); dot.setAttribute('cy',ty); dot.setAttribute('r',Math.max(7,fs.width*.10));
      dot.setAttribute('fill','#ff003c');
      svg.appendChild(dot);
    }
  }
'''
s = s[:start] + new + s[end:]
s = s.replace('    updateLabels();\n    keepBoardSquare();', '    drawAttackLines(threatenedInfo);\n    updateLabels();\n    keepBoardSquare();')

p.write_text(s, encoding='utf-8')
print('svg debug lines called')
