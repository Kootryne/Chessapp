from pathlib import Path

# Add Android vibration permission.
manifest = Path('app/src/main/AndroidManifest.xml')
ms = manifest.read_text(encoding='utf-8')
if '<uses-permission android:name="android.permission.VIBRATE"' not in ms:
    ms = ms.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.VIBRATE" />')
manifest.write_text(ms, encoding='utf-8')

p = Path('app/src/main/assets/chess.html')
s = p.read_text(encoding='utf-8')

# Add colored threats and power colors.
s = s.replace('</style>', '''
/* colored threat glow by moved piece type */
.square.threatened-by-last::before{border-color:var(--threat-color,#ff3b73)!important;background:radial-gradient(circle,var(--threat-soft,rgba(255,60,120,.26)),var(--threat-softer,rgba(255,60,120,.07)) 55%,transparent 72%)!important;box-shadow:0 0 20px var(--threat-color,#ff3b73), inset 0 0 20px var(--threat-soft,rgba(255,60,120,.26))!important}
.square.threatened-by-last .piece{filter:drop-shadow(0 0 14px var(--threat-color,#ff3b73)) drop-shadow(0 5px 7px rgba(0,0,0,.38))!important}
</style>''')

# Add helper for color palette.
palette = r'''
  function pieceFxColors(type){
    if(type==='P') return {main:'#22c55e', soft:'rgba(34,197,94,.30)', beam:'rgba(34,197,94,.92)', core:'rgba(220,255,230,.88)'};
    if(type==='N') return {main:'#facc15', soft:'rgba(250,204,21,.32)', beam:'rgba(250,204,21,.92)', core:'rgba(255,255,210,.9)'};
    if(type==='B' || type==='R') return {main:'#fb923c', soft:'rgba(251,146,60,.32)', beam:'rgba(251,146,60,.92)', core:'rgba(255,234,210,.9)'};
    if(type==='Q') return {main:'#ff2d78', soft:'rgba(255,45,120,.34)', beam:'rgba(255,45,120,.94)', core:'rgba(255,230,245,.9)'};
    if(type==='K') return {main:'#ffffff', soft:'rgba(255,255,255,.30)', beam:'rgba(20,20,25,.92)', core:'rgba(255,255,255,.95)', shadow:'rgba(0,0,0,.88)'};
    return {main:'#ff2d78', soft:'rgba(255,45,120,.30)', beam:'rgba(255,45,120,.9)', core:'rgba(255,255,255,.88)'};
  }

'''
s = s.replace('  function haptic(kind){', palette + '  function haptic(kind){')

# Make haptics more likely to work and stronger. Trigger both before and after if available.
s = s.replace("""  function haptic(kind){
    if(mode==='bot') return;
    if(!navigator.vibrate) return;
    try{
      if(kind==='mate') navigator.vibrate([45,28,75]);
      else if(kind==='capture') navigator.vibrate(28);
      else if(kind==='check') navigator.vibrate(34);
      else navigator.vibrate(10);
    }catch(e){}
  }""", """  function haptic(kind){
    if(mode==='bot') return;
    try{
      if(window.AndroidHaptics && AndroidHaptics.vibrate){
        AndroidHaptics.vibrate(kind==='mate'?90:kind==='capture'?45:kind==='check'?55:22);
        return;
      }
      if(navigator.vibrate){
        if(kind==='mate') navigator.vibrate([60,35,95]);
        else if(kind==='capture') navigator.vibrate(45);
        else if(kind==='check') navigator.vibrate(55);
        else navigator.vibrate(22);
      }
    }catch(e){}
  }""")

# Fix missing move in history so last-move threat detection actually works.
s = s.replace("""    const hist={game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime};""", """    const hist={game:before, selected, legalTargets:deepClone(legalTargets), moveTexts:deepClone(moveTexts), flipped, mode, humanColor, aiColor, aiTime, move};""")

# Return both threat squares and color for the moved piece.
s = s.replace("""  function threatenedSquaresFromLastMove(){
    const last=history[history.length-1]?.move;
    if(!last) return new Set();
    const p=game.board[last.to[0]][last.to[1]];
    if(!p) return new Set();
    const color=pieceColor(p);
    const out=new Set();
    try{
      for(const m of legalMovesFor(game,color)){
        if(m.from[0]===last.to[0] && m.from[1]===last.to[1]){
          const target=game.board[m.to[0]][m.to[1]];
          if(target && pieceColor(target)!==color) out.add(`${m.to[0]},${m.to[1]}`);
        }
      }
    }catch(e){}
    return out;
  }""", """  function threatenedInfoFromLastMove(){
    const last=history[history.length-1]?.move;
    const out={squares:new Set(), colors:null};
    if(!last) return out;
    const p=game.board[last.to[0]][last.to[1]];
    if(!p) return out;
    const color=pieceColor(p);
    out.colors=pieceFxColors(pieceType(p));
    try{
      for(const m of legalMovesFor(game,color)){
        if(m.from[0]===last.to[0] && m.from[1]===last.to[1]){
          const target=game.board[m.to[0]][m.to[1]];
          if(target && pieceColor(target)!==color) out.squares.add(`${m.to[0]},${m.to[1]}`);
        }
      }
    }catch(e){}
    return out;
  }""")

s = s.replace("const threatenedByLast=threatenedSquaresFromLastMove();", "const threatenedInfo=threatenedInfoFromLastMove();")
s = s.replace("""        if(threatenedByLast.has(`${r},${c}`)) sq.classList.add('threatened-by-last');""", """        if(threatenedInfo.squares.has(`${r},${c}`)){
          sq.classList.add('threatened-by-last');
          if(threatenedInfo.colors){
            sq.style.setProperty('--threat-color', threatenedInfo.colors.main);
            sq.style.setProperty('--threat-soft', threatenedInfo.colors.soft);
            sq.style.setProperty('--threat-softer', threatenedInfo.colors.soft.replace('.30','.08').replace('.32','.08').replace('.34','.09'));
          }
        }""")

# Color the power beam by moving piece type.
s = s.replace("""      const strong=!!(move.capture || move.enPassantCapture || move.promotion || move.castle);
      const duration=strong?355:285;""", """      const strong=!!(move.capture || move.enPassantCapture || move.promotion || move.castle);
      const duration=strong?355:285;
      const fx=pieceFxColors(pieceType(piece));""")

s = s.replace("""      beam.style.transform=`rotate(${angle}deg) scaleX(.001)`;
      beam.style.opacity='0';""", """      beam.style.transform=`rotate(${angle}deg) scaleX(.001)`;
      beam.style.opacity='0';
      beam.style.background=`linear-gradient(90deg,rgba(0,0,0,0),${fx.soft},${fx.beam},${fx.core},${fx.beam},rgba(0,0,0,0))`;
      beam.style.boxShadow=`0 0 16px ${fx.main},0 0 46px ${fx.soft}${fx.shadow?`,0 0 22px ${fx.shadow}`:''}`;""")

s = s.replace("""      fromEl.classList.add('power-source');
      toEl.classList.add('power-target');""", """      fromEl.classList.add('power-source');
      toEl.classList.add('power-target');
      fromEl.style.setProperty('--threat-color', fx.main);
      toEl.style.setProperty('--threat-color', fx.main);""")

# Vibrate immediately at the beginning too, so it feels responsive.
s = s.replace("""    isAnimatingMove=true;
    visualMove={from:move.from, to:move.to, capture:!!(move.capture||move.enPassantCapture), piece:before.board[move.from[0]][move.from[1]]};""", """    isAnimatingMove=true;
    haptic(move.capture||move.enPassantCapture?'capture':'move');
    visualMove={from:move.from, to:move.to, capture:!!(move.capture||move.enPassantCapture), piece:before.board[move.from[0]][move.from[1]]};""")

p.write_text(s, encoding='utf-8')
print('Fixed haptics and colored threat/power glows.')
