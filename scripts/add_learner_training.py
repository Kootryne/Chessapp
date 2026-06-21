from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace('<option value="bot">Bot vs bot</option>', '<option value="bot">Bot vs bot</option>\n          <option value="train">Train learner</option>')

s = s.replace('''      <button class="primary" id="newBtn">New game</button>''', '''      <div class="field hidden" id="trainOpponentField">
        <label for="trainOpponentSelect">Train against</label>
        <select id="trainOpponentSelect">
          <option value="instant">Instant bot</option>
          <option value="other">Separate learner</option>
          <option value="same">Same model self-play</option>
        </select>
      </div>
      <button id="trainOneBtn" class="hidden">Train 1 game</button>
      <button id="trainAutoBtn" class="hidden">Auto train</button>
      <button id="resetLearnerBtn" class="hidden">Reset learner</button>
      <button class="primary" id="newBtn">New game</button>''')

s = s.replace('<div class="tip" id="aiTip">AI: off</div>', '<div class="tip" id="aiTip">AI: off</div>\n        <div class="tip hidden" id="learnTip">Learner: 0 games</div>')

s = s.replace('</style>', '''
.learn-flash{animation:learnFlash .38s ease}
@keyframes learnFlash{from{filter:brightness(1.35) saturate(1.3)}to{filter:none}}
</style>''')

s = s.replace("const pauseBotsBtn=$('pauseBotsBtn'), whiteBotThinkSelect=$('whiteBotThinkSelect'), blackBotThinkSelect=$('blackBotThinkSelect');", "const pauseBotsBtn=$('pauseBotsBtn'), whiteBotThinkSelect=$('whiteBotThinkSelect'), blackBotThinkSelect=$('blackBotThinkSelect');\n  const trainOpponentField=$('trainOpponentField'), trainOpponentSelect=$('trainOpponentSelect'), trainOneBtn=$('trainOneBtn'), trainAutoBtn=$('trainAutoBtn'), resetLearnerBtn=$('resetLearnerBtn'), learnTip=$('learnTip');")
s = s.replace("let botsPaused=false, whiteBotTime=120, blackBotTime=120;", "let botsPaused=false, whiteBotTime=120, blackBotTime=120;\n  let trainerRunning=false;")

# Add learner system before setModeUI.
learner_code = r'''
  const LEARN_KEYS=['bias','eval','capture','promo','castle','check','center','mobility','safe'];
  function freshLearner(){ return {w:Array(LEARN_KEYS.length).fill(0), games:0,wins:0,losses:0,draws:0}; }
  function loadLearner(name){ try{return JSON.parse(localStorage.getItem('learner_'+name))||freshLearner();}catch(e){return freshLearner();} }
  function saveLearner(name,m){ try{localStorage.setItem('learner_'+name, JSON.stringify(m));}catch(e){} }
  let learnerA=loadLearner('A'), learnerB=loadLearner('B');
  function resetLearners(){ learnerA=freshLearner(); learnerB=freshLearner(); saveLearner('A',learnerA); saveLearner('B',learnerB); updateLearnTip(); }
  function norm(v,scale){ return Math.max(-1, Math.min(1, v/scale)); }
  function centerScore(r,c){ return (3.5-(Math.abs(3.5-r)+Math.abs(3.5-c))/2)/3.5; }
  function learnerFeatures(state,move){
    const child=applyMove(state,move);
    const side=state.turn==='w'?1:-1;
    const cap=move.capture ? (VALUES[pieceType(move.capture)]||100) : 0;
    const givesCheck=isInCheck(child,child.turn)?1:0;
    const mob=legalMovesFor(child,child.turn).length;
    const safe=!isSquareAttacked(child,move.to[0],move.to[1],child.turn)?1:0;
    return [1, norm(side*evaluate(child),1600), norm(cap,900), move.promotion?1:0, move.castle?1:0, givesCheck, centerScore(move.to[0],move.to[1]), norm(40-mob,40), safe];
  }
  function learnerMove(model,state,eps=.18){
    const moves=legalMovesFor(state,state.turn);
    if(!moves.length) return null;
    if(Math.random()<eps) return moves[Math.floor(Math.random()*moves.length)];
    let best=moves[0], bestScore=-Infinity;
    for(const m of orderedMoves(state,moves)){
      const f=learnerFeatures(state,m);
      let score=0; for(let i=0;i<f.length;i++) score += (model.w[i]||0)*f[i];
      score += Math.random()*0.015;
      if(score>bestScore){bestScore=score; best=m;}
    }
    return best;
  }
  function trainUpdate(model,records,reward){
    const lr=.035;
    const decay=.998;
    for(let i=0;i<model.w.length;i++) model.w[i]*=decay;
    for(const f of records){
      for(let i=0;i<f.length;i++) model.w[i] += lr*reward*f[i]/Math.sqrt(1+model.games/18);
    }
    for(let i=0;i<model.w.length;i++) model.w[i]=Math.max(-6,Math.min(6,model.w[i]));
  }
  function trainResultValue(result, color){
    if(result?.type==='checkmate') return result.winner===color ? 1 : -1;
    return .04;
  }
  function updateLearnTip(){
    const g=learnerA.games;
    learnTip.textContent=`Learner: ${g} games • W ${learnerA.wins} / L ${learnerA.losses} / D ${learnerA.draws}`;
  }
  function trainOneGame(){
    let st=startPosition();
    const modeTrain=trainOpponentSelect.value;
    const learnerColor=Math.random()<.5?'w':'b';
    const seen=new Map();
    const recA=[], recB=[];
    let ply=0;
    while(!st.result && ply<240){
      const key=positionKey(st); seen.set(key,(seen.get(key)||0)+1); if(seen.get(key)>=3){st.result={type:'drawRepetition'}; break;}
      let mv=null;
      if(modeTrain==='instant'){
        if(st.turn===learnerColor){ mv=learnerMove(learnerA,st,.22); if(mv) recA.push(learnerFeatures(st,mv)); }
        else { mv=(searchBestMove(st,12,[]).move)||orderedMoves(st,legalMovesFor(st,st.turn))[0]; }
      } else if(modeTrain==='same'){
        mv=learnerMove(learnerA,st,.25); if(mv) recA.push(learnerFeatures(st,mv));
      } else {
        if(st.turn==='w'){ mv=learnerMove(learnerA,st,.24); if(mv) recA.push(learnerFeatures(st,mv)); }
        else { mv=learnerMove(learnerB,st,.24); if(mv) recB.push(learnerFeatures(st,mv)); }
      }
      if(!mv) break;
      st=applyMove(st,mv); annotateResult(st);
      ply++;
    }
    if(!st.result) st.result={type:'trainingMax'};
    const aColor = modeTrain==='instant' ? learnerColor : 'w';
    const rA=trainResultValue(st.result,aColor);
    trainUpdate(learnerA,recA,rA);
    learnerA.games++;
    if(rA>.5) learnerA.wins++; else if(rA<-.5) learnerA.losses++; else learnerA.draws++;
    if(modeTrain==='other'){
      const rB=trainResultValue(st.result,'b'); trainUpdate(learnerB,recB,rB); learnerB.games++;
    }
    saveLearner('A',learnerA); saveLearner('B',learnerB);
    game=st; selected=null; legalTargets=[]; history=[]; moveTexts=[`Training game ${learnerA.games}`]; updateLearnTip(); draw();
    boardEl.classList.remove('learn-flash'); void boardEl.offsetWidth; boardEl.classList.add('learn-flash');
  }
  function trainAutoLoop(){
    if(!trainerRunning) return;
    trainOneGame();
    setTimeout(trainAutoLoop, 30);
  }

'''
s = s.replace('  function labelOf(select){', learner_code + '  function labelOf(select){')

# Patch setModeUI using existing lines from the bot controls version.
s = s.replace("const bot = mode==='bot';\n    const usesAI = ai || bot;", "const bot = mode==='bot';\n    const train = mode==='train';\n    const usesAI = ai || bot;")
s = s.replace("pauseBotsBtn.classList.toggle('hidden', !bot);", "pauseBotsBtn.classList.toggle('hidden', !bot);\n    trainOpponentField.classList.toggle('hidden', !train);\n    trainOneBtn.classList.toggle('hidden', !train);\n    trainAutoBtn.classList.toggle('hidden', !train);\n    resetLearnerBtn.classList.toggle('hidden', !train);\n    learnTip.classList.toggle('hidden', !train);")
s = s.replace("modeTip.textContent = bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';", "modeTip.textContent = train ? 'Mode: train learner' : bot ? 'Mode: bot vs bot' : ai ? 'Mode: play vs AI' : 'Mode: 2 players';")
s = s.replace("aiTip.textContent = bot ? `AI: White ${labelOf(whiteBotThinkSelect)} • Black ${labelOf(blackBotThinkSelect)}${botsPaused?' • paused':''}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${labelOf(thinkSelect)}` : 'AI: off';", "aiTip.textContent = train ? `Training: ${trainOpponentSelect.options[trainOpponentSelect.selectedIndex].text}${trainerRunning?' • running':''}` : bot ? `AI: White ${labelOf(whiteBotThinkSelect)} • Black ${labelOf(blackBotThinkSelect)}${botsPaused?' • paused':''}` : ai ? `AI: ${humanColor==='w'?'You are White':'You are Black'} • ${labelOf(thinkSelect)}` : 'AI: off';\n    updateLearnTip();")

# Don't let clicks move pieces during trainer mode.
s = s.replace("if(mode==='bot') return;", "if(mode==='train') return;\n    if(mode==='bot') return;")

# MaybeAIMove should ignore trainer mode.
s = s.replace("if((mode!=='ai' && mode!=='bot') || game.result || (mode==='bot' && botsPaused)) return;", "if((mode!=='ai' && mode!=='bot') || game.result || mode==='train' || (mode==='bot' && botsPaused)) return;")

# Mode switch should not reset into AI behavior; trainer shows controls and waits for train buttons.
s = s.replace("if(mode!=='bot') botsPaused=false;", "if(mode!=='bot') botsPaused=false; if(mode!=='train') trainerRunning=false;")

# Events.
s = s.replace("$('newBtn').addEventListener('click', resetGame);", "$('newBtn').addEventListener('click', resetGame);\n  trainOneBtn.addEventListener('click', ()=>{ trainerRunning=false; trainAutoBtn.textContent='Auto train'; trainOneGame(); });\n  trainAutoBtn.addEventListener('click', ()=>{ trainerRunning=!trainerRunning; trainAutoBtn.textContent=trainerRunning?'Stop training':'Auto train'; if(trainerRunning) trainAutoLoop(); setModeUI(); });\n  resetLearnerBtn.addEventListener('click', ()=>{ trainerRunning=false; trainAutoBtn.textContent='Auto train'; resetLearners(); });")

# Initialize tip.
s = s.replace("setModeUI();\n  resetGame();", "setModeUI();\n  updateLearnTip();\n  resetGame();")

p.write_text(s, encoding='utf-8')
print('Added learner AI training mode.')
