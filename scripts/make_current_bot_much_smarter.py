from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '<option value="800">Fast</option>\n          <option value="1600">Smart</option>\n          <option value="2800" selected>Really smart</option>\n          <option value="4500">Max brain</option>',
    '<option value="1500">Fast</option>\n          <option value="3500">Smart</option>\n          <option value="7000" selected>Really smart</option>\n          <option value="15000">Max brain</option>'
)
s = s.replace(
    "let mode='human', humanColor='w', aiColor='b', aiThinking=false, aiTime=2800;",
    "let mode='human', humanColor='w', aiColor='b', aiThinking=false, aiTime=7000;"
)
s = s.replace("aiTime = Number(thinkSelect.value)||2800;", "aiTime = Number(thinkSelect.value)||7000;")
s = s.replace(
    'Fixed board scaling, less-squished pieces, and a much smarter bot mode. White still starts like normal chess.',
    'Stronger bot mode: deeper search, quiescence for captures, mid-game bot switching, and a forced square board. White still starts like normal chess.'
)

# Force the board itself to always be 1:1, and force every grid cell to behave as a square.
s = s.replace(
    '.board{display:grid;grid-template-columns:repeat(8,1fr);aspect-ratio:1;',
    '.board{display:grid;grid-template-columns:repeat(8,1fr);grid-template-rows:repeat(8,1fr);width:100%;height:auto;aspect-ratio:1/1;'
)
s = s.replace(
    '.board-wrap{max-width:700px;margin:0 auto}',
    '.board-wrap{width:min(94vw,700px);max-width:700px;margin:0 auto}'
)
s = s.replace(
    '.square{position:relative;display:grid;place-items:center;user-select:none;touch-action:manipulation}',
    '.square{position:relative;display:grid;place-items:center;user-select:none;touch-action:manipulation;aspect-ratio:1/1;min-width:0;min-height:0;overflow:hidden}'
)

old = """    function negamax(state, depth, alpha, beta){
      if(performance.now()>end) throw new Error('timeout');
      const res=annotateResult(state);
      if(res){
        if(res.type==='checkmate') return -100000 + (6-depth);
        return 0;
      }
      if(depth===0){
        return (state.turn==='w'?1:-1) * evaluate(state);
      }
      let max=-Infinity;
      const moves = orderedMoves(state, legalMovesFor(state, state.turn));
      for(const move of moves){
        const child=applyMove(state, move);
        const score = -negamax(child, depth-1, -beta, -alpha);
        if(score>max) max=score;
        if(score>alpha) alpha=score;
        if(alpha>=beta) break;
      }
      return max;
    }
"""
new = """    function quiesce(state, alpha, beta, qDepth){
      if(performance.now()>end) throw new Error('timeout');
      const stand = (state.turn==='w'?1:-1) * evaluate(state);
      if(stand >= beta) return beta;
      if(alpha < stand) alpha = stand;
      if(qDepth <= 0) return alpha;
      const noisy = orderedMoves(state, legalMovesFor(state, state.turn)).filter(m => m.capture || m.promotion);
      for(const move of noisy){
        const score = -quiesce(applyMove(state, move), -beta, -alpha, qDepth-1);
        if(score >= beta) return beta;
        if(score > alpha) alpha = score;
      }
      return alpha;
    }

    function negamax(state, depth, alpha, beta){
      if(performance.now()>end) throw new Error('timeout');
      const res=annotateResult(state);
      if(res){
        if(res.type==='checkmate') return -100000 + (20-depth);
        return 0;
      }
      if(depth===0){
        return quiesce(state, alpha, beta, 4);
      }
      let max=-Infinity;
      let moves = orderedMoves(state, legalMovesFor(state, state.turn));
      if(isInCheck(state, state.turn)) depth += 1;
      for(const move of moves){
        const child=applyMove(state, move);
        const score = -negamax(child, depth-1, -beta, -alpha);
        if(score>max) max=score;
        if(score>alpha) alpha=score;
        if(alpha>=beta) break;
      }
      return max;
    }
"""
if old not in s:
    raise SystemExit('Could not find negamax block to patch')
s = s.replace(old, new)
s = s.replace('for(let depth=1; depth<=6; depth++){', 'for(let depth=1; depth<=9; depth++){')

# Allow switching between 2-player mode and AI mode without resetting the current game.
s = s.replace(
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; aiColor = other(humanColor); setModeUI(); resetGame(); });",
    "modeSelect.addEventListener('change', ()=>{ mode=modeSelect.value; aiColor = other(humanColor); setModeUI(); draw(); maybeAIMove(); });"
)
s = s.replace(
    "sideSelect.addEventListener('change', ()=>{ humanColor=sideSelect.value; aiColor=other(humanColor); setModeUI(); resetGame(); });",
    "sideSelect.addEventListener('change', ()=>{ humanColor=sideSelect.value; aiColor=other(humanColor); setModeUI(); draw(); maybeAIMove(); });"
)

# Extra Android/WebView safety: if aspect-ratio has a weird moment, JS forces the board height to match the width.
needle = """  function draw(){
    boardEl.innerHTML='';
"""
if needle in s:
    s = s.replace(needle, """  function keepBoardSquare(){
    const w = boardEl.clientWidth || boardEl.getBoundingClientRect().width;
    if(w) boardEl.style.height = Math.round(w) + 'px';
  }
  window.addEventListener('resize', keepBoardSquare);
  window.addEventListener('orientationchange', ()=>setTimeout(keepBoardSquare, 120));

  function draw(){
    keepBoardSquare();
    boardEl.innerHTML='';
""")
s = s.replace("""    updateLabels();
  }
""", """    updateLabels();
    keepBoardSquare();
  }
""", 1)

p.write_text(s, encoding='utf-8')
print('Current bot upgraded, mid-game AI switching enabled, board forced square.')
