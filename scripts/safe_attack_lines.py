from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace('</style>', '''
.attack-overlay{position:absolute;inset:0;z-index:900;pointer-events:none;overflow:visible!important}
.board{position:relative!important;overflow:visible!important;isolation:isolate!important}
.attack-line{z-index:901!important}
.square.last-from::after,.square.last-to::after{background:rgba(255,255,255,.06)!important;box-shadow:none!important}
</style>''')

s = s.replace("""    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    const bs=boardEl.getBoundingClientRect();""", """    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    let overlay=boardEl.querySelector('.attack-overlay');
    if(!overlay){ overlay=document.createElement('div'); overlay.className='attack-overlay'; boardEl.appendChild(overlay); }
    const bs=boardEl.getBoundingClientRect();""")

s = s.replace('      boardEl.appendChild(line);', '      overlay.appendChild(line);')

p.write_text(s, encoding='utf-8')
print('overlay append')
