// Chuông báo động tổng hợp bằng Web Audio API — không cần file mp3, chạy offline.
// Trình duyệt chặn phát âm thanh trước khi người dùng tương tác, nên gọi
// unlockAudio() 1 lần trong lần click/nhấn phím đầu tiên.

let ctx = null

function audioContext() {
  if (ctx == null) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
  }
  return ctx
}

/** Gọi trong cử chỉ người dùng đầu tiên để "mở khoá" âm thanh. */
export function unlockAudio() {
  const ac = audioContext()
  if (ac && ac.state === 'suspended') ac.resume().catch(() => {})
}

/** Ba tiếng bíp báo động (~880Hz). severity 'critical' -> gắt hơn. */
export function playAlarm(severity = 'medium') {
  const ac = audioContext()
  if (!ac) return
  if (ac.state === 'suspended') ac.resume().catch(() => {})

  const beeps = severity === 'critical' ? 4 : 3
  const freq = severity === 'critical' ? 1040 : 880
  const gap = 0.28

  for (let i = 0; i < beeps; i += 1) {
    const t0 = ac.currentTime + i * gap
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.type = 'square'
    osc.frequency.value = freq
    gain.gain.setValueAtTime(0.0001, t0)
    gain.gain.exponentialRampToValueAtTime(0.25, t0 + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + gap * 0.8)
    osc.connect(gain).connect(ac.destination)
    osc.start(t0)
    osc.stop(t0 + gap)
  }
}
