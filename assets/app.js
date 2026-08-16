// Next Step 3PL — shared site JS (nav, year, reveal, FAQ, homepage calculator)
(function(){
  // year
  var yr=document.getElementById('yr'); if(yr){ yr.textContent=new Date().getFullYear(); }
  // mobile nav
  var nt=document.getElementById('navToggle'),nl=document.getElementById('navlinks');
  if(nt&&nl){
    nt.addEventListener('click',function(){var o=nl.classList.toggle('open');nt.setAttribute('aria-expanded',o);});
    nl.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){nl.classList.remove('open');nt.setAttribute('aria-expanded',false);});});
  }
  // reveal on scroll
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
  } else {
    document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});
  }
  // FAQ accordion
  document.querySelectorAll('.qa button').forEach(function(b){b.addEventListener('click',function(){var qa=b.parentElement,ans=qa.querySelector('.ans'),open=qa.classList.contains('open');document.querySelectorAll('.qa').forEach(function(x){x.classList.remove('open');var a=x.querySelector('.ans');if(a)a.style.maxHeight=null;});if(!open){qa.classList.add('open');ans.style.maxHeight=ans.scrollHeight+'px';}});});

  // ---- Homepage cost calculator (only runs where the calculator exists) ----
  if(document.getElementById('s_pal')){
    function money(n){return '$'+n.toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:0});}
    function money2(n){return n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}
    function setRangeFill(el){var p=(el.value-el.min)/(el.max-el.min)*100;el.style.setProperty('--p',p+'%');}
    function bigMoney(n){var d=n.toFixed(2).split('.');document.getElementById('r_big').innerHTML=money(parseInt(d[0]))+'<span class="cents">.'+d[1]+'</span>';}
    var kicker={storage:'Estimated monthly storage',fulfil:'Estimated monthly fulfillment'};
    document.querySelectorAll('.calc-tab').forEach(function(t){t.addEventListener('click',function(){document.querySelectorAll('.calc-tab').forEach(function(x){x.classList.remove('active');});t.classList.add('active');var tab=t.dataset.tab;document.getElementById('p-storage').classList.toggle('active',tab==='storage');document.getElementById('p-fulfil').classList.toggle('active',tab==='fulfil');document.getElementById('r_kicker').textContent=kicker[tab];tab==='storage'?calcStorage():calcFulfil();});});
    var sPal=document.getElementById('s_pal'),sMo=document.getElementById('s_mo'),sType=document.getElementById('s_type');
    var sRate=18;
    function calcStorage(){
      var pal=+sPal.value,mo=+sMo.value;
      document.getElementById('s_pal_v').textContent=pal.toLocaleString();
      document.getElementById('s_mo_v').textContent=mo+' mo';
      setRangeFill(sPal);setRangeFill(sMo);
      var monthly=pal*sRate, receiving=pal*35, total=monthly*mo+receiving;
      document.getElementById('r_kicker').textContent='Estimated monthly storage';
      bigMoney(monthly);
      document.getElementById('r_per').textContent='≈ $'+money2(sRate)+' / unit / month';
      document.getElementById('r_break').innerHTML=
        '<div class="brow"><span>Storage — '+pal+' units × $'+sRate+'</span><b>'+money(monthly)+'/mo</b></div>'+
        '<div class="brow"><span>One-time receiving ('+pal+' × $35)</span><b>'+money(receiving)+'</b></div>'+
        '<div class="brow"><span>Duration</span><b>'+mo+' months</b></div>'+
        '<div class="brow total"><span>Total over '+mo+' mo</span><b>'+money(total)+'</b></div>';
    }
    sPal.addEventListener('input',calcStorage);sMo.addEventListener('input',calcStorage);
    sType.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){sType.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');sRate=+b.dataset.rate;calcStorage();});});
    var fOrd=document.getElementById('f_ord'),fItem=document.getElementById('f_item'),fAddon=document.getElementById('f_addon');
    var fAdd=0, PICK_FIRST=2.50, PICK_ADDL=0.65;
    function calcFulfil(){
      var ord=+fOrd.value,items=+fItem.value;
      document.getElementById('f_ord_v').textContent=ord.toLocaleString();
      document.getElementById('f_item_v').textContent=items;
      setRangeFill(fOrd);setRangeFill(fItem);
      var perOrder=PICK_FIRST+(items-1)*PICK_ADDL+fAdd;
      var monthly=perOrder*ord;
      document.getElementById('r_kicker').textContent='Estimated monthly fulfillment';
      bigMoney(monthly);
      document.getElementById('r_per').textContent='≈ $'+money2(perOrder)+' / order';
      document.getElementById('r_break').innerHTML=
        '<div class="brow"><span>Pick &amp; pack (1st item)</span><b>$'+money2(PICK_FIRST)+'</b></div>'+
        '<div class="brow"><span>+ '+(items-1)+' extra item(s) × $'+money2(PICK_ADDL)+'</span><b>$'+money2((items-1)*PICK_ADDL)+'</b></div>'+
        (fAdd>0?'<div class="brow"><span>Add-on per order</span><b>$'+money2(fAdd)+'</b></div>':'')+
        '<div class="brow"><span>Orders / month</span><b>'+ord.toLocaleString()+'</b></div>'+
        '<div class="brow total"><span>Monthly fulfillment</span><b>'+money(monthly)+'</b></div>';
    }
    fOrd.addEventListener('input',calcFulfil);fItem.addEventListener('input',calcFulfil);
    fAddon.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){fAddon.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');fAdd=+b.dataset.add;calcFulfil();});});
    calcStorage();
  }

  // ---- Quote form: send to WhatsApp (+ email via Web3Forms when configured) ----
  var qf = document.getElementById('quoteForm');
  if (qf) {
    var WEB3_KEY = '711de223-8d1c-4e63-a23a-7ef0a0110fe7'; // Web3Forms access key — set this to also email contact@nextstep3pl.com
    qf.addEventListener('submit', function(e){
      e.preventDefault();
      function v(id){ var el = document.getElementById(id); return el ? el.value : ''; }
      var name=v('qf_name'), company=v('qf_company'), email=v('qf_email'), phone=v('qf_phone'), volume=v('qf_volume'), needs=v('qf_needs');
      var text = ['New quote request — nextstep3pl.com','Name: '+name,'Company: '+company,'Email: '+email,'Phone: '+phone,'Monthly volume: '+volume,'Needs: '+needs].join('\n');
      if (WEB3_KEY) {
        fetch('https://api.web3forms.com/submit', {method:'POST', headers:{'Content-Type':'application/json', 'Accept':'application/json'}, body: JSON.stringify({access_key: WEB3_KEY, subject:'New quote request — nextstep3pl.com', from_name:'Next Step 3PL Website', name:name, company:company, email:email, phone:phone, monthly_volume:volume, message:needs})}).catch(function(){});
      }
      window.open('https://wa.me/17375373986?text=' + encodeURIComponent(text), '_blank');
      var btn = qf.querySelector('button[type=submit]');
      if (btn) { btn.textContent = "✓ Opening WhatsApp — or we'll email you back"; btn.disabled = true; }
    });
  }
})();
