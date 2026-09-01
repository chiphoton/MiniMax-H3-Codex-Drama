#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C

usage() {
  cat <<'USAGE'
Usage:
  compress_video.sh --input FILE --output FILE [options]

Options:
  --codec h264|h265       Video codec (default: h264)
  --crf 0..51             Constant-rate factor (default: 23)
  --preset PRESET         FFmpeg encoder preset (default: medium)
  --audio-bitrate RATE    AAC bitrate, such as 128k (default: 128k)
  --max-width PIXELS      Downscale to at most this width; never upscale
  --no-audio              Omit audio from the output
  --overwrite             Replace an existing output file
  -h, --help              Show this help

The command accepts local regular files only and emits technical status only.
USAGE
}

fail() {
  printf 'error=%s\n' "$1" >&2
  exit 1
}

input_path=""
output_path=""
codec="h264"
crf="23"
preset="medium"
audio_bitrate="128k"
max_width=""
no_audio=0
overwrite=0

while (($#)); do
  case "$1" in
    --input)
      (($# >= 2)) || fail "--input requires a value"
      input_path=$2
      shift 2
      ;;
    --output)
      (($# >= 2)) || fail "--output requires a value"
      output_path=$2
      shift 2
      ;;
    --codec)
      (($# >= 2)) || fail "--codec requires a value"
      codec=$2
      shift 2
      ;;
    --crf)
      (($# >= 2)) || fail "--crf requires a value"
      crf=$2
      shift 2
      ;;
    --preset)
      (($# >= 2)) || fail "--preset requires a value"
      preset=$2
      shift 2
      ;;
    --audio-bitrate)
      (($# >= 2)) || fail "--audio-bitrate requires a value"
      audio_bitrate=$2
      shift 2
      ;;
    --max-width)
      (($# >= 2)) || fail "--max-width requires a value"
      max_width=$2
      shift 2
      ;;
    --no-audio)
      no_audio=1
      shift
      ;;
    --overwrite)
      overwrite=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option"
      ;;
  esac
done

[[ -n "$input_path" ]] || fail "--input is required"
[[ -n "$output_path" ]] || fail "--output is required"
[[ "$input_path" != "-" && "$input_path" != *"://"* ]] || fail "input must be a local file"
[[ "$output_path" != "-" && "$output_path" != *"://"* ]] || fail "output must be a local file"
[[ -f "$input_path" ]] || fail "input must be a local regular file"
command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg is not installed"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is not installed"

[[ "$crf" =~ ^[0-9]+$ ]] && ((crf <= 51)) || fail "CRF must be an integer from 0 to 51"
case "$preset" in
  ultrafast|superfast|veryfast|faster|fast|medium|slow|slower|veryslow|placebo) ;;
  *) fail "unsupported preset" ;;
esac
[[ "$audio_bitrate" =~ ^[1-9][0-9]*[kKmM]?$ ]] || fail "invalid audio bitrate"
if [[ -n "$max_width" ]]; then
  [[ "$max_width" =~ ^[0-9]+$ ]] && ((max_width >= 2)) || fail "max width must be an integer of at least 2"
fi

case "$codec" in
  h264) video_encoder="libx264" ;;
  h265) video_encoder="libx265" ;;
  *) fail "codec must be h264 or h265" ;;
esac

input_dir=$(cd -- "$(dirname -- "$input_path")" && pwd -P) || fail "cannot resolve input directory"
input_abs="${input_dir}/$(basename -- "$input_path")"
output_parent=$(dirname -- "$output_path")
[[ -d "$output_parent" ]] || fail "output directory does not exist"
output_dir=$(cd -- "$output_parent" && pwd -P) || fail "cannot resolve output directory"
output_abs="${output_dir}/$(basename -- "$output_path")"

[[ "$input_abs" != "$output_abs" ]] || fail "input and output must be different files"
if [[ -e "$output_abs" && $overwrite -eq 0 ]]; then
  fail "output exists; use --overwrite only with user authorization"
fi

ffmpeg_args=(-nostdin -hide_banner -loglevel error)
if ((overwrite)); then
  ffmpeg_args+=(-y)
else
  ffmpeg_args+=(-n)
fi
ffmpeg_args+=(
  -protocol_whitelist file
  -i "$input_abs"
  -map 0:V:0
)
if ((no_audio == 0)); then
  ffmpeg_args+=(-map "0:a:0?")
fi
ffmpeg_args+=(
  -map_metadata -1
  -map_chapters -1
  -sn
  -dn
  -c:v "$video_encoder"
  -crf "$crf"
  -preset "$preset"
  -pix_fmt yuv420p
)
if [[ -n "$max_width" ]]; then
  ffmpeg_args+=(-vf "scale=w='trunc(min(iw,${max_width})/2)*2':h=-2")
fi
if ((no_audio)); then
  ffmpeg_args+=(-an)
else
  ffmpeg_args+=(-c:a aac -b:a "$audio_bitrate")
fi

output_extension=${output_abs##*.}
output_extension=$(printf '%s' "$output_extension" | tr '[:upper:]' '[:lower:]')
case "$output_extension" in
  mp4|m4v|mov) ffmpeg_args+=(-movflags +faststart) ;;
esac

if ! ffmpeg "${ffmpeg_args[@]}" "$output_abs" 2>/dev/null; then
  fail "ffmpeg processing failed; diagnostics were suppressed for privacy"
fi

input_bytes=$(wc -c < "$input_abs" | tr -d '[:space:]')
output_bytes=$(wc -c < "$output_abs" | tr -d '[:space:]')
output_duration=$(
  ffprobe -v error -protocol_whitelist file \
    -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$output_abs" 2>/dev/null || true
)
[[ -n "$output_duration" ]] || output_duration="unknown"

printf 'status=ok\n'
printf 'input_bytes=%s\n' "$input_bytes"
printf 'output_bytes=%s\n' "$output_bytes"
printf 'output_duration_seconds=%s\n' "$output_duration"
