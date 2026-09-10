import { useEffect, useState } from 'react'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../services/firebase'

/** Nghe realtime collection `music_tracks`. Mọi thay đổi (bài mới do tài xế tìm,
 * admin bật/tắt, lượt phát, báo cáo) đẩy về ngay. */
export function useMusicRealtime() {
  const [tracks, setTracks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const unsubscribe = onSnapshot(
      collection(db, 'music_tracks'),
      (snapshot) => {
        setTracks(snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })))
        setError(null)
        setLoading(false)
      },
      (err) => {
        setError(err)
        setLoading(false)
      },
    )
    return unsubscribe
  }, [])

  return { tracks, loading, error }
}
