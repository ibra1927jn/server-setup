from shared_config import get_ssh_client


def _build_chat_widget():
    """Build the AI chat widget HTML/CSS/JS to inject into the dashboard."""
    return """
<!-- AI Chat Widget -->
<style>
  #chat-toggle {
    position: fixed; bottom: 24px; right: 24px; z-index: 1000;
    width: 56px; height: 56px; border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    border: none; cursor: pointer; box-shadow: 0 4px 20px rgba(124,58,237,0.4);
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  #chat-toggle:hover { transform: scale(1.1); box-shadow: 0 6px 28px rgba(124,58,237,0.6); }
  #chat-toggle svg { width: 28px; height: 28px; fill: white; }

  #chat-panel {
    position: fixed; bottom: 92px; right: 24px; z-index: 999;
    width: 360px; max-height: 480px;
    background: rgba(15, 15, 30, 0.92);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 16px; display: none; flex-direction: column;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    overflow: hidden;
  }
  #chat-panel.open { display: flex; }

  #chat-header {
    padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex; align-items: center; gap: 10px;
  }
  #chat-header .dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; }
  #chat-header span { color: #e2e8f0; font-weight: 600; font-size: 14px; }
  #chat-header small { color: #94a3b8; font-size: 11px; margin-left: auto; }

  #chat-messages {
    flex: 1; overflow-y: auto; padding: 14px; max-height: 320px;
    display: flex; flex-direction: column; gap: 10px;
  }
  .msg { padding: 10px 14px; border-radius: 12px; font-size: 13px;
    line-height: 1.5; max-width: 85%; word-wrap: break-word; }
  .msg.user { background: rgba(124,58,237,0.25); color: #e2e8f0;
    align-self: flex-end; border-bottom-right-radius: 4px; }
  .msg.bot { background: rgba(255,255,255,0.06); color: #cbd5e1;
    align-self: flex-start; border-bottom-left-radius: 4px; }
  .msg.typing { color: #94a3b8; font-style: italic; }

  #chat-input-area {
    padding: 12px; border-top: 1px solid rgba(255,255,255,0.08);
    display: flex; gap: 8px;
  }
  #chat-input {
    flex: 1; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 10px 14px; color: #e2e8f0; font-size: 13px;
    outline: none; transition: border-color 0.2s;
  }
  #chat-input:focus { border-color: rgba(124,58,237,0.5); }
  #chat-input::placeholder { color: #64748b; }
  #chat-send {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    border: none; border-radius: 10px; padding: 0 16px; cursor: pointer;
    color: white; font-size: 14px; transition: opacity 0.2s;
  }
  #chat-send:hover { opacity: 0.85; }
  #chat-send:disabled { opacity: 0.4; cursor: not-allowed; }
</style>

<button id="chat-toggle" onclick="toggleChat()" title="Chat con IA">
  <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1
    0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
</button>

<div id="chat-panel">
  <div id="chat-header">
    <div class="dot"></div>
    <span>AgenticOS IA</span>
    <small>GLM-4.5 Air</small>
  </div>
  <div id="chat-messages" id="chat-messages"></div>
  <div id="chat-input-area">
    <input id="chat-input" type="text" placeholder="Escribe tu pregunta..." autocomplete="off"
           onkeydown="if(event.key==='Enter')sendChat()">
    <button id="chat-send" onclick="sendChat()">Enviar</button>
  </div>
</div>

<script>
  function toggleChat() {
    const p = document.getElementById('chat-panel');
    p.classList.toggle('open');
    if (p.classList.contains('open')) {
      document.getElementById('chat-input').focus();
      loadHistory();
    }
  }

  function loadHistory() {
    const box = document.getElementById('chat-messages');
    if (box.children.length > 0) return;
    const hist = JSON.parse(localStorage.getItem('agentichat') || '[]');
    hist.forEach(m => addBubble(m.role, m.text, false));
    box.scrollTop = box.scrollHeight;
  }

  function addBubble(role, text, save=true) {
    const box = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    if (save) {
      const hist = JSON.parse(localStorage.getItem('agentichat') || '[]');
      hist.push({role, text});
      if (hist.length > 50) hist.splice(0, hist.length - 50);
      localStorage.setItem('agentichat', JSON.stringify(hist));
    }
  }

  async function sendChat() {
    const inp = document.getElementById('chat-input');
    const btn = document.getElementById('chat-send');
    const msg = inp.value.trim();
    if (!msg) return;

    addBubble('user', msg);
    inp.value = '';
    btn.disabled = true;

    const typing = document.createElement('div');
    typing.className = 'msg bot typing';
    typing.textContent = 'Pensando...';
    document.getElementById('chat-messages').appendChild(typing);

    try {
      const res = await fetch('/webhook/ai-agent', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg})
      });
      const data = await res.json();
      typing.remove();
      const reply = data.output || data.text || data.response || JSON.stringify(data);
      addBubble('bot', reply);
    } catch(e) {
      typing.remove();
      addBubble('bot', 'Error de conexión. Intenta de nuevo.');
    }
    btn.disabled = false;
  }
</script>
"""


def main():
    ssh = get_ssh_client()

    # Read current dashboard
    _, o, _ = ssh.exec_command("cat /var/www/dashboard/index.html")
    current_html = o.read().decode()

    # Inject before </body>
    chat_widget = _build_chat_widget()
    new_html = current_html.replace("</body>", chat_widget + "\n</body>")

    # Upload via SFTP
    with ssh.open_sftp() as sftp, sftp.file("/var/www/dashboard/index.html", "w") as f:
        f.write(new_html)

    print("Chat widget deployed to dashboard!")

    ssh.close()


if __name__ == "__main__":
    main()
