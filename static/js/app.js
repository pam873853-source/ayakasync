document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const saved = localStorage.getItem("ayaka-theme");
  if (saved) root.dataset.theme = saved;
  document.getElementById("themeToggle")?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("ayaka-theme", root.dataset.theme);
  });

  const sidebar = document.getElementById("sidebar");
  const menuButton = document.getElementById("mobileMenu");
  menuButton?.addEventListener("click", (event) => {
    event.stopPropagation();
    sidebar?.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", sidebar?.classList.contains("open") ? "true" : "false");
  });
  document.addEventListener("click", (event) => {
    if (sidebar && menuButton && sidebar.classList.contains("open") &&
        !sidebar.contains(event.target) && !menuButton.contains(event.target)) {
      sidebar.classList.remove("open"); menuButton.setAttribute("aria-expanded", "false");
    }
  });

  const pad = n => String(n).padStart(2, "0");
  const clock = document.getElementById("liveClock");
  const date = document.getElementById("liveDate");
  function updateDateTime(){
    const now = new Date();
    if(clock) clock.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    if(date) date.textContent = new Intl.DateTimeFormat('id-ID',{day:'2-digit',month:'short',year:'numeric'}).format(now);
  }
  updateDateTime(); setInterval(updateDateTime, 1000);

  // Personalized greeting follows the visitor's current local/world time.
  const greeting = document.getElementById("liveGreeting");
  function updateGreeting() {
    if (!greeting) return;
    const hour = new Date().getHours();
    let period = "malam";
    if (hour >= 4 && hour < 11) period = "pagi";
    else if (hour >= 11 && hour < 15) period = "siang";
    else if (hour >= 15 && hour < 18) period = "sore";
    const accountName = greeting.dataset.name || "Pengguna";
    greeting.textContent = `Selamat ${period}, ${accountName}`;
    greeting.setAttribute("aria-live", "polite");
  }
  updateGreeting();
  setInterval(updateGreeting, 30000);

  // Battery is a browser-provided estimate; unsupported browsers show N/A.
  const batteryLevel = document.getElementById("batteryLevel");
  const batteryIcon = document.getElementById("batteryIcon");
  if (navigator.getBattery) {
    navigator.getBattery().then(battery => {
      const paintBattery = () => {
        const pct = Math.round(battery.level * 100);
        if (batteryLevel) batteryLevel.textContent = `${pct}%${battery.charging ? ' ⚡' : ''}`;
        if (batteryIcon) batteryIcon.textContent = pct > 75 ? '▰' : pct > 35 ? '▰' : '▱';
      };
      paintBattery(); battery.addEventListener('levelchange', paintBattery); battery.addEventListener('chargingchange', paintBattery);
    }).catch(() => { if(batteryLevel) batteryLevel.textContent = 'N/A'; });
  } else if (batteryLevel) batteryLevel.textContent = 'N/A';

  // Session uptime measures time since this page was opened, not server uptime.
  const uptime = document.getElementById("sessionUptime");
  const started = Date.now();
  function updateUptime(){ const sec=Math.floor((Date.now()-started)/1000); if(uptime) uptime.textContent=`${pad(Math.floor(sec/3600))}:${pad(Math.floor(sec/60)%60)}:${pad(sec%60)}`; }
  updateUptime(); setInterval(updateUptime,1000);


  // Ayaka Sync chat assistant. Requests are proxied through Flask to avoid browser CORS issues.
  const chatModal = document.getElementById("ayakaChatModal");
  const openChat = document.getElementById("openAyakaChat");
  const closeChat = document.getElementById("closeAyakaChat");
  const chatForm = document.getElementById("ayakaChatForm");
  const chatInput = document.getElementById("ayakaChatInput");
  const chatMessages = document.getElementById("ayakaChatMessages");
  const chatSend = document.getElementById("ayakaChatSend");
  function showChat() {
    if (!chatModal) return;
    chatModal.classList.add("open"); chatModal.setAttribute("aria-hidden", "false");
    window.setTimeout(() => chatInput?.focus(), 80);
  }
  function hideChat() {
    chatModal?.classList.remove("open"); chatModal?.setAttribute("aria-hidden", "true");
  }
  openChat?.addEventListener("click", showChat);
  closeChat?.addEventListener("click", hideChat);
  chatModal?.addEventListener("click", event => { if (event.target === chatModal) hideChat(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape") hideChat(); });
  function addChatBubble(text, type = "assistant") {
    if (!chatMessages) return null;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${type}`;
    bubble.textContent = text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }
  chatForm?.addEventListener("submit", async event => {
    event.preventDefault();
    const message = chatInput?.value.trim();
    if (!message || !chatSend) return;
    addChatBubble(message, "user");
    chatInput.value = ""; chatInput.disabled = true; chatSend.disabled = true;
    const waiting = addChatBubble("Ayaka lagi mikir dulu ya... ✨", "assistant");
    try {
      const response = await fetch("/api/ayaka-chat", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
      });
      const data = await response.json();
      waiting?.remove();
      if (!response.ok || !data.status || !data.result) throw new Error(data.error || "Ayaka belum bisa membalas. Coba lagi ya.");
      addChatBubble(data.result, "assistant");
    } catch (error) {
      waiting?.remove();
      addChatBubble(error.message || "Koneksi Ayaka AI sedang bermasalah. Coba lagi ya.", "assistant error");
    } finally {
      chatInput.disabled = false; chatSend.disabled = false; chatInput.focus();
    }
  });

  const mode = document.getElementById("orderMode");
  const order = document.getElementById("orderId");
  mode?.addEventListener("change", () => { if(order){order.disabled=mode.value!=="manual";order.required=mode.value==="manual";if(mode.value!=="manual")order.value="";} });

  // Progressive enhancement: never hide page content while waiting for GSAP/CDN.
  if (window.gsap) {
    if (window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
    gsap.from(".hero-copy", {y:24, duration:.65, ease:"power2.out"});
    gsap.from(".hero-art", {y:24, duration:.8, delay:.08, ease:"power2.out"});
    if (window.ScrollTrigger) {
      // Repeating reveal: animate on every entry and reverse when scrolling away.
      // This keeps the motion active in both scroll directions, not just the first pass.
      gsap.utils.toArray(".guide-card, .status-card, .feature-card, .tutorial-item, .content-card, .stat-card, .panel").forEach((item, i) => {
        gsap.fromTo(item,
          { y: 26, opacity: 0.35 },
          {
            y: 0, opacity: 1, duration: 0.55,
            delay: (i % 4) * 0.035, ease: "power2.out",
            clearProps: "transform",
            scrollTrigger: {
              trigger: item,
              start: "top 94%",
              end: "bottom 6%",
              toggleActions: "play reverse play reverse",
              invalidateOnRefresh: true
            }
          }
        );
      });
      // Recalculate trigger positions after images/fonts/layout settle.
      window.addEventListener("load", () => ScrollTrigger.refresh(), { once: true });
    } else {
      gsap.from(".guide-card, .status-card, .feature-card, .tutorial-item, .content-card", {
        y:14, duration:.5, stagger:.04, ease:"power2.out"
      });
    }
    if (document.querySelector(".ayaka-emblem")) {
      gsap.to(".ayaka-emblem", {y:-9, duration:2.2, repeat:-1, yoyo:true, ease:"sine.inOut"});
      gsap.to(".orbit-one", {rotation:360, duration:28, repeat:-1, ease:"none"});
      gsap.to(".orbit-two", {rotation:-360, duration:38, repeat:-1, ease:"none"});
    }
  }
});
