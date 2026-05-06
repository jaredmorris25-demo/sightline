<<<<<<< feature/us-003-auth-submit
import * as AuthSession from 'expo-auth-session'
import * as WebBrowser from 'expo-web-browser'

WebBrowser.maybeCompleteAuthSession()

export const AUTH0_DOMAIN = 'dev-kr7ljpg5onbkey04.us.auth0.com'
export const AUTH0_CLIENT_ID = 'aSkACgfJTufyEd8pWaWjdth8AUXYtMv7'
export const AUTH0_AUDIENCE = 'https://api.sightline.app'
export const AUTH0_SCOPE = 'openid profile email read:sightings write:sightings'

export const redirectUri = AuthSession.makeRedirectUri({
  scheme: 'sightline',
  path: 'callback',
})
=======
import Auth0 from 'react-native-auth0'

export const auth0 = new Auth0({
  domain: process.env.EXPO_PUBLIC_AUTH0_DOMAIN ?? 'dev-kr7ljpg5onbkey04.us.auth0.com',
  clientId: process.env.EXPO_PUBLIC_AUTH0_CLIENT_ID ?? 'aSkACgfJTufyEd8pWaWjdth8AUXYtMv7',
})

export const AUTH0_AUDIENCE = 'https://api.sightline.app'
export const AUTH0_SCOPE = 'openid profile email read:sightings write:sightings'
>>>>>>> develop
