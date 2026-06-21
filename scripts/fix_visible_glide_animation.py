from pathlib import Path

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Remove the accidentally inserted animation call from resetGame.
s = s.replace("""    draw();
    animateMoveVisual(before, move);
    maybeAIMove();
  }

  function isSquareAttacked""", """    draw();
    maybeAIMove();
  }

  function isSquareAttacked""")

# Put the animation call into the actual move function.
s = s.replace("""    selected=null; legalTargets=[];
    draw();
    maybeAIMove();
  }

  function getAIWorker""", """    selected=null; legalTargets=[];
    draw();
    animateMoveVisual(before, move);
    maybeAIMove();
  }

  function getAIWorker""")

# Make the movement much more visible and slower.
s = s.replace('.moving-ghost{position:fixed;z-index:9999;pointer-events:none;display:grid;place-items:center;will-change:transform,opacity;transition:transform .22s cubic-bezier(.18,.86,.23,1),opacity .12s ease;', '.moving-ghost{position:fixed;z-index:9999;pointer-events:none;display:grid;place-items:center;will-change:transform,opacity;transition:transform .48s cubic-bezier(.13,.9,.12,1),opacity .18s ease;')
s = s.replace('.move-streak{position:fixed;z-index:9998;pointer-events:none;height:16px;border-radius:999px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.48),rgba(255,255,255,0));filter:blur(4px);', '.move-streak{position:fixed;z-index:9998;pointer-events:none;height:26px;border-radius:999px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.85),rgba(99,102,241,.55),rgba(255,255,255,0));filter:blur(6px);')
s = s.replace("streak.style.width=Math.max(28,len*.72)+'px';", "streak.style.width=Math.max(42,len*.95)+'px';")
s = s.replace("ghost.style.transform=`translate(${dx}px,${dy}px) scale(1.04)`;", "ghost.style.transform=`translate(${dx}px,${dy}px) scale(1.12)`;")
s = s.replace("streak.style.opacity='.86';", "streak.style.opacity='1';")
s = s.replace("setTimeout(()=>{ ghost.style.opacity='0'; streak.style.opacity='0'; },210);", "setTimeout(()=>{ ghost.style.opacity='0'; streak.style.opacity='0'; },470);")
s = s.replace("setTimeout(()=>{ ghost.remove(); streak.remove(); },360);", "setTimeout(()=>{ ghost.remove(); streak.remove(); },680);")

# Add an obvious temporary glow on the destination square so manual moves feel responsive.
s = s.replace("""      requestAnimationFrame(()=>{
        ghost.style.transform=`translate(${dx}px,${dy}px) scale(1.12)`;""", """      toEl.classList.add('motion-target');
      setTimeout(()=>toEl.classList.remove('motion-target'),620);
      requestAnimationFrame(()=>{
        ghost.style.transform=`translate(${dx}px,${dy}px) scale(1.12)`;""")

s = s.replace('</style>', '''
.motion-target{box-shadow:inset 0 0 0 5px rgba(34,211,238,.55), inset 0 0 32px rgba(34,211,238,.24)!important}
</style>''')

p.write_text(s, encoding='utf-8')
print('Fixed animation placement and made glide/streak visible.')
