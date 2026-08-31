<p align="center">
  <a href="README.md">🌐 English</a> ·
  <a href="../README_zh.md">🎬 示例画廊</a>
</p>

<h1 align="center">🔊 MiniMax H3 音频案例</h1>

<p align="center"><strong>通过固定 32×32 H3 代理工作流生成并验证的 13 个纯提示词音频案例。</strong></p>

以下卡片保留了实时验证时使用的完整生成提示词与原始 FLAC 输出。编号采用只追加规则：新案例使用下一个尚未占用的三位数编号，并添加在现有卡片末尾。

全部案例均使用 `minimax_h3_fl2va_int8_convrot.safetensors`、Qwen3-VL-32B H3 文本编码器、MiniMax H3 视频/音频 VAE，以及 `minimax_h3_turbo_v4_step600_ema.safetensors`。音频由 `VAEDecodeAudio` 直接交给核心 `SaveAudio` 保存，不经过视频解码或封装分支。

<table>
  <tr>
    <td>
      <h2>001 · 👩 紧急新闻播报</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2001</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult woman news anchor delivers a concise emergency bulletin in clear neutral English. Her tone is controlled, urgent, and authoritative. She says exactly: &lt;d&gt;[English] A powerful storm is moving east. Residents should seek shelter before nightfall.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Clean broadcast studio voice with very light newsroom room tone; no sound effects.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./001-woman-urgent-news.flac"></audio>
      <p><a href="./001-woman-urgent-news.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>002 · 👩 安抚式航空欢迎广播</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2002</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult woman airline cabin announcer speaks over a modern aircraft public-address system. Her delivery is warm, calm, professional, and reassuring. She says exactly: &lt;d&gt;[English] Welcome aboard flight two eighteen. Please fasten your seatbelt and stow your tray table.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Gentle aircraft cabin ventilation beneath a slightly bandwidth-limited public-address voice.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./002-woman-reassuring-airline.flac"></audio>
      <p><a href="./002-woman-reassuring-airline.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>003 · 👩 愤怒对质</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2003</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult woman confronts a colleague in a tense indoor scene. Her voice is angry, hurt, and tightly controlled rather than screaming. She says exactly: &lt;d&gt;[English] You knew the bridge was unsafe, and you sent them across anyway.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Close natural dialogue in a quiet room, one sharp breath before the line, no other sounds.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./003-woman-angry-confrontation.flac"></audio>
      <p><a href="./003-woman-angry-confrontation.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>004 · 👨 沉稳纪录片旁白</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2004</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult man delivers documentary narration in a deep, steady, grave voice with precise diction. He says exactly: &lt;d&gt;[English] For centuries, the desert winds have shaped these cliffs into silent monuments.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Clean dry narration with subtle natural breath; no room noise or effects.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./004-man-grave-documentary.flac"></audio>
      <p><a href="./004-man-grave-documentary.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>005 · 👨 突发新闻播报</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2005</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult man television news anchor delivers a breaking-news update in crisp neutral English. His tone is focused, urgent, and controlled. He says exactly: &lt;d&gt;[English] Breaking news. Emergency crews have closed the harbor after a fuel spill.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Clean broadcast studio voice with faint newsroom ambience; no sound effects.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./005-man-breaking-news.flac"></audio>
      <p><a href="./005-man-breaking-news.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>006 · 🧒 兴奋观看火箭发射</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2006</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
A naturally voiced eight-year-old child reacts with breathless wonder and delighted excitement while watching a rocket launch. The child says exactly: &lt;d&gt;[English] Look, the rocket is moving! It is really going to space!&lt;/d&gt; No adult voice and no additional words.

overall_soundscape:
Outdoor launch-viewing ambience with a distant low rocket rumble beneath the clear child voice.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./006-child-excited-rocket.flac"></audio>
      <p><a href="./006-child-excited-rocket.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>007 · 🧒 夜间惊恐低语</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2007</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
A naturally voiced ten-year-old child whispers with genuine fear in a dark bedroom at night. The child says exactly: &lt;d&gt;[English] Mom, I heard something scratching behind the bedroom wall.&lt;/d&gt; No adult reply and no additional words.

overall_soundscape:
Very quiet bedroom room tone with one faint scratch behind the wall after the sentence.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./007-child-frightened-night.flac"></audio>
      <p><a href="./007-child-frightened-night.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>008 · 👵 老年女声：回望晨光</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2008</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An elderly woman in her late seventies speaks in a gentle, slightly weathered voice. Her delivery is intimate, reflective, and quietly grateful. She says exactly: &lt;d&gt;[English] At my age, every sunrise feels less ordinary and more like a gift.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Close natural voice in a still room, soft breath and subtle chair creak.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./008-older-woman-reflective.flac"></audio>
      <p><a href="./008-older-woman-reflective.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>009 · 👴 老年男声：诙谐往事</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2009</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An elderly man in his eighties speaks in a warm, weathered baritone with a dry sense of humor. He sounds amused and nostalgic. He says exactly: &lt;d&gt;[English] The map was wrong, of course, but getting lost made the best story.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Intimate fireside voice with a soft fireplace crackle and one quiet chuckle at the end.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./009-older-man-wry-story.flac"></audio>
      <p><a href="./009-older-man-wry-story.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>010 · 🤖 空间站机器人广播</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2010</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
A clearly synthetic service robot makes a precise space-station announcement. The voice is metallic, gender-neutral, calm, and machine-timed rather than human. It says exactly: &lt;d&gt;[English] Attention passengers. Docking sequence complete. Atmospheric pressure is within safe limits.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Clean futuristic intercom with a short electronic chime before the announcement and faint machinery hum.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./010-robot-station-announcement.flac"></audio>
      <p><a href="./010-robot-station-announcement.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>011 · 🐕🐈 家中猫狗</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2011</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
A natural domestic-animal sound scene with no human speech. At the start, a medium-sized dog gives exactly two alert barks. After a short pause, a house cat answers with one clear meow. The dog gives a soft questioning whine, then the cat purrs close to the microphone. End with one small collar jingle.

overall_soundscape:
Quiet living room room tone; realistic dog and cat vocalizations at close range, no human sounds.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./011-animals-dog-cat-home.flac"></audio>
      <p><a href="./011-animals-dog-cat-home.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>012 · 🐓🐄🐐 清晨农场</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2012</p>
      <p><strong>结果：</strong>5.175 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
A realistic farmyard sound sequence at dawn with no human speech. A rooster crows once from nearby. A cow answers with one deep moo from farther away. A goat gives two short bleats. Small birds continue chirping naturally in the background.

overall_soundscape:
Open rural morning ambience with light wind, distant barn reflections, and clearly separated animal calls.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./012-animals-farm-morning.flac"></audio>
      <p><a href="./012-animals-farm-morning.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td>
      <h2>013 · 👨 15 秒机长广播</h2>
      <p><strong>参数：</strong>Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 362 · 6 步 · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM 关闭 · denoise 1.0 · seed 2013</p>
      <p><strong>结果：</strong>15.075 秒 · 32 kHz 双声道 · FLAC</p>
      <p><strong>提示词</strong></p>
      <pre><code>integrated_multimodal_description:
An adult man airline captain speaks over a modern aircraft public-address system in calm, confident, reassuring English. He says exactly: &lt;d&gt;[English] Good afternoon, this is your captain speaking. We are beginning our descent into Singapore. The weather is clear, and we expect to be at the gate in twenty minutes. Cabin crew, please prepare for landing.&lt;/d&gt; No additional words or speakers.

overall_soundscape:
Steady aircraft cabin ventilation under a slightly bandwidth-limited cockpit public-address voice.

non_diegetic_music:
None.</code></pre>
      <audio controls preload="none" src="./013-man-airline-15s.flac"></audio>
      <p><a href="./013-man-airline-15s.flac">🔊 播放或下载 FLAC</a></p>
    </td>
  </tr>
</table>
