(function () {
  const log = document.getElementById("log");
  const text = document.getElementById("text");
  const send = document.getElementById("send");
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // Keep the typing dots visible for at least this long (milliseconds)
  const MIN_TYPING_TIME = 600;

  // Change these to questions your documents can answer
  const starters = [
    "How do I register a business name?",
    "What is a Negosyo Center?",
    "What are your office hours?"
  ];

  function showWelcome() {
    log.innerHTML = "";

    const hello = document.createElement("div");
    hello.className = "hello";

    hello.innerHTML =
      "<h2>How can we help your business?</h2>" +
      "<p>Ask about DTI services in Baguio and Benguet, or pick a question below.</p>";

    const chips = document.createElement("div");
    chips.className = "chips";

    starters.forEach(function (label) {
      const button = document.createElement("button");

      button.type = "button";
      button.className = "chip";
      button.textContent = label;

      button.onclick = function () {
        sendMessage(label);
      };

      chips.appendChild(button);
    });

    hello.appendChild(chips);
    log.appendChild(hello);
  }

  // Escape text so replies can never inject HTML
  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Inline formatting: **bold**, `code`, [link](https://...)
  function formatInline(value) {
    return escapeHtml(value)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(
        /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
      );
  }

  // Turn the model's markdown-style text into paragraphs and lists
  function renderMarkdown(source) {
    const lines = source.replace(/\r\n/g, "\n").split("\n");
    let html = "";
    let listType = null;
    let paragraph = [];

    function flushParagraph() {
      if (paragraph.length > 0) {
        html += "<p>" + paragraph.map(formatInline).join("<br>") + "</p>";
        paragraph = [];
      }
    }

    function closeList() {
      if (listType) {
        html += "</" + listType + ">";
        listType = null;
      }
    }

    lines.forEach(function (raw) {
      const line = raw.trim();

      if (!line) {
        flushParagraph();
        closeList();
        return;
      }

      const bullet = line.match(/^[-*\u2022]\s+(.*)/);
      const number = line.match(/^\d+[.)]\s+(.*)/);
      const heading = line.match(/^#{1,6}\s+(.*)/);

      if (bullet || number) {
        flushParagraph();
        const type = bullet ? "ul" : "ol";

        if (listType !== type) {
          closeList();
          html += "<" + type + ">";
          listType = type;
        }

        html += "<li>" + formatInline((bullet || number)[1]) + "</li>";
        return;
      }

      closeList();

      if (heading) {
        flushParagraph();
        html += "<p><strong>" + formatInline(heading[1]) + "</strong></p>";
        return;
      }

      paragraph.push(line);
    });

    flushParagraph();
    closeList();

    return html;
  }

  // Add a message bubble
  function addMessage(type, content) {
    const bubble = document.createElement("div");

    bubble.className = "msg " + type;
    if (type === "bot") {
      bubble.innerHTML = renderMarkdown(content);
    } else {
      bubble.textContent = content;
    }

    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;

    return bubble;
  }

  // Add a small "Sources" line under a bot reply
  function addSources(sources) {
    if (!Array.isArray(sources) || sources.length === 0) {
      return;
    }

    const line = document.createElement("div");
    line.className = "sources";
    line.append("Sources: ");

    sources.forEach(function (item, index) {
      if (index > 0) {
        line.append(", ");
      }

      const title = item.title || item.id;

      if (item.source && item.source.startsWith("http")) {
        const link = document.createElement("a");
        link.href = item.source;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = title;
        line.appendChild(link);
      } else {
        line.append(title);
      }
    });

    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
  }

  // Show typing animation
  function showTyping() {
    const dots = document.createElement("div");

    dots.className = "msg bot typing";
    dots.innerHTML = "<i></i><i></i><i></i>";

    log.appendChild(dots);
    log.scrollTop = log.scrollHeight;

    return dots;
  }

  // Update Send button state
  function updateSendButton() {
    send.disabled = !text.value.trim();
  }

  // Send message to Flask
  async function sendMessage(message) {
    message = message.trim();

    if (!message) {
      return;
    }

    addMessage("me", message);

    text.value = "";
    send.disabled = true;

    const typing = showTyping();
    const startedAt = Date.now();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: message
        })
      });

      if (!response.ok) {
        throw new Error("Request failed: " + response.status);
      }

      const data = await response.json();

      if (typeof data.reply !== "string") {
        throw new Error("Invalid server response");
      }

      // Make sure the typing dots are visible for a moment
      const elapsed = Date.now() - startedAt;
      if (elapsed < MIN_TYPING_TIME) {
        await wait(MIN_TYPING_TIME - elapsed);
      }

      typing.remove();
      addMessage("bot", data.reply);
      addSources(data.sources);

    } catch (error) {
      console.error("Chat error:", error);

      typing.remove();

      addMessage(
        "bot",
        "Something went wrong. Please try again."
      );

    } finally {
      updateSendButton();
      text.focus();
    }
  }

  // Enable Send button when input has text
  text.addEventListener("input", updateSendButton);

  // Send on Enter
  text.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();

      if (!send.disabled) {
        sendMessage(text.value);
      }
    }
  });

  // Send on button click
  send.addEventListener("click", function () {
    sendMessage(text.value);
  });

  // Initialize chatbot
  showWelcome();
  updateSendButton();

})();