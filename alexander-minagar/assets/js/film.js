(() => {
  const config = window.SITE_CONTENT && window.SITE_CONTENT.film;
  if (!config) return;
  document.title = `${config.title} | ${window.SITE_CONTENT.name}`;
  document.getElementById("film-eyebrow").textContent = config.eyebrow || "01 / Film";
  document.getElementById("film-synopsis")?.replaceChildren(config.synopsis || "");
  const metadata = document.getElementById("film-metadata");
  [["Year", config.year], ["Runtime", config.runtime], ["My role", config.role]].forEach(([label, value]) => {
    if (!value) return;
    const group = document.createElement("div");
    const term = document.createElement("dt");
    const definition = document.createElement("dd");
    term.textContent = label;
    definition.textContent = value;
    group.append(term, definition);
    metadata?.append(group);
  });
  if (metadata) metadata.hidden = !metadata.children.length;
  if (Array.isArray(config.credits) && config.credits.length) {
    const list = document.getElementById("film-credit-list");
    config.credits.forEach(credit => {
      const item = document.createElement("li");
      item.textContent = typeof credit === "string" ? credit : `${credit.role || ""}${credit.role && credit.name ? ": " : ""}${credit.name || ""}`;
      list.append(item);
    });
    document.getElementById("film-credits").hidden = false;
  }
  if (!config.videoUrl || !config.videoUrl.trim()) return;
  const screen = document.getElementById("film-screen");
  const caption = document.getElementById("film-caption");
  const external = document.getElementById("film-external-link");
  const raw = config.videoUrl.trim();
  let url;
  try { url = new URL(raw, document.baseURI); } catch { caption.textContent = "The film link is unavailable. Please check back later."; return; }
  if (!["https:", "http:", "file:"].includes(url.protocol)) return;
  const hostname = url.hostname.replace(/^www\./, "");
  let embedUrl = "";
  if (["youtube.com", "m.youtube.com", "youtube-nocookie.com", "youtu.be"].includes(hostname)) {
    const parts = url.pathname.split("/").filter(Boolean);
    const candidate = hostname === "youtu.be" ? parts[0] : url.searchParams.get("v") || (["embed", "shorts"].includes(parts[0]) ? parts[1] : "");
    if (/^[A-Za-z0-9_-]{11}$/.test(candidate || "")) embedUrl = `https://www.youtube-nocookie.com/embed/${candidate}`;
  } else if (["vimeo.com", "player.vimeo.com"].includes(hostname)) {
    const parts = url.pathname.split("/").filter(Boolean);
    const idIndex = parts.findIndex(part => /^\d+$/.test(part));
    if (idIndex !== -1) {
      const secret = url.searchParams.get("h") || parts[idIndex + 1];
      embedUrl = `https://player.vimeo.com/video/${parts[idIndex]}${secret && /^[a-zA-Z0-9]+$/.test(secret) ? `?h=${secret}` : ""}`;
    }
  }
  if (url.protocol !== "file:") { external.href = url.href; external.hidden = false; }
  if (embedUrl) {
    const frame = document.createElement("iframe");
    frame.src = embedUrl;
    frame.title = config.title;
    frame.loading = "lazy";
    frame.allow = "accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen";
    frame.allowFullscreen = true;
    frame.referrerPolicy = "strict-origin-when-cross-origin";
    screen.replaceChildren(frame);
    if (caption) caption.textContent = "If the embedded player is unavailable, open the film using the link below.";
  } else if (/\.(mp4|webm|ogg)$/i.test(url.pathname)) {
    const video = document.createElement("video");
    video.controls = true;
    video.playsInline = true;
    video.preload = "metadata";
    video.src = url.href;
    if (config.poster) video.poster = config.poster;
    if (config.captionsUrl) {
      const track = document.createElement("track");
      track.kind = "captions";
      track.label = "English";
      track.srclang = "en";
      track.src = config.captionsUrl;
      track.default = true;
      video.append(track);
    }
    video.addEventListener("error", () => { caption.textContent = "The video could not load. Please check back later or try the film link."; });
    screen.replaceChildren(video);
    caption.textContent = config.captionsUrl ? "Use the player controls to enable captions." : "";
  } else {
    const title = screen.querySelector("h2");
    const message = screen.querySelector("p");
    title.textContent = "Watch the film";
    message.textContent = "Open the film using the link below.";
    caption.textContent = "The film opens on its video hosting page.";
  }
})();
