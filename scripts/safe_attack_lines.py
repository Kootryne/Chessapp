from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Keep only the board style selector. No attack display, no bot animation setting UI.
s = s.replace("""        </select>
      </div>
      <div class="field" id="sideField">""", """        </select>
      </div>
      <div class="field" id="boardStyleField">
        <label for="boardStyleSelect">Board style</label>
        <select id="boardStyleSelect">
          <option value="bright">Bright board</option>
          <option value="dark">Dark board</option>
        </select>
      </div>
      <div class="field" id="sideField">""", 1)

s = s.replace('</style>', '''
body[data-board-style="bright"]{--light:#f1ddb5;--dark:#9f8058}
body[data-board-style="dark"]{--light:#b8b1a7;--dark:#292a2e}
body[data-board-style="dark"] .square.white .piece{color:#f8fafc;text-shadow:0 2px 0 rgba(20,20,20,.65),0 0 18px rgba(255,255,255,.34)}
body[data-board-style="dark"] .square.black .piece{color:#1b2128;text-shadow:0 1px 0 rgba(255,255,255,.20),0 0 14px rgba(0,0,0,.45)}
.attack-beam,.attack-svg,.attack-debug-badge{display:none!important}
.square.threatened-by-last::before,.square.attack-source::after,.square.attack-path-h::after,.square.attack-path-v::after,.square.attack-path-d1::after,.square.attack-path-d2::after{display:none!important;content:none!important}
.square.threatened-by-last .piece{filter:drop-shadow(0 5px 6px rgba(0,0,0,.33))!important}
</style>''')

# Disable attack display fully.
start = s.index('  function drawAttackLines(info){')
end = s.index('\n\n  function kingCount', start)
s = s[:start] + r'''  function drawAttackLines(info){
    boardEl.querySelectorAll('.attack-beam,.attack-svg,.attack-debug-badge').forEach(e=>e.remove());
    boardEl.querySelectorAll('.attack-source,.attack-path-h,.attack-path-v,.attack-path-d1,.attack-path-d2').forEach(e=>e.classList.remove('attack-source','attack-path-h','attack-path-v','attack-path-d1','attack-path-d2'));
  }
''' + s[end:]
s = s.replace('    updateLabels();\n    keepBoardSquare();', '    drawAttackLines(threatenedInfo);\n    updateLabels();\n    keepBoardSquare();')

# Board style UI only.
s = s.replace("""const modeSelect=$('modeSelect'), sideSelect=$('sideSelect'), thinkSelect=$('thinkSelect');""", """const modeSelect=$('modeSelect'), sideSelect=$('sideSelect'), thinkSelect=$('thinkSelect'), boardStyleSelect=$('boardStyleSelect');""")
s = s.replace("""  const PST = {""", """  function setBoardStyle(style){
    const chosen = style === 'dark' ? 'dark' : 'bright';
    document.body.dataset.boardStyle = chosen;
    if(boardStyleSelect) boardStyleSelect.value = chosen;
    try{ localStorage.setItem('chessDuelBoardStyle', chosen); }catch(e){}
  }
  setBoardStyle((()=>{ try{return localStorage.getItem('chessDuelBoardStyle')||'bright'}catch(e){return 'bright'} })());
  if(boardStyleSelect) boardStyleSelect.addEventListener('change', ()=>setBoardStyle(boardStyleSelect.value));

  const PST = {""")

# Cancel stale bot/AI searches when starting a new game so double New Game does not stack old searches.
s = s.replace("""function resetGame(){
    clearMoveFX();""", """function cancelAIWork(){
    aiJob++;
    aiThinking=false;
    if(aiWorker){ try{ aiWorker.terminate(); }catch(e){} aiWorker=null; }
  }

  function resetGame(){
    clearMoveFX();
    cancelAIWork();""")

# Bots/AI should still animate, but the next move should not wait for the animation to finish.
start = s.index('  function doMove(move){')
end = s.index('\n\n  function getAIWorker', start)
s = s[:start] + r'''  function doMove(move){
    const before=deepClone(game);
    const botControlledMove = mode==='bot' || (mode==='ai' && before.turn===aiColor);
    if(isAnimatingMove && !botControlledMove) return;
    const after=applyMove(before, move);
    const moveText = moveToText(before, move, after);
    const hist={game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime, move};
    const finishMove = ()=>{
      history.push(hist);
      game=after;
      moveTexts.push(moveText);
      annotateResult(game);
      applyRepetitionDraw();
      hapticForMove(before, move, game);
      visualMove=null;
      isAnimatingMove=false;
      draw();
      maybeAIMove();
    };
    haptic(move.capture||move.enPassantCapture?'capture':'move');
    selected=null; legalTargets=[];
    if(botControlledMove){
      finishMove();
      try{ animateMoveVisual(before, move, ()=>{}); }catch(e){}
      return;
    }
    isAnimatingMove=true;
    visualMove={from:move.from, to:move.to, capture:!!(move.capture||move.enPassantCapture), piece:before.board[move.from[0]][move.from[1]]};
    draw();
    animateMoveVisual(before, move, finishMove);
  }
''' + s[end:]

p.write_text(s, encoding='utf-8')
print('bot moves animate without waiting; stale AI searches cancelled')
