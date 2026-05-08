import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import * as AuthSession from 'expo-auth-session'
import * as WebBrowser from 'expo-web-browser'
import { setAuthToken } from './api'
import { AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE, AUTH0_SCOPE, redirectUri } from './auth'

WebBrowser.maybeCompleteAuthSession()

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
  login: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  accessToken: null,
  isLoading: false,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const discovery = AuthSession.useAutoDiscovery(`https://${AUTH0_DOMAIN}`)

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: AUTH0_CLIENT_ID,
      scopes: AUTH0_SCOPE.split(' '),
      redirectUri,
      extraParams: { audience: AUTH0_AUDIENCE },
    },
    discovery
  )

  useEffect(() => {
    if (response?.type !== 'success') return

    setIsLoading(true)
    AuthSession.exchangeCodeAsync(
      {
        clientId: AUTH0_CLIENT_ID,
        code: response.params.code,
        redirectUri,
        extraParams: { code_verifier: request?.codeVerifier ?? '' },
      },
      { tokenEndpoint: `https://${AUTH0_DOMAIN}/oauth/token` }
    )
      .then(async tokens => {
        setAccessToken(tokens.accessToken)
        setAuthToken(tokens.accessToken)
        const userInfoRes = await fetch(`https://${AUTH0_DOMAIN}/userinfo`, {
          headers: { Authorization: `Bearer ${tokens.accessToken}` },
        })
        const profile = await userInfoRes.json()
        setUser({ sub: profile.sub, email: profile.email, name: profile.name })
      })
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [response])

  const login = () => { promptAsync() }

  const logout = () => {
    setUser(null)
    setAccessToken(null)
    setAuthToken(null)
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
