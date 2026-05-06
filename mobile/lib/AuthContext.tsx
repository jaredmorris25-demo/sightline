<<<<<<< feature/us-003-auth-submit
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import * as AuthSession from 'expo-auth-session'
import { useAuthRequest } from 'expo-auth-session/providers/auth0'
import { setAuthToken } from './api'
import { AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE, AUTH0_SCOPE, redirectUri } from './auth'
=======
import React, { createContext, useContext, useState, ReactNode } from 'react'
import { auth0, AUTH0_AUDIENCE, AUTH0_SCOPE } from './auth'
import { setAuthToken } from './api'
>>>>>>> develop

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
<<<<<<< feature/us-003-auth-submit
  login: () => void
  logout: () => void
=======
  login: () => Promise<void>
  logout: () => Promise<void>
>>>>>>> develop
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  accessToken: null,
  isLoading: false,
  isAuthenticated: false,
<<<<<<< feature/us-003-auth-submit
  login: () => {},
  logout: () => {},
=======
  login: async () => {},
  logout: async () => {},
>>>>>>> develop
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

<<<<<<< feature/us-003-auth-submit
  const [request, response, promptAsync] = useAuthRequest(
    {
      clientId: AUTH0_CLIENT_ID,
      scopes: AUTH0_SCOPE.split(' '),
      redirectUri,
      extraParams: { audience: AUTH0_AUDIENCE },
    },
    { domain: AUTH0_DOMAIN }
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
=======
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
>>>>>>> develop
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
