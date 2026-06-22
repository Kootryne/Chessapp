from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Keep the board style selector and add bot animation toggle.
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
      <div class="field hidden" id="botWaitField">
        <label for="botWaitSelect">Bot animation</label>
        <select id="botWaitSelect">
          <option value="wait">Wait for animation</option>
          <option value="skip">Skip animation</option>
        </select>
      </div>
      <div class="field" id="sideField">""", 1)

# Only board theme CSS, plus hard-disable any previous attack visuals.
s = s.replace('</style>', '''
body[data-board-style="bright"]{--light:#f1ddb5;--dark:#9f8058}
body[data-board-style="dark"]{--light:#b8b1a7;--dark:#292a2e}
body[data-board-style="dark"] .square.white .piece{color:#f8fafc;text-shadow:0 2px 0 rgba(20,20,20,.65),0 0 18px rgba(255,255,255,.34)}
body[data-board-style="dark"] .square.black .piece{color:#1b2128;text-shadow:0 1px 0 rgba(255,255,255,.20),0 0 14px rgba(0,0,0,.45)}
.attack-beam,.attack-svg,.attack-debug-badge{display:none!important}
.square.threatened-by-last::before,.square.attack-source::after,.square.attack-path-h::after,.square.attack-path-v::after,.square.attack-path-d1::after,.square.attack-path-d2::after{display:none!important;content:none!important}
.square.threatened-by-last .piece{filter:drop-shadow(0 5px 6px rgba(0,0,0,.33))!important}
</style>''')

# Replace the attack drawing function with a cleanup-only no-op.
start = s.index('  function drawAttackLines(info){')
end = s.index('\n\n  function kingCount', start)
new = r'''  function drawAttackLines(info){
    boardEl.querySelectorAll('.attack-beam,.attack-svg,.attack-debug-badge').forEach(e=>e.remove());
    boardEl.querySelectorAll('.attack-source,.attack-path-h,.attack-path-v,.attack-path-d1,.attack-path-d2').forEach(e=>e.classList.remove('attack-source','attack-path-h','attack-path-v','attack-path-d1','attack-path-d2'));
  }
'''
s = s[:start] + new + s[end:]
s = s.replace('    updateLabels();\n    keepBoardSquare();', '    drawAttackLines(threatenedInfo);\n    updateLabels();\n    keepBoardSquare();')

# Wire board style UI and save it.
s = s.replace("""const modeSelect=$('modeSelect'), sideSelect=$('sideSelect'), thinkSelect=$('thinkSelect');""", """const modeSelect=$('modeSelect'), sideSelect=$('sideSelect'), thinkSelect=$('thinkSelect'), boardStyleSelect=$('boardStyleSelect'), botWaitSelect=$('botWaitSelect');""")
s = s.replace("""  const sideField=$('sideField'), thinkField=$('thinkField');""", """  const sideField=$('sideField'), thinkField=$('thinkField'), botWaitField=$('botWaitField');""")
s = s.replace("""let botsPaused=false, whiteBotTime=120, blackBotTime=120;""", """let botsPaused=false, whiteBotTime=120, blackBotTime=120, botWaitAnimation=true;""")
s = s.replace("""  const PST = {""", """  function setBoardStyle(style){
    const chosen = style === 'dark' ? 'dark' : 'bright';
    document.body.dataset.boardStyle = chosen;
    if(boardStyleSelect) boardStyleSelect.value = chosen;
    try{ localStorage.setItem('chessDuelBoardStyle', chosen); }catch(e){}
  }
  setBoardStyle((()=>{ try{return localStorage.getItem('chessDuelBoardStyle')||'bright'}catch(e){return 'bright'} })());
  if(boardStyleSelect) boardStyleSelect.addEventListener('change', ()=>setBoardStyle(boardStyleSelect.value));

  function setBotWaitAnimation(value){
    botWaitAnimation = value !== 'skip';
    if(botWaitSelect) botWaitSelect.value = botWaitAnimation ? 'wait' : 'skip';
    try{ localStorage.setItem('chessDuelBotWaitAnimation', botWaitAnimation ? 'wait' : 'skip'); }catch(e){}
  }
  setBotWaitAnimation((()=>{ try{return localStorage.getItem('chessDuelBotWaitAnimation')||'wait'}catch(e){return 'wait'} })());
  if(botWaitSelect) botWaitSelect.addEventListener('change', ()=>setBotWaitAnimation(botWaitSelect.value));

  const PST = {""")

# Show the bot animation setting only when a bot/AI mode is active.
s = s.replace("""    blackBotField.classList.toggle('hidden', !bot);""", """    blackBotField.classList.toggle('hidden', !bot);
    if(botWaitField) botWaitField.classList.toggle('hidden', !(ai || bot));""")
s = s.replace("""    aiTip.textContent = editor ? 'Editor: build any position' : bot ? `AI: White ${labelOf(whiteBotThinkSelect)} • Black ${labelOf(blackBotThinkSelect)}${botsPaused?' • paused':''}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${labelOf(thinkSelect)}` : 'AI: off';""", """    aiTip.textContent = editor ? 'Editor: build any position' : bot ? `AI: White ${labelOf(whiteBotThinkSelect)} • Black ${labelOf(blackBotThinkSelect)} • anim ${botWaitAnimation?'wait':'skip'}${botsPaused?' • paused':''}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${labelOf(thinkSelect)} • anim ${botWaitAnimation?'wait':'skip'}` : 'AI: off';""")

# Add optional no-wait behavior: bot/AI moves skip the visual animation when disabled.
start = s.index('  function doMove(move){')
end = s.index('\n\n  function getAIWorker', start)
do_move = r'''  function doMove(move){
    if(isAnimatingMove) return;
    const before=deepClone(game);
    const after=applyMove(before, move);
    const moveText = moveToText(before, move, after);
    const hist={game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime, move};
    const botControlledMove = mode==='bot' || (mode==='ai' && before.turn===aiColor);
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
    if(botControlledMove && !botWaitAnimation){
      finishMove();
      return;
    }
    isAnimatingMove=true;
    visualMove={from:move.from, to:move.to, capture:!!(move.capture||move.enPassantCapture), piece:before.board[move.from[0]][move.from[1]]};
    draw();
    animateMoveVisual(before, move, finishMove);
  }
'''
s = s[:start] + do_move + s[end:]

p.write_text(s, encoding='utf-8')
print('attack display removed, board style and bot wait toggle kept')
