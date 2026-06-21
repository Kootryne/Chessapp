from pathlib import Path

# Softer native haptics bridge amplitude.
java = Path('app/src/main/java/com/kootryne/chessduel/MainActivity.java')
jsrc = java.read_text(encoding='utf-8')
jsrc = jsrc.replace('vibrator.vibrate(VibrationEffect.createOneShot(duration, VibrationEffect.DEFAULT_AMPLITUDE));', 'vibrator.vibrate(VibrationEffect.createOneShot(duration, 42));')
java.write_text(jsrc, encoding='utf-8')

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Add editor mode option.
s = s.replace('<option value="bot">Bot vs bot</option>', '<option value="bot">Bot vs bot</option>\n          <option value="editor">Editor</option>')

# Add editor tools panel after tip row.
s = s.replace('<div class="tip" id="aiTip">AI: off</div>', '<div class="tip" id="aiTip">AI: off</div>\n        <div class="editor-tools hidden" id="editorTools">\n          <div class="editor-title">Editor: tap a piece, then tap a square. Tap a piece on the board to remove it.</div>\n          <div class="editor-palette" id="editorPalette"></div>\n          <button id="editorClearBtn">Clear</button>\n          <button id="editorStartBtn">Start position</button>\n        </div>')

# CSS: rectangular threat glow, red attack lines, better fullscreen bottom controls, editor palette.
s = s.replace('</style>', '''
/* editor + attack threat FX + cleaner fullscreen controls */
.square.threatened-by-last::before{border-radius:0!important;border:3px solid rgba(255,45,80,.95)!important;background:linear-gradient(180deg,rgba(255,45,80,.30),rgba(255,45,80,.10))!important;box-shadow:0 0 24px rgba(255,45,80,.95), inset 0 0 22px rgba(255,45,80,.30)!important;animation:none!important}
.square.threatened-by-last .piece{filter:drop-shadow(0 0 16px rgba(255,45,80,.98)) drop-shadow(0 5px 7px rgba(0,0,0,.40))!important}
.attack-line{position:absolute;height:16px;transform-origin:0 50%;z-index:2;pointer-events:none;border-radius:0;background:linear-gradient(90deg,rgba(255,40,75,0),rgba(255,40,75,.92),rgba(255,255,255,.74),rgba(255,40,75,.78));box-shadow:0 0 16px rgba(255,40,75,.92),0 0 42px rgba(255,40,75,.45);mix-blend-mode:screen;opacity:.9}
.attack-line::after{content:'';position:absolute;left:0;right:0;top:50%;height:2px;transform:translateY(-50%);background:rgba(255,255,255,.88);box-shadow:0 0 10px rgba(255,255,255,.9)}
.editor-tools{grid-column:1/-1;display:grid;gap:8px;margin-top:10px;padding:10px;border-radius:16px;background:rgba(15,23,42,.48);border:1px solid rgba(255,255,255,.10)}
.editor-tools.hidden{display:none!important}.editor-title{font-size:.82rem;color:var(--muted)}.editor-palette{display:flex;gap:6px;flex-wrap:wrap}.editor-piece{width:38px;height:38px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.12);display:grid;place-items:center;font-size:1.45rem;box-shadow:0 6px 18px rgba(0,0,0,.22)}.editor-piece.active{outline:3px solid rgba(34,211,238,.8);background:rgba(34,211,238,.22)}
body.board-only .hero{max-height:190px!important;min-height:unset!important;bottom:max(10px,env(safe-area-inset-bottom))!important;overflow-y:auto!important;padding:10px!important}
body.board-only .hero .controls{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:7px!important;overflow:visible!important;min-height:unset!important}
body.board-only .hero .field{display:block!important;min-width:0!important}body.board-only .hero .field.hidden{display:none!important}body.board-only .hero .field label{display:none!important}
body.board-only .hero select,body.board-only .hero button{width:100%!important;max-width:none!important;min-width:0!important;min-height:38px!important;padding:8px 7px!important;font-size:.70rem!important;line-height:1.05!important;text-overflow:ellipsis;overflow:hidden}
body.board-only .board-card{padding-bottom:calc(205px + env(safe-area-inset-bottom))!important}
body.board-only .board-wrap{width:min(100vw,calc(100vh - 225px - env(safe-area-inset-bottom)))!important;height:min(100vw,calc(100vh - 225px - env(safe-area-inset-bottom)))!important}
</style>''')

# Add editor state vars.
s = s.replace('let isAnimatingMove=false, visualMove=null;', 'let isAnimatingMove=false, visualMove=null;\n  let editorPiece=null;')

# Add DOM refs. Use append after existing fullscreen const or pause const.
s = s.replace("const promotionPicker=$('promotionPicker');", "const promotionPicker=$('promotionPicker');\n  const editorTools=$('editorTools'), editorPalette=$('editorPalette'), editorClearBtn=$('editorClearBtn'), editorStartBtn=$('editorStartBtn');")

# Replace haptic function to be softer and longer. Also avoid double-pulses after normal/capture.
s = s.replace("""  function haptic(kind){
    if(mode==='bot') return;
    try{
      if(window.AndroidHaptics && AndroidHaptics.vibrate){
        AndroidHaptics.vibrate(kind==='mate'?90:kind==='capture'?45:kind==='check'?55:22);
        return;
      }
      if(navigator.vibrate){
        if(kind==='mate') navigator.vibrate([60,35,95]);
        else if(kind==='capture') navigator.vibrate(45);
        else if(kind==='check') navigator.vibrate(55);
        else navigator.vibrate(22);
      }
    }catch(e){}
  }
  function hapticForMove(before, move, after){
    if(after.result?.type==='checkmate') return haptic('mate');
    if(move.capture || move.enPassantCapture) return haptic('capture');
    if(isInCheck(after, after.turn)) return haptic('check');
    haptic('move');
  }""", """  function haptic(kind){
    if(mode==='bot') return;
    try{
      const dur = kind==='mate'?520:kind==='capture'?360:kind==='check'?390:kind==='edit'?140:285;
      if(window.AndroidHaptics && AndroidHaptics.vibrate){ AndroidHaptics.vibrate(dur); return; }
      if(navigator.vibrate) navigator.vibrate(dur);
    }catch(e){}
  }
  function hapticForMove(before, move, after){
    if(after.result?.type==='checkmate') return haptic('mate');
    if(isInCheck(after, after.turn)) return haptic('check');
  }""")

# Editor helpers before draw.
editor_code = r'''
  function setupEditorPalette(){
    if(!editorPalette) return;
    editorPalette.innerHTML='';
    const pieces=['wK','wQ','wR','wB','wN','wP','bK','bQ','bR','bB','bN','bP','erase'];
    for(const code of pieces){
      const b=document.createElement('button');
      b.className='editor-piece';
      b.type='button';
      b.dataset.piece=code;
      b.textContent=code==='erase'?'✕':PIECE_ICON[pieceColor(code)][pieceType(code)];
      b.addEventListener('click',()=>{
        editorPiece=code;
        [...editorPalette.children].forEach(x=>x.classList.toggle('active',x===b));
        haptic('edit');
      });
      editorPalette.appendChild(b);
    }
  }
  function editorClickSquare(r,c){
    if(mode!=='editor') return false;
    game.result=null;
    selected=null; legalTargets=[]; history=[]; moveTexts=[];
    if(editorPiece && editorPiece!=='erase') game.board[r][c]=editorPiece;
    else game.board[r][c]=null;
    haptic('edit');
    draw();
    return true;
  }
  function clearEditorBoard(){
    game.board=Array.from({length:8},()=>Array(8).fill(null));
    game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[];
    haptic('edit'); draw();
  }

'''
s = s.replace('  function draw(){', editor_code + '  function draw(){')

# In draw, add attack line rendering after all squares are appended.
# Find end of nested loops before status update. Use a stable snippet.
s = s.replace("""    updateStatus();""", """    drawAttackLines(threatenedInfo);
    updateStatus();""", 1)

attack_code = r'''
  function drawAttackLines(info){
    if(!info || !info.squares || !info.squares.size) return;
    const last=history[history.length-1]?.move;
    if(!last) return;
    const from=squareElAt(last.to[0],last.to[1]);
    if(!from) return;
    const bs=boardEl.getBoundingClientRect();
    const fs=from.getBoundingClientRect();
    const sx=fs.left-bs.left+fs.width/2, sy=fs.top-bs.top+fs.height/2;
    for(const key of info.squares){
      const [r,c]=key.split(',').map(Number);
      const to=squareElAt(r,c); if(!to) continue;
      const ts=to.getBoundingClientRect();
      const tx=ts.left-bs.left+ts.width/2, ty=ts.top-bs.top+ts.height/2;
      const dx=tx-sx, dy=ty-sy, len=Math.hypot(dx,dy), angle=Math.atan2(dy,dx)*180/Math.PI;
      const line=document.createElement('div');
      line.className='attack-line';
      line.style.left=sx+'px'; line.style.top=(sy-8)+'px'; line.style.width=len+'px';
      line.style.transform=`rotate(${angle}deg)`;
      boardEl.appendChild(line);
    }
  }

'''
s = s.replace('  function setupEditorPalette(){', attack_code + '  function setupEditorPalette(){')

# Make threatened square red, while move beam remains piece-colored. Replace dynamic threat vars with fixed red.
s = s.replace("""        if(threatenedInfo.squares.has(`${r},${c}`)){
          sq.classList.add('threatened-by-last');
          if(threatenedInfo.colors){
            sq.style.setProperty('--threat-color', threatenedInfo.colors.main);
            sq.style.setProperty('--threat-soft', threatenedInfo.colors.soft);
            sq.style.setProperty('--threat-softer', threatenedInfo.colors.soft.replace('.30','.08').replace('.32','.08').replace('.34','.09'));
          }
        }""", """        if(threatenedInfo.squares.has(`${r},${c}`)){
          sq.classList.add('threatened-by-last');
          sq.style.setProperty('--threat-color', '#ff2d50');
          sq.style.setProperty('--threat-soft', 'rgba(255,45,80,.30)');
          sq.style.setProperty('--threat-softer', 'rgba(255,45,80,.08)');
        }""")

# onSquareClick: editor should intercept before normal chess.
s = s.replace('function onSquareClick(r,c){\n    if(isAnimatingMove) return;', 'function onSquareClick(r,c){\n    if(isAnimatingMove) return;\n    if(mode===\'editor\'){ editorClickSquare(r,c); return; }')

# setModeUI: show editor tools and mode text.
s = s.replace("const bot = mode==='bot';", "const bot = mode==='bot';\n    const editor = mode==='editor';")
s = s.replace("pauseBotsBtn.classList.toggle('hidden', !bot);", "pauseBotsBtn.classList.toggle('hidden', !bot);\n    if(editorTools) editorTools.classList.toggle('hidden', !editor);")
s = s.replace("modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';", "modeTip.textContent = editor ? 'Mode: editor' : bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';")
s = s.replace("aiTip.textContent = bot ?", "aiTip.textContent = editor ? 'Editor: build any position' : bot ?")

# maybeAIMove should not run in editor.
s = s.replace("if((mode!=='ai' && mode!=='bot') || game.result || mode==='train' || (mode==='bot' && botsPaused)) return;", "if((mode!=='ai' && mode!=='bot') || game.result || mode==='train' || mode==='editor' || (mode==='bot' && botsPaused)) return;")
s = s.replace("if((mode!=='ai' && mode!=='bot') || game.result || (mode==='bot' && botsPaused)) return;", "if((mode!=='ai' && mode!=='bot') || game.result || mode==='editor' || (mode==='bot' && botsPaused)) return;")

# Event listeners for editor buttons and init palette.
s = s.replace("$('newBtn').addEventListener('click', resetGame);", "$('newBtn').addEventListener('click', resetGame);\n  if(editorClearBtn) editorClearBtn.addEventListener('click', clearEditorBoard);\n  if(editorStartBtn) editorStartBtn.addEventListener('click', ()=>{game=startPosition(); game.result=null; history=[]; moveTexts=[]; selected=null; legalTargets=[]; haptic('edit'); draw();});")
s = s.replace("setModeUI();\n  updateLearnTip();", "setupEditorPalette();\n  setModeUI();\n  if(typeof updateLearnTip==='function') updateLearnTip();")
s = s.replace("setModeUI();\n  resetGame();", "setupEditorPalette();\n  setModeUI();\n  resetGame();")

p.write_text(s, encoding='utf-8')
print('Added editor mode, softer long haptics, attack lines, and responsive fullscreen controls.')
