#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C

usage() {
  cat <<'USAGE'
Usage:
  slice_video.sh --input FILE --output-dir DIR --segment-seconds N [options]

Options:
  --prefix NAME          Output basename prefix (default: part)
  --extension EXT        Output extension (default: mp4)
  --mode precise|copy    Precise re-encode or keyframe-aligned copy (default: precise)
  --crf 0..51            H.264 CRF in precise mode (default: 20)
  --preset PRESET        H.264 preset in precise mode (default: medium)
  --audio-bitrate RATE   AAC bitrate in precise mode (default: 128k)
  --no-audio             Omit audio from the segments
  -h, --help             Show this help

The command accepts a local regular file only. It refuses to reuse a prefix
that already has matching output files and emits technical status only.
USAGE
}

fail() {
  printf 'error=%s\n' "$1" >&2
  exit 1
}

input_path=""
output_dir_path=""
segment_seconds=""
prefix="part"
extension="mp4"
mode="precise"
crf="20"
preset="medium"
audio_bitrate="128k"
no_audio=0

while (($#)); do
  case "$1" in
    --input)
      (($# >= 2)) || fail "--input requires a value"
      input_path=$2
      shift 2
      ;;
    --output-dir)
      (($# >= 2)) || fail "--output-dir requires a value"
      output_dir_path=$2
      shift 2
      ;;
    --segment-seconds)
      (($# >= 2)) || fail "--segment-seconds requires a value"
      segment_seconds=$2
      shift 2
      ;;
    --prefix)
      (($# >= 2)) || fail "--prefix requires a value"
      prefix=$2
      shift 2
      ;;
    --extension)
      (($# >= 2)) || fail "--extension requires a value"
      extension=$2
      shift 2
      ;;
    --mode)
      (($# >= 2)) || fail "--mode requires a value"
      mode=$2
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
    --no-audio)
      no_audio=1
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
[[ -n "$output_dir_path" ]] || fail "--output-dir is required"
[[ -n "$segment_seconds" ]] || fail "--segment-seconds is required"
[[ "$input_path" != "-" && "$input_path" != *"://"* ]] || fail "input must be a local file"
[[ -f "$input_path" ]] || fail "input must be a local regular file"
[[ "$output_dir_path" != *"://"* ]] || fail "output directory must be local"
[[ "$segment_seconds" =~ ^[0-9]+([.][0-9]+)?$ ]] || fail "segment seconds must be a positive number"
awk -v value="$segment_seconds" 'BEGIN { exit !(value > 0) }' || fail "segment seconds must be greater than zero"
[[ "$prefix" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "prefix contains unsupported characters"
[[ "$extension" =~ ^[A-Za-z0-9]+$ ]] || fail "extension contains unsupported characters"
case "$mode" in
  precise|copy) ;;
  *) fail "mode must be precise or copy" ;;
esac
[[ "$crf" =~ ^[0-9]+$ ]] && ((crf <= 51)) || fail "CRF must be an integer from 0 to 51"
case "$preset" in
  ultrafast|superfast|veryfast|faster|fast|medium|slow|slower|veryslow|placebo) ;;
  *) fail "unsupported preset" ;;
esac
[[ "$audio_bitrate" =~ ^[1-9][0-9]*[kKmM]?$ ]] || fail "invalid audio bitrate"

command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg is not installed"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is not installed"

input_dir=$(cd -- "$(dirname -- "$input_path")" && pwd -P) || fail "cannot resolve input directory"
input_abs="${input_dir}/$(basename -- "$input_path")"
mkdir -p -- "$output_dir_path"
output_dir=$(cd -- "$output_dir_path" && pwd -P) || fail "cannot resolve output directory"

if [[ "$mode" == "precise" ]]; then
  case "$extension" in
    mp4|m4v|mov|mkv) ;;
    *) fail "precise mode supports mp4, m4v, mov, or mkv output" ;;
  esac
fi

shopt -s nullglob
existing_segments=("${output_dir}/${prefix}_"*".${extension}")
if ((${#existing_segments[@]})); then
  fail "matching output files already exist; use a fresh directory or prefix"
fi

if ! source_duration=$(
  ffprobe -v error -protocol_whitelist file \
    -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$input_abs" 2>/dev/null
); then
  fail "ffprobe failed; diagnostics were suppressed for privacy"
fi
if ! source_fps=$(
  ffprobe -v error -protocol_whitelist file \
    -select_streams V:0 \
    -show_entries stream=avg_frame_rate \
    -of default=noprint_wrappers=1:nokey=1 \
    "$input_abs" 2>/dev/null
); then
  fail "ffprobe failed; diagnostics were suppressed for privacy"
fi
[[ -n "$source_fps" ]] || fail "input has no primary video stream"

segment_time_delta=$(
  awk -v rate="$source_fps" 'BEGIN {
    split(rate, parts, "/")
    if (parts[1] > 0 && parts[2] > 0) {
      printf "%.9f", parts[2] / (2 * parts[1])
    } else {
      printf "0.050000000"
    }
  }'
)

output_pattern="${output_dir}/${prefix}_%04d.${extension}"
ffmpeg_args=(
  -nostdin
  -hide_banner
  -loglevel error
  -n
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
)

if [[ "$mode" == "copy" ]]; then
  ffmpeg_args+=(-c copy)
  boundary_accuracy="keyframe-aligned"
else
  ffmpeg_args+=(
    -c:v libx264
    -crf "$crf"
    -preset "$preset"
    -pix_fmt yuv420p
    -force_key_frames "expr:gte(t,n_forced*${segment_seconds})"
  )
  if ((no_audio)); then
    ffmpeg_args+=(-an)
  else
    ffmpeg_args+=(-c:a aac -b:a "$audio_bitrate")
  fi
  boundary_accuracy="frame-aligned"
fi

ffmpeg_args+=(
  -f segment
  -segment_time "$segment_seconds"
)
if [[ "$mode" == "precise" ]]; then
  ffmpeg_args+=(-segment_time_delta "$segment_time_delta")
fi
ffmpeg_args+=(
  -reset_timestamps 1
  -avoid_negative_ts make_zero
)

if ! ffmpeg "${ffmpeg_args[@]}" "$output_pattern" 2>/dev/null; then
  fail "ffmpeg processing failed; diagnostics were suppressed for privacy"
fi

segments=("${output_dir}/${prefix}_"*".${extension}")
((${#segments[@]} > 0)) || fail "ffmpeg completed without producing segments"

printf 'status=ok\n'
printf 'source_duration_seconds=%s\n' "$source_duration"
printf 'source_avg_frame_rate=%s\n' "$source_fps"
printf 'requested_segment_seconds=%s\n' "$segment_seconds"
printf 'mode=%s\n' "$mode"
printf 'boundary_accuracy=%s\n' "$boundary_accuracy"
printf 'segment_count=%s\n' "${#segments[@]}"
