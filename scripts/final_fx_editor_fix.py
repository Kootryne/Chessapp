from pathlib import Path

# Even softer native haptics.
java = Path('app/src/main/java/com/kootryne/chessduel/MainActivity.java')
jsrc = java.read_text(encoding='utf-8')
jsrc = jsrc.replace('VibrationEffect.createOneShot(duration, 42)', 'VibrationEffect.createOneShot(duration, 24)')
java.write_text(jsrc, encoding='utf-8')

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Stronger CSS overrides: editor palette visible in fullscreen, threat glow outside square, real red attack beams.
s = s.replace('</style>', '''
/* final editor + threat path fixes */
.board{position:relative!important;overflow:visible!important}
.square.threatened-by-last::before{content:''!important;position:absolute!important;inset:-7%!important;border-radius:0!important;border:4px solid rgba(255,35,70,.98)!important;background:transparent!important;box-shadow:0 0 22px rgba(255,35,70,.98),0 0 42px rgba(255,35,70,.45)!important;z-index:12!important;pointer-events:none!important;animation:none!important}
.attack-line{position:absolute!important;height:var(--beam-h,64px)!important;transform-origin:0 50%!important;z-index:9!important;pointer-events:none!important;border-radius:0!important;background:linear-gradient(90deg,rgba(255,35,70,0),rgba(255,35,70,.52),rgba(255,35,70,.94),rgba(255,255,255,.50),rgba(255,35,70,.80),rgba(255,35,70,0))!important;box-shadow:0 0 18px rgba(255,35,70,.95),0 0 50px rgba(255,35,70,.42)!important;mix-blend-mode:screen!important;opacity:.92!important}
.attack-line::after{content:'';position:absolute;left:2%;right:2%;top:50%;height:3px;transform:translateY(-50%);background:rgba(255,245,245,.9);box-shadow:0 0 10px rgba(255,255,255,.9)}
body.editor-mode .editor-tools{display:grid!important}
body.editor-mode.board-only .editor-tools{position:fixed!important;left:8px!important;right:8px!important;bottom:calc(206px + env(safe-area-inset-bottom))!important;z-index:95!important;display:grid!important;grid-template-columns:1fr auto auto!important;align-items:center!important;gap:8px!important;max-height:96px!important;overflow:hidden!important;padding:8px!important;border-radius:16px!important;background:rgba(8,13,30,.86)!important;border:1px solid rgba(255,255,255,.16)!important;box-shadow:0 18px 50px rgba(0,0,0,.45)!important;backdrop-filter:blur(16px)!important}
body.editor-mode.board-only .editor-title{display:none!important}
body.editor-mode.board-only .editor-palette{display:flex!important;gap:6px!important;overflow-x:auto!important;flex-wrap:nowrap!important;min-width:0!important;scrollbar-width:none!important}
body.editor-mode.board-only .editor-piece{flex:0 0 39px!important;width:39px!important;height:39px!important;font-size:1.28rem!important;border-radius:10px!important}
body.editor-mode.board-only #editorClearBtn,body.editor-mode.board-only #editorStartBtn{width:auto!important;min-width:58px!important;font-size:.68rem!important;padding:8px!important}
body.editor-mode.board-only .board-card{padding-bottom:calc(310px + env(safe-area-inset-bottom))!important}
body.editor-mode.board-only .board-wrap{width:min(100vw,calc(100vh - 330px - env(safe-area-inset-bottom)))!important;height:min(100vw,calc(100vh - 330px - env(safe-area-inset-bottom)))!important}
</style>''')

# Ensure editor mode toggles a body class and palette gets built when entering editor.
s = s.replace("""    const editor = mode==='editor';""", """    const editor = mode==='editor';
    document.body.classList.toggle('editor-mode', editor);""")
s = s.replace("""    if(editorTools) editorTools.classList.toggle('hidden', !editor);""", """    if(editorTools) editorTools.classList.toggle('hidden', !editor);
    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();""")

# Replace attack line drawing with a thick square-path beam like the reference.
start = s.find('  function drawAttackLines(info){')
end = s.find('  function setupEditorPalette(){')
if start != -1 and end != -1:
    new_draw = r'''  function drawAttackLines(info){
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    const bs=boardEl.getBoundingClientRect();
    const fs=from.getBoundingClientRect();
    const sx=fs.left-bs.left+fs.width/2, sy=fs.top-bs.top+fs.height/2;
    const h=Math.max(18, fs.width*.82);
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
      boardEl.appendChild(line);
    }
  }

'''
    s = s[:start] + new_draw + s[end:]

# Force the move beam to recolor from the moving piece, separate from red attack beams.
s = s.replace("beam.className='power-beam';", "beam.className=`power-beam moving-${pieceType(piece).toLowerCase()}`;")
s = s.replace("""      beam.style.background=`linear-gradient(90deg,rgba(0,0,0,0),${fx.soft},${fx.beam},${fx.core},${fx.beam},rgba(0,0,0,0))`;
      beam.style.boxShadow=`0 0 16px ${fx.main},0 0 46px ${fx.soft}${fx.shadow?`,0 0 22px ${fx.shadow}`:''}`;""", """      beam.style.setProperty('background', `linear-gradient(90deg,rgba(0,0,0,0),${fx.soft},${fx.beam},${fx.core},${fx.beam},rgba(0,0,0,0))`, 'important');
      beam.style.setProperty('box-shadow', `0 0 16px ${fx.main},0 0 46px ${fx.soft}${fx.shadow?`,0 0 22px ${fx.shadow}`:''}`, 'important');""")

p.write_text(s, encoding='utf-8')
print('Fixed editor palette visibility, attack path beams, outside-square threat glow, and move beam color separation.')
