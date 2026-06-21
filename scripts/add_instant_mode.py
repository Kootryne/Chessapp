from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '<option value="120">Super fast (~150 ms)</option>',
    '<option value="12">Instant (~12 ms)</option>\n          <option value="120">Super fast (~150 ms)</option>'
)
s = s.replace(
    '<option value="120" selected>Super fast (~150 ms)</option>',
    '<option value="12" selected>Instant (~12 ms)</option>\n          <option value="120">Super fast (~150 ms)</option>'
)

old = """    const rootMoves = orderedMoves(rootState, legalMovesFor(rootState, rootState.turn));
    if(rootMoves.length===0) return {move:null, score:0, depth:0};
"""
new_main = """    const rootMoves = orderedMoves(rootState, legalMovesFor(rootState, rootState.turn));
    if(rootMoves.length===0) return {move:null, score:0, depth:0};
    if(timeLimit <= 25){
      let best=rootMoves[0], bestScore=-Infinity;
      for(const move of rootMoves){
        const child=applyMove(rootState, move);
        let score = -(child.turn==='w'?1:-1) * evaluate(child);
        if(move.capture) score += 120 + (VALUES[pieceType(move.capture)]||0) - (VALUES[pieceType(move.piece)]||0)/8;
        if(move.promotion) score += 900;
        if(move.castle) score += 40;
        if(avoidKeys && avoidKeys.includes(positionKey(child))) score -= 650;
        move.__score = score;
        if(score > bestScore){ bestScore=score; best=move; }
      }
      return {move:best, score:bestScore, depth:1};
    }
"""
if old in s:
    s = s.replace(old, new_main, 1)
p.write_text(s, encoding='utf-8')

w_path = Path('app/src/main/assets/ai_worker.js')
w = w_path.read_text(encoding='utf-8')
new_worker = new_main.replace('positionKey(child)', 'keyOf(child)')
if old in w:
    w = w.replace(old, new_worker, 1)
w_path.write_text(w, encoding='utf-8')
print('Added instant mode.')
