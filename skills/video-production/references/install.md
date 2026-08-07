# Video production install

Read this once before the first **video-use** session. Seedance needs no install.

## video-use

### 1. Repo (already vendored)

```text
~/.agents/vendor/video-use          # git clone
~/.agents/skills/video-production/video-use/  # symlink → vendor
```

To update:

```bash
cd ~/.agents/vendor/video-use && git pull --ff-only
```

### 2. Python deps

```bash
cd ~/.agents/vendor/video-use && uv sync
```

### 3. ffmpeg (required)

```bash
command -v ffmpeg >/dev/null || brew install ffmpeg
```

Optional for URL sources: `brew install yt-dlp`

### 4. ElevenLabs API key (required for transcription)

Scribe needs `ELEVENLABS_API_KEY`. Check in order:

```bash
[ -n "$ELEVENLABS_API_KEY" ] && echo "env ok"
grep -q '^ELEVENLABS_API_KEY=..' ~/.agents/vendor/video-use/.env 2>/dev/null && echo "dotenv ok"
```

If missing, ask the user once for a key from https://elevenlabs.io/app/settings/api-keys and write:

```bash
printf 'ELEVENLABS_API_KEY=%s\n' "$KEY" > ~/.agents/vendor/video-use/.env
chmod 600 ~/.agents/vendor/video-use/.env
```

Never echo the key in tool output. Never commit `.env`.

### 5. Verify

```bash
cd ~/.agents/vendor/video-use
uv run python helpers/transcribe.py --help
ffmpeg -version | head -1
```

### 6. Lazy installs (first animation slot only)

- **HyperFrames**: `npx --yes hyperframes ...` (Node.js 22+)
- **Remotion**: `npx create-video@latest` or project-local `remotion render`
- **Manim**: read `video-use/skills/manim-video/SKILL.md`

## seedance

No dependencies. Load `seedance/SKILL.md` and generate prompts.
