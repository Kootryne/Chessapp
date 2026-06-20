from pathlib import Path

html_path = Path('app/src/main/assets/chess.html')
worker_path = Path('app/src/main/assets/ai_worker.js')
s = html_path.read_text(encoding='utf-8')

# Add position keys and repetition helpers in the main UI.
needle = """  function other(color){ return color==='w'?'b':'w'; }
  function inBounds(r,c){ return r>=0 && r<8 && c>=0 && c<8; }
"""
insert = """  function other(color){ return color==='w'?'b':'w'; }
  function positionKey(state){
    return state.turn+'|'+state.board.flat().map(p=>p||'..').join('')+'|'
      +(state.castling.wK?1:0)+(state.castling.wQ?1:0)+(state.castling.bK?1:0)+(state.castling.bQ?1:0)+'|'
      +(state.enPassant?state.enPassant.join(','):'-');
  }
  function repetitionCountFor(state){
    const key=positionKey(state);
    let count=1;
    for(const h of history){
      if(h?.game && positionKey(h.game)===key) count++;
    }
    return count;
  }
  function recentPositionKeys(limit=14){
    const keys=[];
    try{ keys.push(positionKey(game)); }catch(e){}
    for(let i=history.length-1;i>=0 && keys.length<limit;i--){
      if(history[i]?.game) keys.push(positionKey(history[i].game));
    }
    return [...new Set(keys)];
  }
  function applyRepetitionDraw(){
    if(game.result) return;
    if(repetitionCountFor(game)>=3) game.result={type:'drawRepetition'};
  }
  function inBounds(r,c){ return r>=0 && r<8 && c>=0 && c<8; }
"""
if needle not in s:
    raise SystemExit('Could not insert repetition helpers')
s = s.replace(needle, insert)

# Make main fallback search avoid recently repeated positions.
s = s.replace('function searchBestMove(rootState, timeLimit){', 'function searchBestMove(rootState, timeLimit, avoidKeys=[]){')
s = s.replace(
    """          const child=applyMove(rootState, move);
          const score=-negamax(child, depth-1, -Infinity, Infinity);
          move.__score = score;
          if(score>depthBestScore){ depthBestScore=score; depthBest=move; }
""",
    """          const child=applyMove(rootState, move);
          const rawScore=-negamax(child, depth-1, -Infinity, Infinity);
          let score = rawScore;
          if(avoidKeys && avoidKeys.includes(positionKey(child))) score -= 650;
          move.__score = score;
          if(score>depthBestScore){ depthBestScore=score; depthBest=move; }
"""
)

# Add draw by repetition after every move.
s = s.replace("""    annotateResult(game);
    selected=null; legalTargets=[];
""", """    annotateResult(game);
    applyRepetitionDraw();
    selected=null; legalTargets=[];
""")

# Main UI / overlay text for repetition.
s = s.replace("""    if(game.result?.type==='checkmate') return `${game.result.winner==='w'?'White':'Black'} wins!\\nCheckmate`;
    if(game.result?.type==='stalemate') return 'Draw!\\nStalemate';
    if(game.result?.type==='draw50') return 'Draw!\\n50-move rule';
""", """    if(game.result?.type==='checkmate') return `${game.result.winner==='w'?'White':'Black'} wins!\\nCheckmate`;
    if(game.result?.type==='stalemate') return 'Draw!\\nStalemate';
    if(game.result?.type==='draw50') return 'Draw!\\n50-move rule';
    if(game.result?.type==='drawRepetition') return 'Draw!\\nRepetition';
""")
s = s.replace("""    if(game.result?.type==='checkmate') statusText.textContent = `Checkmate. ${game.result.winner==='w'?'White':'Black'} wins.`;
    else if(game.result?.type==='stalemate') statusText.textContent = 'Stalemate. Nobody can move.';
    else if(game.result?.type==='draw50') statusText.textContent = 'Draw by fifty-move rule.';
""", """    if(game.result?.type==='checkmate') statusText.textContent = `Checkmate. ${game.result.winner==='w'?'White':'Black'} wins.`;
    else if(game.result?.type==='stalemate') statusText.textContent = 'Stalemate. Nobody can move.';
    else if(game.result?.type==='draw50') statusText.textContent = 'Draw by fifty-move rule.';
    else if(game.result?.type==='drawRepetition') statusText.textContent = 'Draw by repeated position.';
""")
s = s.replace("game.result?.type==='stalemate' ? 'Draw'", "(game.result && game.result.type!=='checkmate') ? 'Draw'")

# Pass avoid keys to worker and fallback searches.
s = s.replace("worker.postMessage({type:'search', job:++aiJob, state:deepClone(game), time:turnTime});", "worker.postMessage({type:'search', job:++aiJob, state:deepClone(game), time:turnTime, avoidKeys:recentPositionKeys(14)});")
s = s.replace("searchBestMove(game, Math.min(turnTime, 2500));", "searchBestMove(game, Math.min(turnTime, 2500), recentPositionKeys(14));")
s = s.replace("searchBestMove(game, Math.min(turnTime,2500));", "searchBestMove(game, Math.min(turnTime,2500), recentPositionKeys(14));")

html_path.write_text(s, encoding='utf-8')

# Patch generated worker AI. It has no access to main history, so the main thread sends avoidKeys.
w = worker_path.read_text(encoding='utf-8')
w = w.replace('function searchBestMove(rootState, timeLimit){', 'function searchBestMove(rootState, timeLimit, avoidKeys=[]){')
w = w.replace(
    """          const child=applyMove(rootState, move);
          const score=-negamax(child, depth-1, -Infinity, Infinity);
          move.__score = score;
          if(score>depthBestScore){ depthBestScore=score; depthBest=move; }
""",
    """          const child=applyMove(rootState, move);
          const rawScore=-negamax(child, depth-1, -Infinity, Infinity);
          let score = rawScore;
          if(avoidKeys && avoidKeys.includes(keyOf(child))) score -= 650;
          move.__score = score;
          if(score>depthBestScore){ depthBestScore=score; depthBest=move; }
"""
)
w = w.replace("searchBestMove(msg.state, msg.time || 7000);", "searchBestMove(msg.state, msg.time || 7000, msg.avoidKeys || []);")
worker_path.write_text(w, encoding='utf-8')

print('Added repetition draw detection and anti-repeat bot move penalty.')
