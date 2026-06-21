from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Better copy.
s = s.replace('Promotion auto-queens for now.', 'Pawn promotion lets you choose.')

# Add promotion picker overlay inside the board wrapper.
s = s.replace(
    '<div id="resultOverlay" class="result-overlay hidden"></div>',
    '<div id="resultOverlay" class="result-overlay hidden"></div>\n        <div id="promotionPicker" class="promotion-picker hidden"></div>'
)

# Style: keep controls visible in fullscreen, hide history/sidebar, add board polish and animations.
s = s.replace('</style>', '''
/* fullscreen control panel */
body.board-only .hero{display:block!important;position:fixed;left:10px;right:10px;bottom:10px;z-index:28;padding:10px;border-radius:22px;background:rgba(15,23,42,.72);border:1px solid rgba(255,255,255,.18);box-shadow:0 22px 70px rgba(0,0,0,.45);backdrop-filter:blur(18px)}
body.board-only .hero .eyebrow,body.board-only .hero h1,body.board-only .hero .sub{display:none!important}
body.board-only .hero .controls{display:flex;gap:8px;align-items:end;overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px;scrollbar-width:none}
body.board-only .hero .field{min-width:130px}
body.board-only .hero select,body.board-only .hero button{padding:9px 11px;border-radius:13px;white-space:nowrap}
body.board-only .board-card{padding:0 0 118px 0!important;align-items:center;background:radial-gradient(circle at 50% 28%,rgba(79,70,229,.15),transparent 28rem),#050816!important}
body.board-only .board-wrap{width:min(100vw,calc(100vh - 125px));height:min(100vw,calc(100vh - 125px));filter:drop-shadow(0 26px 55px rgba(0,0,0,.48))}
body.board-only .board{border-radius:12px;border:4px solid rgba(255,255,255,.14)}

/* nicer board style */
.board{background:#111827;transition:transform .25s ease,box-shadow .25s ease}
.board-card{background:linear-gradient(160deg,rgba(255,255,255,.13),rgba(255,255,255,.06));overflow:hidden}
.square{transition:background .18s ease,filter .18s ease,transform .18s ease}
.square:hover{filter:brightness(1.08)}
.square.last-from::after,.square.last-to::after{content:"";position:absolute;inset:0;background:rgba(250,204,21,.25);pointer-events:none}
.square.last-to::after{box-shadow:inset 0 0 0 4px rgba(250,204,21,.5)}
.piece{animation:piecePop .18s ease;transition:transform .18s ease,filter .18s ease}
.square:hover .piece{transform:scale(1.05)}
@keyframes piecePop{from{transform:scale(.86);opacity:.72}to{transform:scale(1);opacity:1}}
.result-overlay{animation:resultBoom .28s ease}
@keyframes resultBoom{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}
.promotion-picker{position:absolute;inset:0;display:grid;place-items:center;background:rgba(2,6,23,.64);z-index:22;backdrop-filter:blur(4px)}
.promotion-box{display:flex;gap:10px;padding:14px;border-radius:24px;background:rgba(15,23,42,.88);border:1px solid rgba(255,255,255,.22);box-shadow:0 20px 60px rgba(0,0,0,.5)}
.promotion-box button{font-size:2.6rem;line-height:1;padding:15px 18px;border-radius:18px;background:rgba(255,255,255,.14)}
.promotion-box button:hover{transform:translateY(-2px);background:rgba(255,255,255,.22)}
</style>''')

# All real promotion choices instead of auto queen.
s = s.replace("if(one===promoRow) push(one,c,{promotion:'Q'}); else push(one,c);", "if(one===promoRow){ for(const pr of ['Q','R','B','N']) push(one,c,{promotion:pr}); } else push(one,c);")
s = s.replace("if(rr===promoRow) push(rr,cc,{capture:board[rr][cc],promotion:'Q'}); else push(rr,cc,{capture:board[rr][cc]});", "if(rr===promoRow){ for(const pr of ['Q','R','B','N']) push(rr,cc,{capture:board[rr][cc],promotion:pr}); } else push(rr,cc,{capture:board[rr][cc]});")

# JS references.
s = s.replace("const fullscreenBtn=$('fullscreenBtn'), resultOverlay=$('resultOverlay');", "const fullscreenBtn=$('fullscreenBtn'), resultOverlay=$('resultOverlay'), promotionPicker=$('promotionPicker');")
s = s.replace("let boardOnly=false, lastBoardTap=0;", "let boardOnly=false, lastBoardTap=0;")

# Highlight the last move.
s = s.replace(
    "const legal = legalTargets.find(m => m.to[0]===r && m.to[1]===c);\n        if(selected && selected[0]===r && selected[1]===c) sq.classList.add('selected');",
    "const legal = legalTargets.find(m => m.to[0]===r && m.to[1]===c);\n        const last = history[history.length-1]?.move;\n        if(last && last.from[0]===r && last.from[1]===c) sq.classList.add('last-from');\n        if(last && last.to[0]===r && last.to[1]===c) sq.classList.add('last-to');\n        if(selected && selected[0]===r && selected[1]===c) sq.classList.add('selected');"
)

# Promotion picker functions.
funcs = '''
  function showPromotionPicker(moves){
    if(!moves || moves.length===0) return;
    const color = pieceColor(moves[0].piece);
    promotionPicker.innerHTML='';
    const box=document.createElement('div'); box.className='promotion-box';
    for(const t of ['Q','R','B','N']){
      const m=moves.find(x=>x.promotion===t);
      if(!m) continue;
      const btn=document.createElement('button');
      btn.textContent=PIECE_ICON[color][t];
      btn.setAttribute('aria-label','Promote to '+nameOfPiece(color+t));
      btn.addEventListener('click', ()=>{ promotionPicker.classList.add('hidden'); promotionPicker.innerHTML=''; doMove(m); });
      box.appendChild(btn);
    }
    promotionPicker.appendChild(box);
    promotionPicker.classList.remove('hidden');
  }

'''
s = s.replace('  function nameOfPiece(piece){', funcs + '  function nameOfPiece(piece){')

# Use promotion picker when multiple promotion moves target the same square.
s = s.replace(
    """    const legal = legalTargets.find(m=>m.to[0]===r && m.to[1]===c);
    if(selected && legal){ doMove(legal); return; }
""",
    """    const possibleMoves = legalTargets.filter(m=>m.to[0]===r && m.to[1]===c);
    const legal = possibleMoves[0];
    if(selected && legal){
      if(possibleMoves.some(m=>m.promotion)){ showPromotionPicker(possibleMoves); return; }
      doMove(legal); return;
    }
"""
)

p.write_text(s, encoding='utf-8')
print('Added fullscreen controls, polish, last-move animation, and real promotion choice.')
