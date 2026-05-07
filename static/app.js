/**
 * Helena — Frontend Logic
 * Handles knock animation, screen transitions, chat interaction,
 * and communication with the Flask backend.
 */

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // DOM references
  // -----------------------------------------------------------------------
  const knockScreen   = document.getElementById("knock-screen");
  const chatScreen    = document.getElementById("chat-screen");
  const messagesEl    = document.getElementById("chat-messages");
  const inputEl       = document.getElementById("message-input");
  const sendBtn       = document.getElementById("send-btn");
  const headerStatus  = document.getElementById("header-status");

  // Fetch visitor count
  fetch("/visit-count")
      .then(res => res.json())
      .then(data => {
          const el = document.getElementById("visitor-count");
          if (el && data.count !== null) el.textContent = data.count;
      })
      .catch(() => {
          document.getElementById("visitor-count").textContent = "—";
      });

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  let sessionId = null;
  let isWaiting = false;


  // =======================================================================
  // 1. KNOCK SCREEN
  // =======================================================================

  knockScreen.addEventListener("click", handleKnock, { once: true });

  function handleKnock() {
    // Play knock animation
    knockScreen.classList.add("knocking");

    // After animation (~800ms), transition to chat
    setTimeout(() => {
      // Generate session ID at knock time (per SSD spec)
      sessionId = crypto.randomUUID();

      // Fade out knock screen
      knockScreen.classList.add("hidden");

      // Show chat screen after knock fades
      setTimeout(() => {
        chatScreen.classList.add("visible");

        // Force a reflow then set opacity for the fade-in
        requestAnimationFrame(() => {
          chatScreen.style.opacity = "1";
        });

        // Focus the input
        inputEl.focus();

        // Add Helena's greeting
        addBubble(
          "helena",
          "Ugh, you actually showed up. What do you want?"
        );
      }, 300);
    }, 800);
  }


  // =======================================================================
  // 2. CHAT — SEND MESSAGE
  // =======================================================================

  // Send on button click
  sendBtn.addEventListener("click", sendMessage);

  // Send on Enter key
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isWaiting) return;

    // Render user's bubble
    addBubble("user", text);
    inputEl.value = "";

    // Lock UI
    setWaiting(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      });

      const data = await res.json();

      // Remove typing indicator
      removeTypingIndicator();

      if (res.ok && data.reply) {
        addBubble("helena", data.reply);
      } else {
        addErrorBubble(data.error || "Something went wrong.");
      }
    } catch (err) {
      removeTypingIndicator();
      addErrorBubble(
        "Even my server is embarrassed to deal with you right now. Try again."
      );
      console.error("[Helena] Fetch error:", err);
    } finally {
      setWaiting(false);
    }
  }


  // =======================================================================
  // 3. BUBBLE RENDERING
  // =======================================================================

  function addBubble(type, text) {
    const bubble = document.createElement("div");
    bubble.classList.add("bubble", `bubble-${type}`);

    const msgSpan = document.createElement("span");
    msgSpan.textContent = text;
    bubble.appendChild(msgSpan);

    const timeEl = document.createElement("div");
    timeEl.classList.add("bubble-time");
    timeEl.textContent = getCurrentTime();
    bubble.appendChild(timeEl);

    messagesEl.appendChild(bubble);
    scrollToBottom();
  }

  function addErrorBubble(text) {
    const bubble = document.createElement("div");
    bubble.classList.add("bubble", "bubble-error");

    // Error tag
    const tag = document.createElement("div");
    tag.classList.add("error-tag");
    tag.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      API Error
    `;
    bubble.appendChild(tag);

    const msgSpan = document.createElement("span");
    msgSpan.textContent = text;
    bubble.appendChild(msgSpan);

    const timeEl = document.createElement("div");
    timeEl.classList.add("bubble-time");
    timeEl.textContent = getCurrentTime();
    bubble.appendChild(timeEl);

    messagesEl.appendChild(bubble);
    scrollToBottom();
  }


  // =======================================================================
  // 4. TYPING INDICATOR
  // =======================================================================

  function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.classList.add("typing-indicator");
    indicator.id = "typing-indicator";
    indicator.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(indicator);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
  }


  // =======================================================================
  // 5. UI STATE HELPERS
  // =======================================================================

  function setWaiting(waiting) {
    isWaiting = waiting;
    sendBtn.disabled = waiting;
    inputEl.disabled = waiting;

    if (waiting) {
      headerStatus.textContent = "typing...";
      showTypingIndicator();
    } else {
      headerStatus.textContent = "online · probably judging you";
      inputEl.focus();
    }
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
})();
