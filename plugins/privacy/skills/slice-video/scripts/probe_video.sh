#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C

usage() {
  cat <<'USAGE'
Usage:
  probe_video.sh --input FILE

Prints only selected technical container and stream fields. It never emits
frames, packets, tags, chapters, attachments, subtitles, or decoded media.
USAGE
}

fail() {
  printf 'error=%s\n' "$1" >&2
  exit 1
}

input_path=""
while (($#)); do
  case "$1" in
    --input)
      (($# >= 2)) || fail "--input requires a value"
      input_path=$2
      shift 2
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
[[ "$input_path" != "-" && "$input_path" != *"://"* ]] || fail "input must be a local file"
[[ -f "$input_path" ]] || fail "input must be a local regular file"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is not installed"

input_dir=$(cd -- "$(dirname -- "$input_path")" && pwd -P) || fail "cannot resolve input directory"
input_abs="${input_dir}/$(basename -- "$input_path")"

if ! probe_output=$(ffprobe -v error \
  -protocol_whitelist file \
  -show_entries 'format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,bit_rate,sample_rate,channels' \
  -of json \
  "$input_abs" 2>/dev/null); then
  fail "ffprobe failed; diagnostics were suppressed for privacy"
fi

printf '%s\n' "$probe_output"
