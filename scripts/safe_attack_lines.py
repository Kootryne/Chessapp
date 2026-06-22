from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Add attack-line CSS without touching game logic.
s = s.replace('</style>', '''
/* safe attack line overlay */
.board{position:relative!important;overflow:visible!important;isolation:isolate!important}
.attack-overlay{position:absolute;inset:0;z-index:900;pointer-events:none;overflow:visible!important}
.attack-line{position:absolute!important;height:var(--beam-h,64px)!important;transform-origin:0 50%!important;z-index:901!important;pointer-events:none!important;border-radius:0!important;background:linear-gradient(90deg,rgba(255,35,70,0),rgba(255,35,70,.45),rgba(255,35,70,.92),rgba(255,255,255,.55),rgba(255,35,70,.84),rgba(255,35,70,0))!important;box-shadow:0 0 18px rgba(255,35,70,.95),0 0 52px rgba(255,35,70,.46)!important;mix-blend-mode:screen!important;opacity:.96!important}
.attack-line::after{content:'';position:absolute;left:2%;right:2%;top:50%;height:3px;transform:translateY(-50%);background:rgba(255,255,255,.9);box-shadow:0 0 10px rgba(255,255,255,.9)}
.power-source,.power-target{box-shadow:inset 0 0 0 4px var(--threat-color,#facc15), inset 0 0 34px var(--threat-soft,rgba(250,204,21,.28))!important}
.power-target{box-shadow:inset 0 0 0 5px var(--threat-color,#facc15), inset 0 0 44px var(--threat-soft,rgba(250,204,21,.34))!important}
</style>''')

# Make drawAttackLines use an overlay above squares. Only insert two small changes.
s = s.replace("""    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    const bs=boardEl.getBoundingClientRect();""", """    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    let overlay=boardEl.querySelector('.attack-overlay');
    if(!overlay){ overlay=document.createElement('div'); overlay.className='attack-overlay'; boardEl.appendChild(overlay); }
    const bs=boardEl.getBoundingClientRect();""")

s = s.replace("""      const line=document.createElement('div');
      line.className='attack-line';
      line.style.left=sx+'px'; line.style.top=(sy-h/2)+'px'; line.style.width=len+'px';
      line.style.setProperty('--beam-h', h+'px');
      line.style.transform=`rotate(${angle}deg)`;
      boardEl.appendChild(line);""", """      const line=document.createElement('div');
      line.className='attack-line';
      line.style.left=sx+'px'; line.style.top=(sy-h/2)+'px'; line.style.width=len+'px';
      line.style.setProperty('--beam-h', Math.max(h, fs.width*.88)+'px');
      line.style.transform=`rotate(${angle}deg)`;
      overlay.appendChild(line);""")

p.write_text(s, encoding='utf-8')
print('Safely added attack line overlay without removing helper functions.')
