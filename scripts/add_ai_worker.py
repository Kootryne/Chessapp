from pathlib import Path
import re

asset = Path('app/src/main/assets/chess.html')
html = asset.read_text(encoding='utf-8')
script = re.search(r'<script>([\s\S]*?)</script>', html).group(1)

const_start = script.index('  const PST =')
const_end = script.index('\n\n  let game', const_start)
const_block = script[const_start:const_end].replace('  ', '', 1)
const_block = "const FILES='abcdefgh';\n" + const_block.strip() + "\n"

def grab_func(name: str) -> str:
    token = f'function {name}('
    start = script.index(token)
    brace = script.index('{', start)
    depth = 0
    for i in range(brace, len(script)):
        if script[i] == '{':
            depth += 1
        elif script[i] == '}':
            depth -= 1
            if depth == 0:
                return script[start:i+1]
    raise RuntimeError(f'Could not grab {name}')

names = [
    'deepClone','sqName','other','inBounds','pieceColor','pieceType',
    'isSquareAttacked','findKing','isInCheck','generatePseudoMoves','applyMove',
    'legalMovesFor','annotateResult','orderedMoves','moveScoreGuess','evaluate','searchBestMove'
]
funcs = '\n\n'.join(grab_func(n) for n in names)

# Add a transposition cache to the worker search. It is intentionally simple, but fast enough to avoid many repeated branches.
funcs = funcs.replace(
    'let bestMove=null, bestScore=-Infinity, reachedDepth=0;',
    "let bestMove=null, bestScore=-Infinity, reachedDepth=0;\n    const tt=new Map();\n    function keyOf(s){return s.turn+'|'+s.board.flat().map(p=>p||'..').join('')+'|'+(s.castling.wK?1:0)+(s.castling.wQ?1:0)+(s.castling.bK?1:0)+(s.castling.bQ?1:0)+'|'+(s.enPassant?s.enPassant.join(','):'-');}"
)
funcs = funcs.replace(
    "function negamax(state, depth, alpha, beta){\n      if(performance.now()>end) throw new Error('timeout');",
    "function negamax(state, depth, alpha, beta){\n      if(performance.now()>end) throw new Error('timeout');\n      const ttKey=keyOf(state)+'|'+depth;\n      if(tt.has(ttKey)) return tt.get(ttKey);"
)
funcs = funcs.replace('      return max;\n    }', '      tt.set(ttKey,max);\n      return max;\n    }', 1)

worker = """// Generated during the APK build. Runs chess AI off the UI thread.
""" + const_block + "\n" + funcs + """

self.onmessage = (event) => {
  const msg = event.data || {};
  if(msg.type !== 'search') return;
  try {
    const result = searchBestMove(msg.state, msg.time || 7000);
    self.postMessage({type:'done', job:msg.job, move:result.move, depth:result.depth, score:result.score});
  } catch (err) {
    self.postMessage({type:'error', job:msg.job, error:String(err && err.message || err)});
  }
};
"""
Path('app/src/main/assets/ai_worker.js').write_text(worker, encoding='utf-8')

old_vars = "let mode='human', humanColor='w', aiColor='b', aiThinking=false, aiTime=7000;"
new_vars = "let mode='human', humanColor='w', aiColor='b', aiThinking=false, aiTime=7000;\n  let aiWorker=null, aiJob=0;"
html = html.replace(old_vars, new_vars)

old_move = """  function maybeAIMove(){
    if(mode!=='ai' || game.result || game.turn!==aiColor) return;
    aiThinking=true; draw();
    setTimeout(()=>{
      try{
        const {move, depth, score} = searchBestMove(game, aiTime);
        aiTip.textContent = `AI: depth ${depth || 1} • score ${score>0?'+':''}${Math.round(score/10)/10}`;
        aiThinking=false;
        if(move) doMove(move); else draw();
      }catch(err){
        aiThinking=false; aiTip.textContent='AI: move failed'; draw();
      }
    }, 60);
  }
"""
new_move = """  function getAIWorker(){
    if(aiWorker) return aiWorker;
    try{
      aiWorker = new Worker('ai_worker.js');
      aiWorker.onmessage = ev => {
        const data = ev.data || {};
        if(data.job !== aiJob) return;
        if(data.type === 'done'){
          aiThinking=false;
          aiTip.textContent = `AI worker: depth ${data.depth || 1} • score ${data.score>0?'+':''}${Math.round((data.score||0)/10)/10}`;
          if(data.move) doMove(data.move); else draw();
        } else if(data.type === 'error'){
          aiThinking=false;
          aiTip.textContent = 'AI worker failed; using fallback';
          setTimeout(()=>{
            const {move, depth, score} = searchBestMove(game, Math.min(aiTime, 2500));
            aiTip.textContent = `Fallback AI: depth ${depth || 1} • score ${score>0?'+':''}${Math.round(score/10)/10}`;
            if(move) doMove(move); else draw();
          }, 30);
        }
      };
      return aiWorker;
    }catch(e){ return null; }
  }

  function maybeAIMove(){
    if(mode!=='ai' || game.result || game.turn!==aiColor) return;
    aiThinking=true; draw();
    const worker=getAIWorker();
    if(worker){
      aiTip.textContent='AI thinking in background...';
      worker.postMessage({type:'search', job:++aiJob, state:deepClone(game), time:aiTime});
      return;
    }
    setTimeout(()=>{
      try{
        const {move, depth, score} = searchBestMove(game, Math.min(aiTime, 2500));
        aiTip.textContent = `Fallback AI: depth ${depth || 1} • score ${score>0?'+':''}${Math.round(score/10)/10}`;
        aiThinking=false;
        if(move) doMove(move); else draw();
      }catch(err){
        aiThinking=false; aiTip.textContent='AI move failed'; draw();
      }
    }, 60);
  }
"""
if old_move not in html:
    raise SystemExit('Could not find maybeAIMove block to replace')
html = html.replace(old_move, new_move)
asset.write_text(html, encoding='utf-8')
print('AI search moved to Web Worker with transposition cache.')
