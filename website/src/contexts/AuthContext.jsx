import { createContext, useEffect, useState } from 'react'
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from 'firebase/auth'
import { auth } from '../services/firebase'

export const AuthContext = createContext(null)

const googleProvider = new GoogleAuthProvider()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Phân quyền lấy từ custom claim `admin` trong ID token (gán phía backend
  // bằng scripts/set_admin.py). Cùng Firebase project với app tài xế nên
  // "đã đăng nhập" chưa đủ — phải là admin mới được vào web quản trị.
  const [isAdmin, setIsAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        const { claims } = await firebaseUser.getIdTokenResult()
        setIsAdmin(claims.admin === true)
      } else {
        setIsAdmin(false)
      }
      setUser(firebaseUser)
      setLoading(false)
    })
    return unsubscribe
  }, [])

  const login = (email, password) =>
    signInWithEmailAndPassword(auth, email, password)

  const loginWithGoogle = () => signInWithPopup(auth, googleProvider)

  const logout = () => signOut(auth)

  return (
    <AuthContext.Provider
      value={{ user, isAdmin, loading, login, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}
