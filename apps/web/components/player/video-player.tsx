"use client";

import {
  AlertCircle,
  Loader2,
  Maximize,
  Pause,
  Play,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from "lucide-react";
import * as React from "react";

import { api } from "@/lib/api-client";
import type { PlaybackInfo } from "@/lib/types";
import { cn, formatTimecode } from "@/lib/utils";

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];
/** Watch-progress backend'ga har 12 sekundda saqlanadi (FRONTEND_UX_UI 5.3) */
const SAVE_INTERVAL_MS = 12_000;

export interface VideoPlayerProps {
  lessonId: string;
  poster?: string | null;
  startAt?: number;
  onProgress?: (payload: { watchSeconds: number; positionSeconds: number }) => void;
  onEnded?: () => void;
  className?: string;
}

export function VideoPlayer({
  lessonId,
  poster,
  startAt = 0,
  onProgress,
  onEnded,
  className,
}: VideoPlayerProps) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const hlsRef = React.useRef<{ destroy: () => void } | null>(null);
  const watchedRef = React.useRef(0);
  const lastTickRef = React.useRef(0);

  const [playback, setPlayback] = React.useState<PlaybackInfo | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [playing, setPlaying] = React.useState(false);
  const [muted, setMuted] = React.useState(false);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const [speed, setSpeed] = React.useState(1);

  // ---- Playback URL olish (vaqtinchalik signed URL) ----
  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPlayback(null);

    (async () => {
      try {
        const info = await api.get<PlaybackInfo>(`/lessons/${lessonId}/playback`);
        if (!cancelled) setPlayback(info);
      } catch (caught) {
        if (!cancelled) {
          setError(
            caught instanceof Error ? caught.message : "Videoni yuklab bo'lmadi",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [lessonId]);

  // ---- HLS yoki oddiy mp4 ni ulash ----
  React.useEffect(() => {
    const video = videoRef.current;
    if (!video || !playback) return;

    hlsRef.current?.destroy();
    hlsRef.current = null;
    watchedRef.current = 0;

    const isHls =
      playback.content_type.includes("mpegURL") || playback.url.includes(".m3u8");

    if (isHls && !video.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari'dan boshqa brauzerlar uchun hls.js
      let destroyed = false;
      import("hls.js")
        .then(({ default: Hls }) => {
          if (destroyed || !Hls.isSupported()) {
            video.src = playback.url;
            return;
          }
          const hls = new Hls({ maxBufferLength: 30, enableWorker: true });
          hls.loadSource(playback.url);
          hls.attachMedia(video);
          hls.on(Hls.Events.ERROR, (_event, data) => {
            if (data.fatal) setError("Video oqimida xatolik yuz berdi");
          });
          hlsRef.current = hls;
        })
        .catch(() => {
          video.src = playback.url;
        });

      return () => {
        destroyed = true;
        hlsRef.current?.destroy();
        hlsRef.current = null;
      };
    }

    video.src = playback.url;
    return () => {
      hlsRef.current?.destroy();
      hlsRef.current = null;
    };
  }, [playback]);

  // ---- Progressni davriy saqlash ----
  React.useEffect(() => {
    if (!onProgress) return;
    const timer = setInterval(() => {
      const video = videoRef.current;
      if (!video || video.paused) return;
      onProgress({
        watchSeconds: Math.floor(watchedRef.current),
        positionSeconds: Math.floor(video.currentTime),
      });
    }, SAVE_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [onProgress]);

  // Sahifa yopilishi/pauza paytida oxirgi holatni saqlaymiz
  React.useEffect(() => {
    const flush = () => {
      const video = videoRef.current;
      if (!video || !onProgress) return;
      onProgress({
        watchSeconds: Math.floor(watchedRef.current),
        positionSeconds: Math.floor(video.currentTime),
      });
    };
    window.addEventListener("beforeunload", flush);
    return () => {
      window.removeEventListener("beforeunload", flush);
      flush();
    };
  }, [onProgress]);

  // ---- Klaviatura boshqaruvi (FRONTEND_UX_UI 9) ----
  React.useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const video = videoRef.current;
      if (!video) return;
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;

      switch (event.key) {
        case " ":
        case "k":
          event.preventDefault();
          void togglePlay();
          break;
        case "ArrowRight":
          event.preventDefault();
          video.currentTime = Math.min(video.currentTime + 10, video.duration || Infinity);
          break;
        case "ArrowLeft":
          event.preventDefault();
          video.currentTime = Math.max(video.currentTime - 10, 0);
          break;
        case "m":
          video.muted = !video.muted;
          setMuted(video.muted);
          break;
        case "f":
          void toggleFullscreen();
          break;
        default:
          break;
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const togglePlay = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) await video.play().catch(() => undefined);
    else video.pause();
  };

  const toggleFullscreen = async () => {
    const container = containerRef.current;
    if (!container) return;
    if (document.fullscreenElement) await document.exitFullscreen().catch(() => undefined);
    else await container.requestFullscreen().catch(() => undefined);
  };

  const seek = (event: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = Number(event.target.value);
    setCurrentTime(video.currentTime);
  };

  if (error) {
    return (
      <div className={cn("player-frame flex flex-col items-center justify-center gap-3 p-6", className)}>
        <AlertCircle className="size-8 text-destructive" />
        <p className="text-center text-sm text-white/80">{error}</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={cn("player-frame group", className)}>
      {loading ? (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black">
          <Loader2 className="size-8 animate-spin text-white/70" />
        </div>
      ) : null}

      <video
        ref={videoRef}
        poster={poster ?? undefined}
        playsInline
        preload="metadata"
        className="size-full"
        onLoadedMetadata={(event) => {
          const video = event.currentTarget;
          setDuration(video.duration || 0);
          if (startAt > 0 && startAt < (video.duration || Infinity)) {
            video.currentTime = startAt;
          }
        }}
        onPlay={() => setPlaying(true)}
        onPause={() => {
          setPlaying(false);
          onProgress?.({
            watchSeconds: Math.floor(watchedRef.current),
            positionSeconds: Math.floor(videoRef.current?.currentTime ?? 0),
          });
        }}
        onTimeUpdate={(event) => {
          const video = event.currentTarget;
          setCurrentTime(video.currentTime);
          // Faqat haqiqatda ko'rilgan vaqtni hisoblaymiz (seek qilish hisoblanmaydi)
          const delta = video.currentTime - lastTickRef.current;
          if (delta > 0 && delta < 1.5) watchedRef.current += delta;
          lastTickRef.current = video.currentTime;
        }}
        onEnded={() => {
          setPlaying(false);
          onEnded?.();
        }}
        onError={() => setError("Video faylini o'qib bo'lmadi")}
      />

      {/* Boshqaruv paneli */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent p-3 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100 data-[playing=false]:opacity-100"
        data-playing={playing}
      >
        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.5}
          value={currentTime}
          onChange={seek}
          aria-label="Video vaqti"
          className="h-1.5 w-full cursor-pointer accent-primary"
        />

        <div className="mt-2 flex items-center gap-2 text-white">
          <button
            type="button"
            onClick={togglePlay}
            className="rounded p-1.5 hover:bg-white/15"
            aria-label={playing ? "Pauza" : "Ijro"}
          >
            {playing ? <Pause className="size-5" /> : <Play className="size-5" />}
          </button>

          <button
            type="button"
            onClick={() => {
              const video = videoRef.current;
              if (video) video.currentTime = Math.max(video.currentTime - 10, 0);
            }}
            className="rounded p-1.5 hover:bg-white/15"
            aria-label="10 soniya orqaga"
          >
            <SkipBack className="size-4" />
          </button>

          <button
            type="button"
            onClick={() => {
              const video = videoRef.current;
              if (video) video.currentTime += 10;
            }}
            className="rounded p-1.5 hover:bg-white/15"
            aria-label="10 soniya oldinga"
          >
            <SkipForward className="size-4" />
          </button>

          <button
            type="button"
            onClick={() => {
              const video = videoRef.current;
              if (!video) return;
              video.muted = !video.muted;
              setMuted(video.muted);
            }}
            className="rounded p-1.5 hover:bg-white/15"
            aria-label={muted ? "Ovozni yoqish" : "Ovozni o'chirish"}
          >
            {muted ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}
          </button>

          <span className="ml-1 text-xs tabular-nums text-white/85">
            {formatTimecode(currentTime)} / {formatTimecode(duration)}
          </span>

          <div className="ml-auto flex items-center gap-1.5">
            <select
              value={speed}
              onChange={(event) => {
                const value = Number(event.target.value);
                setSpeed(value);
                if (videoRef.current) videoRef.current.playbackRate = value;
              }}
              aria-label="Ijro tezligi"
              className="rounded bg-white/15 px-1.5 py-1 text-xs text-white outline-none"
            >
              {SPEEDS.map((option) => (
                <option key={option} value={option} className="text-black">
                  {option}×
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={toggleFullscreen}
              className="rounded p-1.5 hover:bg-white/15"
              aria-label="To'liq ekran"
            >
              <Maximize className="size-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
