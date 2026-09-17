import assert from 'node:assert/strict'
import { execFile } from 'node:child_process'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { promisify } from 'node:util'
import test from 'node:test'
import { createCanvasServer } from '../src/server.js'
import { fetchTestModels } from './fixtures/codex-models.js'
import { readVideoProperties, videoPropertiesFromProbe } from '../src/video-properties.js'

const run = promisify(execFile)

test('video details use average rational FPS, skip cover art and retain container and stream tags', () => {
  const result = videoPropertiesFromProbe({
    format: { filename: '/private/host/file.mp4', format_name: 'mov,mp4,m4a,3gp,3g2,mj2', duration: '4.004', tags: { title: 'Generated scene', comment: '{"prompt":"Sunrise"}' } },
    streams: [
      { codec_type: 'video', width: 64, height: 64, disposition: { attached_pic: 1 } },
      { index: 1, codec_type: 'video', width: 1920, height: 1080, codec_name: 'h264', avg_frame_rate: '30000/1001', r_frame_rate: '60/1', tags: { encoder: 'Video encoder' }, side_data_list: [{ rotation: 90 }] },
      { index: 2, codec_type: 'audio', codec_name: 'aac', sample_rate: '48000', channels: 2, tags: { language: 'eng' } },
    ],
  }, 'video/mp4')
  assert.equal(result.fps, 30000 / 1001)
  assert.equal(result.width, 1920)
  assert.equal(result.height, 1080)
  assert.equal(result.duration, 4.004)
  assert.equal(result.format, 'MP4')
  assert.ok(result.metadata.some(row => row.name === 'Container · comment' && row.value === '{"prompt":"Sunrise"}'))
  assert.ok(result.metadata.some(row => row.name === 'video 1 · Rotation' && row.value === '90°'))
  assert.ok(result.metadata.some(row => row.name === 'audio 2 · language' && row.value === 'eng'))
  assert.equal(JSON.stringify(result).includes('/private/host'), false)
})

test('unknown rates stay unavailable and stream duration or nominal FPS can fill missing container fields', () => {
  const stream = { codec_type: 'video', width: 320, height: 240, duration: '2.5', avg_frame_rate: '0/0', r_frame_rate: '24/1' }
  const result = videoPropertiesFromProbe({ streams: [stream] }, 'video/webm')
  assert.equal(result.duration, 2.5)
  assert.equal(result.fps, 24)
  assert.equal(result.format, 'WebM')
  assert.equal(videoPropertiesFromProbe({ streams: [{ ...stream, r_frame_rate: '0/0' }] }, 'video/mp4').fps, undefined)
  assert.equal(videoPropertiesFromProbe({ streams: [stream], format: { tags: { major_brand: 'qt  ' } } }, 'video/mp4').format, 'QuickTime / MOV')
})

test('metadata failures explain missing ffprobe, hide process details and preserve cancellation', async () => {
  await assert.rejects(readVideoProperties('/asset.mp4', 'video/mp4', {
    execFileImpl: async () => { throw Object.assign(new Error('spawn error'), { code: 'ENOENT' }) },
  }), /requires ffprobe/)
  await assert.rejects(readVideoProperties('/asset.mp4', 'video/mp4', {
    execFileImpl: async () => { throw new Error('private host path') },
  }), error => !error.message.includes('private host') && error.code === 'video-director/video-properties-unavailable')
  const controller = new AbortController()
  controller.abort()
  const aborted = new Error('cancelled')
  await assert.rejects(readVideoProperties('/asset.mp4', 'video/mp4', {
    signal: controller.signal, execFileImpl: async () => { throw aborted },
  }), error => error === aborted)
})

test('stored MP4 and WebM properties are served through Canvas HTTP routes after restart and storage moves', async t => {
  try { await run('ffmpeg', ['-version']); await run('ffprobe', ['-version']) }
  catch (error) { if (error.code === 'ENOENT') return t.skip('FFmpeg is not installed'); throw error }
  const root = await mkdtemp(join(tmpdir(), 'vd-video-properties-'))
  let app
  let url
  const close = async () => { await app?.close() }
  t.after(async () => { await close(); await rm(root, { recursive: true, force: true }) })
  const start = async () => {
    app = await createCanvasServer({ dataDir: join(root, 'data'), providers: [], fetchCodexModels: fetchTestModels })
    url = await app.listen(0)
  }
  const rpc = async (endpoint, payload, channel = '/video-director') => {
    const response = await fetch(`${url}/api/rpc`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel, endpoint, payload }) })
    return response.json()
  }
  const properties = asset => fetch(new URL(`${asset.url}/properties`, url))
  await start()
  const { value: { project } } = await rpc('projects/create', { name: 'Video fixture', sessionId: 'fixture' })
  let mp4
  for (const [extension, codec, format] of [['mp4', 'mpeg4', 'MP4'], ['webm', 'libvpx', 'WebM']]) {
    const path = join(root, `sample.${extension}`)
    await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=24', '-t', '0.5', '-c:v', codec, '-metadata', 'title=Inspect fixture', path])
    const put = await rpc('assets/put', { projectId: project.id, kind: 'video', name: `sample.${extension}`, mimeType: `video/${extension}`, dataBase64: (await readFile(path)).toString('base64') })
    assert.equal(put.ok, true)
    const asset = put.value.asset
    if (extension === 'mp4') mp4 = asset
    const response = await properties(asset)
    assert.equal(response.status, 200)
    assert.equal(response.headers.get('Cache-Control'), 'no-store')
    const { value } = await response.json()
    assert.equal(value.width, 160)
    assert.equal(value.height, 90)
    assert.equal(value.duration, 0.5)
    assert.equal(value.fps, 24)
    assert.equal(value.format, format)
    assert.ok(value.metadata.some(entry => entry.value === 'Inspect fixture'))
  }
  await close()
  await start()
  assert.equal((await (await properties(mp4)).json()).value.fps, 24)
  const info = await rpc('info', {}, '/canvas-storage')
  assert.equal((await rpc('change', { expectedDataDir: info.value.dataDir, dataDir: join(root, 'moved') }, '/canvas-storage')).ok, true)
  assert.equal((await (await properties(mp4)).json()).value.fps, 24)
  assert.equal((await fetch(new URL(`${mp4.url}/properties`, url), { headers: { Origin: 'https://unrelated.example' } })).status, 403)
  assert.equal((await rpc('assets/properties', { assetId: '../../outside' })).ok, false)
  const image = await rpc('assets/put', { projectId: project.id, kind: 'image', name: 'image.png', mimeType: 'image/png', dataBase64: Buffer.from('image').toString('base64') })
  assert.equal((await rpc('assets/properties', { assetId: image.value.asset.id })).error.code, 'video-director/invalid-input')
  const imageProperties = await properties(image.value.asset)
  assert.equal(imageProperties.status, 503)
  assert.equal((await imageProperties.json()).error.code, 'video-director/invalid-input')
})
