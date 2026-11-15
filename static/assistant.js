// All model requests go through our server. No provider key reaches the browser.
(() => {
  const $ = id => document.getElementById(id);
  const text = () => I18N[currentLang];
  let history = [], busy = false, fingerprint = '', revision = 0;
  const chat = $('sageChat'), input = $('sageChatInput'), send = $('sageChatSend');
  // A small DOM-only Markdown renderer. Raw HTML and links stay inert text.
  function inlineMarkdown(parent, content) {
    const pattern = /(\*{1,3})([^*\n]+)\1|`([^`\n]+)`/g;
    let offset = 0, match;
    while ((match = pattern.exec(content))) {
      parent.append(document.createTextNode(content.slice(offset, match.index)));
      const tag = match[3] !== undefined ? 'code' : match[1].length > 1 ? 'strong' : 'em';
      const element = document.createElement(tag);
      element.textContent = match[3] !== undefined ? match[3] : match[2];
      parent.append(element);
      offset = pattern.lastIndex;
    }
    parent.append(document.createTextNode(content.slice(offset)));
  }
  function renderMarkdown(parent, content) {
    let list = null, listKind = '', code = null;
    for (const line of content.split('\n')) {
      if (line.trim().startsWith('```')) {
        if (code) code = null;
        else { const pre = document.createElement('pre'); code = document.createElement('code'); pre.append(code); parent.append(pre); }
        list = null; continue;
      }
      if (code) { code.textContent += line + '\n'; continue; }
      if (!line.trim()) { list = null; continue; }
      const item = line.match(/^\s*(?:[-*•]\s+|\d+[.)]\s+)(.*)$/);
      if (item) {
        const kind = /^\s*\d/.test(line) ? 'ol' : 'ul';
        if (!list || kind !== listKind) { list = document.createElement(kind); listKind = kind; parent.append(list); }
        const li = document.createElement('li'); inlineMarkdown(li, item[1]); list.append(li);
      } else {
        list = null;
        const heading = line.match(/^#{1,6}\s+(.*)$/);
        const paragraph = document.createElement('p');
        if (heading) { const strong = document.createElement('strong'); inlineMarkdown(strong, heading[1]); paragraph.append(strong); }
        else inlineMarkdown(paragraph, line);
        parent.append(paragraph);
      }
    }
  }
  function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    const label = document.createElement('span');
    label.className = 'chat-message-label';
    label.textContent = role === 'user' ? text().chat_you : 'SAGE';
    div.append(label);
    if (role === 'assistant') {
      const body = document.createElement('div'); body.className = 'chat-markdown';
      renderMarkdown(body, content); div.append(body);
    } else div.append(document.createTextNode(content));
    $('sageChatMessages').append(div);
    div.scrollIntoView({block:'nearest'});
    return div;
  }
  function reset(message) {
    history = []; revision++;
    $('sageChatMessages').replaceChildren();
    addMessage('assistant', message || text().chat_greeting);
  }
  function open() {
    chat.hidden = false;
    $('openSageChat').setAttribute('aria-expanded','true');
    input.focus();
  }
  function close() {
    chat.hidden = true;
    $('openSageChat').setAttribute('aria-expanded','false');
    $('openSageChat').focus();
  }
  function context() {
    if (!appState.ort || !appState.rotationResult) return {analysis_available:false};
    return {
      analysis_available:true,
      field:{...appState.analysisField, field_size_decare:Number(fieldSizeInput.value)},
      observations:appState.ort, monthly:appState.aylik?.properties?.parameter || null,
      historical_climate:appState.cok_yillik,
      farmer_inputs:appState.rotationInputs,
      results:appState.rotationResult,
      source_notes:'NASA POWER gridded daily/monthly. RH2M is relative air humidity, not soil moisture. No live SMAP. Crop health is unsimulated observed weather; scenario only affects rotation. Income is gross, not profit.'
    };
  }
  function refreshLabels() {
    $('chatContextLabel').textContent = appState.rotationResult ? `${text().chat_context} · ${appState.analysisField?.start || ''}–${appState.analysisField?.end || ''}` : text().chat_no_context;
    send.textContent = busy ? text().chat_sending : text().chat_send;
    $('closeSageChat').setAttribute('aria-label', currentLang === 'tr' ? 'Sohbeti kapat' : 'Close chat');
  }
  function renderHealth() {
    const health = appState.bitki_sagligi;
    if (!health) return;
    const t = text();
    const historical = health.age_days == null || health.age_days > 7 || health.age_days < 0;
    $('healthPeriod').textContent = `${health.start_date || '—'} → ${health.latest_date || '—'} · ${historical ? t.health_historical : t.health_recent} · ${health.valid_days}/7 ${t.health_days}`;
    $('healthCards').replaceChildren();
    for (const card of health.cards || []) {
      const article = document.createElement('article');
      article.className = 'health-card'; article.dataset.status = card.status;
      const elements = [['span', t[`health_${card.status}`], 'health-status'],['h4',card.title,''],
        ['p',`${card.matching_days}/${card.valid_days} ${t.health_matches}`, 'health-evidence'],['p',card.criteria,''],['p',card.action,'']];
      elements.forEach(([tag,value,cls])=>{const el=document.createElement(tag);el.textContent=value;el.className=cls;article.append(el);});
      $('healthCards').append(article);
    }
    $('healthLimits').textContent = (health.valid_days < 4 ? t.health_missing+' ' : '') + health.limitation;
  }
  window.addEventListener('sage:analysis', () => {
    const next = JSON.stringify(context());
    if (fingerprint && next !== fingerprint) reset(text().chat_updated);
    fingerprint = next;
    refreshLabels(); renderHealth();
  });
  window.addEventListener('sage:language', () => { refreshLabels(); if (!history.length) reset(); });
  $('openSageChat').addEventListener('click', () => chat.hidden ? open() : close());
  $('closeSageChat').addEventListener('click', close);
  $('resetSageChat').addEventListener('click', () => reset());
  chat.addEventListener('keydown', event => { if(event.key === 'Escape') close(); });
  input.addEventListener('input', () => { $('chatCharCount').textContent = `${input.value.length} / 2000`; });
  input.addEventListener('keydown',event=>{if(event.key === 'Enter' && !event.shiftKey && !event.isComposing){event.preventDefault();$('sageChatForm').requestSubmit();}});
  document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click',()=>{input.value=text()[button.dataset.question]; input.dispatchEvent(new Event('input'));input.focus();}));
  $('healthAskAssistant').addEventListener('click',()=>{open();input.value=text().chat_health_question;input.dispatchEvent(new Event('input'));});
  $('sageChatForm').addEventListener('submit', async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    const requestRevision = revision;
    const previous = history.slice(-12).map(turn => ({...turn, content:turn.content.slice(0,6000)}));
    addMessage('user',message);
    input.value=''; input.dispatchEvent(new Event('input'));
    busy=true;send.disabled=true;refreshLabels();
    const pending = addMessage('assistant', text().chat_sending);
    const controller = new AbortController();
    const timeout = setTimeout(()=>controller.abort(),85000);
    try {
      const response = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message, history:previous, context:context(),lang:currentLang}),signal:controller.signal});
      const data = await response.json();
      if (!response.ok) { const err = new Error(data.error); err.code=data.error; throw err; }
      if (requestRevision !== revision) return;
      pending.remove();
      addMessage('assistant',data.reply);
      history = [...previous,{role:'user',content:message},{role:'assistant',content:data.reply}].slice(-12);
    } catch(error) {
      if (requestRevision !== revision) return;
      pending.remove();
      const key = error.code === 'rate_limited' ? 'chat_rate' : error.code === 'not_configured' ? 'chat_not_configured' : error.code?.startsWith('provider') ? 'chat_unavailable' : 'chat_error';
      addMessage('error', text()[key]);
      // Keep the failed question editable for an explicit retry.
      input.value = message; input.dispatchEvent(new Event('input'));
    } finally {
      clearTimeout(timeout);busy=false;send.disabled=false;refreshLabels();
    }
  });
  reset();refreshLabels();
})();
