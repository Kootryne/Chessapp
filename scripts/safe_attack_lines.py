from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

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
