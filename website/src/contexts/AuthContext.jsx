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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
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
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
