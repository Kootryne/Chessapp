from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Only show floating editor dock in fullscreen editor mode; never in normal non-fullscreen UI.
s = s.replace('</style>', '''
/* editor dock visibility + animation lock fix */
#floatingEditorDock{display:none!important;pointer-events:none!important}
body.editor-mode.board-only #floatingEditorDock{display:flex!important;pointer-events:auto!important}
body:not(.board-only) #floatingEditorDock{display:none!important;pointer-events:none!important}
</style>''')

# Explicitly hide/show dock in JS too, not only CSS.
s = s.replace("""    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();
    if(editor) ensureFloatingEditorDock();""", """    if(editor && editorPalette && !editorPalette.children.length) setupEditorPalette();
    const floatingDock=document.getElementById('floatingEditorDock');
    if(editor && boardOnly){ ensureFloatingEditorDock(); }
    if(floatingDock) floatingDock.style.display = (editor && boardOnly) ? 'flex' : 'none';""")

# setBoardOnly should refresh UI so the floating editor dock follows fullscreen state.
s = s.replace("""  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', boardOnly);
    try{ if(boardOnly && document.documentElement.requestFullscreen) document.documentElement.requestFullscreen(); }catch(e){}
    if(!boardOnly){ try{ if(document.fullscreenElement) document.exitFullscreen(); }catch(e){} }
    keepBoardSquare();
  }""", """  function setBoardOnly(on){
    boardOnly=on;
    document.body.classList.toggle('board-only', boardOnly);
    try{ if(boardOnly && document.documentElement.requestFullscreen) document.documentElement.requestFullscreen(); }catch(e){}
    if(!boardOnly){ try{ if(document.fullscreenElement) document.exitFullscreen(); }catch(e){} }
    keepBoardSquare();
    setModeUI();
  }""")

# Add a failsafe so a WebView animation that misses onfinish cannot permanently lock the game.
s = s.replace("""      if(ghost.animate){
        const lift=Math.min(18,Math.max(8,size*.14));
        const anim=ghost.animate([""", """      if(ghost.animate){
        const lift=Math.min(18,Math.max(8,size*.14));
        const anim=ghost.animate([""")
s = s.replace("""        anim.onfinish=finish;
      } else {""", """        anim.onfinish=finish;
        setTimeout(finish, duration+220);
      } else {""")

# If anything still leaves the board locked, clear it before reacting to new clicks or AI loops.
s = s.replace("""function onSquareClick(r,c){
    if(isAnimatingMove) return;""", """function onSquareClick(r,c){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(isAnimatingMove) return;""")
s = s.replace("""  function maybeAIMove(){
    if(aiThinking) return;""", """  function maybeAIMove(){
    if(isAnimatingMove && !document.querySelector('.moving-ghost')){ isAnimatingMove=false; visualMove=null; clearMoveFX(); }
    if(aiThinking) return;""")

p.write_text(s, encoding='utf-8')
print('Fixed editor dock visibility outside fullscreen and added animation lock failsafes.')
