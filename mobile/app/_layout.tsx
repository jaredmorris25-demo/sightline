import { Stack } from 'expo-router'
import { AuthProvider } from '../lib/AuthContext'

export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="login" options={{ title: 'Sign In' }} />
      </Stack>
    </AuthProvider>
  )
}
