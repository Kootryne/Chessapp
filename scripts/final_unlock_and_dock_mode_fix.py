from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Board must never become unclickable because of a stale CSS animation class.
s = s.replace('</style>', '''
/* final unlock + dock mode fix */
.board.animating{pointer-events:auto!important}
#floatingEditorDock{display:none!important;pointer-events:none!important}
body.board-only.editor-mode #floatingEditorDock{display:flex!important;pointer-events:auto!important}
body:not(.editor-mode) #floatingEditorDock, body:not(.board-only) #floatingEditorDock{display:none!important;pointer-events:none!important}
</style>''')

# Replace the broken setModeUI dock logic with explicit mode/fullscreen sync.
bad = """    if(editorTools) editorTools.classList.toggle('hidden', !editor);
    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette(); ensureFloatingEditorDock();
    if(editor) ensureFloatingEditorDock();"""
good = """    if(editorTools) editorTools.classList.toggle('hidden', !editor);
    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();
    let floatingDock=document.getElementById('floatingEditorDock');
    if(editor && boardOnly) floatingDock=ensureFloatingEditorDock();
    if(floatingDock){
      const showDock = editor && boardOnly;
      floatingDock.style.display = showDock ? 'flex' : 'none';
      floatingDock.style.pointerEvents = showDock ? 'auto' : 'none';
    }
    document.body.classList.toggle('editor-mode', editor);"""
if bad in s:
    s = s.replace(bad, good)
else:
    s = s.replace("""    if(editorTools) editorTools.classList.toggle('hidden', !editor);""", """    if(editorTools) editorTools.classList.toggle('hidden', !editor);
    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();
    let floatingDock=document.getElementById('floatingEditorDock');
    if(editor && boardOnly) floatingDock=ensureFloatingEditorDock();
    if(floatingDock){
      const showDock = editor && boardOnly;
      floatingDock.style.display = showDock ? 'flex' : 'none';
      floatingDock.style.pointerEvents = showDock ? 'auto' : 'none';
    }""")

# Make sure changing away from editor immediately clears editor mode state and hides dock.
s = s.replace("""modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); mode=modeSelect.value; if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""", """modeSelect.addEventListener('change', ()=>{ const oldMode=mode; if(oldMode==='editor') saveCustomStartFromEditor(); mode=modeSelect.value; if(mode!=='editor'){ document.body.classList.remove('editor-mode'); const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } } if(mode!=='bot') botsPaused=false; aiColor = mode==='bot' ? game.turn : other(humanColor); setModeUI(); draw(); maybeAIMove(); });""")

# setBoardOnly should also hide dock when leaving fullscreen.
s = s.replace("""  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', on);
    setTimeout(()=>{ keepBoardSquare(); draw(); setModeUI(); }, 40);
  }""", """  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', on);
    if(!on){ const d=document.getElementById('floatingEditorDock'); if(d){ d.style.display='none'; d.style.pointerEvents='none'; } }
    setTimeout(()=>{ keepBoardSquare(); draw(); setModeUI(); }, 40);
  }""")

# If the board gets stuck with .animating, clear that on every draw before squares are created.
s = s.replace("""  function draw(){
    keepBoardSquare();""", """  function draw(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    keepBoardSquare();""")

p.write_text(s, encoding='utf-8')
print('Applied final editor dock mode sync and board unlock fixes.')
