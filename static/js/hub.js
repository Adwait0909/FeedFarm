// Minimal interactions for hub: smooth focus, accessible keyboard, no fake functionality
document.addEventListener('DOMContentLoaded', function(){
  // Make primary cards keyboard-focusable and show focus styles
  document.querySelectorAll('.card.primary').forEach(function(el){
    el.setAttribute('tabindex','0');
    el.addEventListener('keypress', function(e){
      if(e.key === 'Enter' || e.key === ' ') el.click();
    });
  });
});
