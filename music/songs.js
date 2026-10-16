// Tap a cover to hear the song's 30-second preview; one plays at a time.
// Also sends the recommendation form, when there is one.
(() => {
  let audio = null, current = null;
  const stop = () => {
    if (audio) audio.pause();
    if (current) current.classList.remove("playing");
    audio = current = null;
  };
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-preview]");
    if (!btn) return;
    if (btn === current) return stop();
    stop();
    audio = new Audio(btn.dataset.preview);
    current = btn;
    btn.classList.add("playing");
    audio.addEventListener("ended", stop);
    audio.play().catch(stop);
  });

  const form = document.querySelector(".recommend form");
  if (!form) return;
  const status = form.querySelector(".recommend-status");
  form.addEventListener("submit", async (e) => {
    const data = new FormData(form);
    const to = form.dataset.mailto;
    e.preventDefault();
    if (to) {
      const subject = "A song for you: " + data.get("song");
      const body = [`Song: ${data.get("song")}`, `Artist: ${data.get("artist")}`,
        data.get("why") ? `\n${data.get("why")}` : "", data.get("name") ? `\n— ${data.get("name")}` : ""].join("\n");
      // If an email app opens, the page loses focus: clear the form and say thanks.
      // If nothing has opened after a moment, offer to copy the message instead.
      let done = false;
      const opened = () => {
        if (done) return;
        done = true;
        form.reset();
        status.textContent = "Thank you! I'll give it a listen.";
      };
      window.addEventListener("blur", opened, { once: true });
      setTimeout(() => window.removeEventListener("blur", opened), 15000);
      location.href = `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      status.textContent = "Opening your email app…";
      setTimeout(() => {
        if (done) return;
        if (!document.hasFocus()) return opened();
        status.textContent = "";
        const msg = document.createElement("span");
        msg.textContent = `No email app opened. Send it to ${to} instead: `;
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "linklike";
        copy.textContent = "copy the address and message";
        copy.addEventListener("click", async () => {
          try {
            await navigator.clipboard.writeText(`To: ${to}\nSubject: ${subject}\n\n${body}`);
            done = true;
            form.reset();
            status.textContent = "Copied. Paste it into an email to send it. Thank you!";
          } catch {
            copy.textContent = `copying didn't work; the address is ${to}`;
          }
        });
        status.append(msg, copy);
      }, 1500);
      return;
    }
    status.textContent = "Sending…";
    try {
      const r = await fetch(form.action, { method: "POST", body: data, headers: { Accept: "application/json" } });
      if (!r.ok) throw new Error();
      form.reset();
      status.textContent = "Thank you. I'll give it a listen.";
    } catch {
      status.textContent = "That didn't go through. Please try again in a moment.";
    }
  });
})();
