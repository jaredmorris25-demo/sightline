import React, { createContext, useContext, useState, ReactNode } from 'react'
import { auth0, AUTH0_AUDIENCE, AUTH0_SCOPE } from './auth'
import { setAuthToken } from './api'

interface User {
  sub?: string
  email?: string
  name?: string
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  accessToken: null,
  isLoading: false,
  isAuthenticated: false,
  login: async () => {},
  logout: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const login = async () => {
    setIsLoading(true)
    try {
      const credentials = await auth0.webAuth.authorize({
        audience: AUTH0_AUDIENCE,
        scope: AUTH0_SCOPE,
      })
      setAccessToken(credentials.accessToken)
      setAuthToken(credentials.accessToken)
      const profile = await auth0.auth.userInfo({ token: credentials.accessToken })
      setUser({ sub: profile.sub, email: profile.email, name: profile.name })
    } catch {
      // user cancelled or network error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await auth0.webAuth.clearSession()
    } catch {
      // ignore
    } finally {
      setUser(null)
      setAccessToken(null)
      setAuthToken(null)
      setIsLoading(false)
    }
  }

  return (
    <AuthContext.Provider value={{ user, accessToken, isLoading, isAuthenticated: !!accessToken, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
