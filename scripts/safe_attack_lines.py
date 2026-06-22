from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace('</style>', '''
.square.threatened-by-last::before{content:"";position:absolute;inset:0;border-radius:0!important;border:2px solid rgba(255,70,110,.96)!important;background:rgba(255,35,70,.08)!important;box-shadow:0 0 12px rgba(255,60,110,.55), inset 0 0 14px rgba(255,60,110,.20)!important;z-index:2;pointer-events:none;animation:none!important}
.square.threatened-by-last .piece{filter:drop-shadow(0 0 10px rgba(255,70,110,.78)) drop-shadow(0 5px 7px rgba(0,0,0,.38))!important}
.square.attack-source::after,.square.attack-path-h::after,.square.attack-path-v::after,.square.attack-path-d1::after,.square.attack-path-d2::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;mix-blend-mode:screen}
.square.attack-source::after{background:radial-gradient(circle,rgba(255,50,85,.38),rgba(255,20,60,.12) 60%,transparent 76%);box-shadow:inset 0 0 12px rgba(255,45,80,.35),0 0 10px rgba(255,45,80,.30)}
.square.attack-path-h::after{background:linear-gradient(90deg,transparent 0 17%,rgba(255,35,70,.10) 17% 31%,rgba(255,45,85,.82) 42% 58%,rgba(255,35,70,.10) 69% 83%,transparent 83% 100%);box-shadow:0 0 10px rgba(255,30,70,.24), inset 0 0 8px rgba(255,30,70,.10)}
.square.attack-path-v::after{background:linear-gradient(180deg,transparent 0 17%,rgba(255,35,70,.10) 17% 31%,rgba(255,45,85,.82) 42% 58%,rgba(255,35,70,.10) 69% 83%,transparent 83% 100%);box-shadow:0 0 10px rgba(255,30,70,.24), inset 0 0 8px rgba(255,30,70,.10)}
.square.attack-path-d1::after{background:linear-gradient(135deg,transparent 0 27%,rgba(255,35,70,.12) 36% 41%,rgba(255,45,85,.86) 45% 55%,rgba(255,35,70,.12) 59% 64%,transparent 73% 100%);box-shadow:0 0 10px rgba(255,30,70,.24), inset 0 0 8px rgba(255,30,70,.10)}
.square.attack-path-d2::after{background:linear-gradient(45deg,transparent 0 27%,rgba(255,35,70,.12) 36% 41%,rgba(255,45,85,.86) 45% 55%,rgba(255,35,70,.12) 59% 64%,transparent 73% 100%);box-shadow:0 0 10px rgba(255,30,70,.24), inset 0 0 8px rgba(255,30,70,.10)}
.attack-svg,.attack-debug-badge{display:none!important}
</style>''')

insert = r'''
  function pathSquaresBetween(from,to){
    const dr=to[0]-from[0], dc=to[1]-from[1];
    const adr=Math.abs(dr), adc=Math.abs(dc);
    let sr=0, sc=0, cls='';
    if(dr===0 && dc!==0){ sr=0; sc=Math.sign(dc); cls='attack-path-h'; }
    else if(dc===0 && dr!==0){ sr=Math.sign(dr); sc=0; cls='attack-path-v'; }
    else if(adr===adc && adr>0){ sr=Math.sign(dr); sc=Math.sign(dc); cls=(Math.sign(dr)===Math.sign(dc))?'attack-path-d1':'attack-path-d2'; }
    else return [];
    const out=[];
    let r=from[0], c=from[1];
    while(true){
      out.push([r,c,cls]);
      if(r===to[0] && c===to[1]) break;
      r+=sr; c+=sc;
      if(r<0||r>7||c<0||c>7) break;
    }
    return out;
  }

'''
needle = '\n\n\n  function drawAttackLines(info){'
if needle in s:
    s = s.replace(needle, '\n' + insert + '  function drawAttackLines(info){', 1)

start = s.index('  function drawAttackLines(info){')
end = s.index('\n\n  function kingCount', start)
new = r'''  function drawAttackLines(info){
    boardEl.querySelectorAll('.attack-svg,.attack-debug-badge').forEach(e=>e.remove());
    boardEl.querySelectorAll('.attack-source,.attack-path-h,.attack-path-v,.attack-path-d1,.attack-path-d2').forEach(e=>e.classList.remove('attack-source','attack-path-h','attack-path-v','attack-path-d1','attack-path-d2'));
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const fromSq=squareElAt(last.to[0],last.to[1]);
    if(fromSq) fromSq.classList.add('attack-source');
    for(const key of info.squares){
      const [r,c]=key.split(',').map(Number);
      const path=pathSquaresBetween(last.to,[r,c]);
      for(const [pr,pc,cls] of path){
        const sq=squareElAt(pr,pc);
        if(!sq) continue;
        if(pr===last.to[0] && pc===last.to[1]) continue;
        if(pr===r && pc===c) continue;
        sq.classList.add(cls);
      }
    }
  }
'''
s = s[:start] + new + s[end:]
s = s.replace('    updateLabels();\n    keepBoardSquare();', '    drawAttackLines(threatenedInfo);\n    updateLabels();\n    keepBoardSquare();')

p.write_text(s, encoding='utf-8')
print('square path attack glow')
