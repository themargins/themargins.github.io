-- Pandoc filter for project pages: turns image syntax that points at a
-- video into a proper <video>, and a YouTube/Vimeo link into an embed.
--
--   ![Caption](clip.mov)            video with controls (.mov is served as the converted .mp4)
--   ![Caption](spin.mov){.loop}     silent, autoplaying loop, like a moving photo
--   ![Caption](https://youtu.be/ID) embedded player (Vimeo links work too)
--
-- build_projects.py passes each video's size and poster in the `media` metadata.

local VIDEO = { mov = true, mp4 = true, m4v = true, hevc = true, webm = true }
local media = {}

local function esc(s)
  s = s:gsub("&", "&amp;"):gsub('"', "&quot;"):gsub("<", "&lt;"):gsub(">", "&gt;")
  return s
end

local function embed_url(src)
  local id = src:match("youtu%.be/([%w_-]+)")
    or src:match("youtube%.com/watch%?.-v=([%w_-]+)")
    or src:match("youtube%.com/shorts/([%w_-]+)")
    or src:match("youtube%.com/embed/([%w_-]+)")
  if id then return "https://www.youtube-nocookie.com/embed/" .. id end
  id = src:match("vimeo%.com/(%d+)")
  if id then return "https://player.vimeo.com/video/" .. id .. "?dnt=1" end
end

local function is_video(src)
  return VIDEO[(src:match("%.(%w+)$") or ""):lower()] or embed_url(src) ~= nil
end

local function has_class(el, name)
  for _, c in ipairs(el.classes) do if c == name then return true end end
  return false
end

local function video_html(el)
  local label = esc(pandoc.utils.stringify(el.caption))
  local url = embed_url(el.src)
  if url then
    return '<span class="embed"><iframe src="' .. url .. '" title="' .. label
      .. '" loading="lazy" allow="fullscreen; picture-in-picture" allowfullscreen></iframe></span>'
  end
  local src = el.src
  local ext = (src:match("%.(%w+)$") or ""):lower()
  if ext == "mov" or ext == "m4v" or ext == "hevc" then
    src = src:gsub("%.%w+$", ".mp4")
  end
  local info = media[src:match("([^/]+)$")] or {}
  local attrs = {}
  if has_class(el, "loop") then
    table.insert(attrs, "autoplay muted loop playsinline")
  else
    table.insert(attrs, 'controls playsinline preload="metadata"')
  end
  if label ~= "" then table.insert(attrs, 'aria-label="' .. label .. '"') end
  if info.poster then
    local dir = src:match("^(.*/)") or ""
    table.insert(attrs, 'poster="' .. esc(dir .. info.poster) .. '"')
  end
  if info.w and info.h then
    -- Keep the shape before it loads, and keep tall phone videos within the screen
    table.insert(attrs, string.format(
      'width="%s" height="%s" style="aspect-ratio: %s / %s; width: min(100%%, calc(85vh * %s / %s))"',
      info.w, info.h, info.w, info.h, info.w, info.h))
  end
  return '<video src="' .. esc(src) .. '" ' .. table.concat(attrs, " ") .. '><a href="'
    .. esc(src) .. '">Watch the video</a></video>'
end

local function Meta(m)
  if m.media then
    for name, v in pairs(m.media) do
      media[name] = {
        w = v.w and pandoc.utils.stringify(v.w),
        h = v.h and pandoc.utils.stringify(v.h),
        poster = v.poster and pandoc.utils.stringify(v.poster),
      }
    end
  end
end

-- Pandoc 2: a captioned image on its own line is a paragraph with a "fig:" title.
local function Para(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    local img = el.content[1]
    if is_video(img.src) and img.title:sub(1, 4) == "fig:" and #img.caption > 0 then
      return {
        pandoc.RawBlock("html", "<figure>\n" .. video_html(img) .. "\n<figcaption>"),
        pandoc.Plain(img.caption),
        pandoc.RawBlock("html", "</figcaption>\n</figure>"),
      }
    end
  end
end

local function Image(el)
  if is_video(el.src) then
    return pandoc.RawInline("html", video_html(el))
  end
  el.attributes["loading"] = "lazy"
  el.attributes["decoding"] = "async"
  return el
end

return { { Meta = Meta }, { Para = Para }, { Image = Image } }
